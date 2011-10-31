#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides unit tests for deferred methods."""
# Copyright (C) 2008-2010 Sebastian Heinlein <glatzor@ubuntu.com>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# Licensed under the GNU General Public License Version 2

__author__  = "Sebastian Heinlein <devel@glatzor.de>"

import os
import sys
import unittest

import mox

sys.path.insert(0, os.path.abspath(".."))
from defer import inline_callbacks, Deferred, utils

class DeferredTestCase(mox.MoxTestBase):
    """Test suite for defer"""

    def test_single_callback(self):
        """Test simple callback."""
        deferred = Deferred()
        deferred.callback("start")
        self.assertEquals(deferred.result, "start")

    def test_additional_callback(self):
        """Test additional callback."""
        cbs = self.mox.CreateMockAnything()
        cbs.callback("start").AndReturn("end")
        self.mox.ReplayAll()
        deferred = Deferred()
        deferred.add_callback(cbs.callback)
        deferred.callback("start")
        self.assertEquals(deferred.result, "end")

    def test_chained_callbacks(self):
        """Test chained callbacks."""
        error = Exception(":'(")
        cbs = self.mox.CreateMockAnything()
        cbs.callback("start").AndReturn("step1")
        cbs.callback("step1").AndReturn("end")
        self.mox.ReplayAll()
        deferred = Deferred()
        deferred.add_callback(cbs.callback)
        deferred.add_callback(cbs.callback)
        deferred.callback("start")
        self.assertEquals(deferred.result, "end")

    def test_nested_callbacks(self):
        """Test nested Deferred."""
        cbs = self.mox.CreateMockAnything()
        cbs.callback("start", 1).AndReturn("step1")
        cbs.callback("step1", 2).AndReturn("step2")
        cbs.callback("step2", 3).AndReturn("step3")
        cbs.callback("step3", 4).AndReturn("step4")
        cbs.callback("step4", 5).AndReturn("step5")
        cbs.callback("step5", 6).AndReturn("end")
        self.mox.ReplayAll()
        def get_nested_deferred(previous):
            deferred2 = Deferred()
            deferred2.callback(previous)
            deferred2.add_callback(cbs.callback, 2)
            deferred2.add_callback(get_nested_deferred2)
            return deferred2
        def get_nested_deferred2(previous):
            deferred3 = Deferred()
            deferred3.callback(previous)
            deferred3.add_callback(cbs.callback, 3)
            deferred3.add_callback(get_nested_deferred3)
            return deferred3
        def get_nested_deferred3(previous):
            deferred4 = Deferred()
            deferred4.add_callback(cbs.callback, 4)
            deferred4.add_callback(cbs.callback, 5)
            deferred4.callback(previous)
            return deferred4
        deferred = Deferred()
        deferred.add_callback(cbs.callback, 1)
        deferred.add_callback(get_nested_deferred)
        deferred.add_callback(cbs.callback, 6)
        deferred.callback("start")
        self.assertEquals(deferred.result, "end")

    @inline_callbacks
    def test_inline_callbacks(self):
        """ test inline callbacks """
        res = yield self._inline_callback()
        self.assertEquals(res, "lala")

    def test_deferable(self):
        """Test a deferable decorated method."""
        res = self._deferable("huhu", defer=True)
        assert(isinstance(res, Deferred))
        self.assertEqual(res.result, "async")
        res = self._deferable("huhu")
        self.assertEqual(res, "sync")

    @utils.deferable
    def _deferable(self, arg, reply_handler=None, error_handler=None):
        """Helper method which allows to be called async by specifing
        a reply_handler.
        """
        self.assertEqual(arg, "huhu", "Wrong argument")
        if reply_handler:
            reply_handler("async")
        else:
            return "sync"

    @inline_callbacks
    def test_auto_deferable_inline(self):
        """Test if a deferable method is automatically deferred if called
        from an inline_callbacks decorated method."""
        res = yield self._deferable("huhu")
        self.assertEqual(res, "async")

    @inline_callbacks
    def test_auto_deferable_overwrite(self):
        """Test if the defer argument overwrites the automatic deferration."""
        res = yield self._deferable("huhu", defer=False)
        self.assertEqual(res, "sync")

    @inline_callbacks
    def test_inline_exception(self):
        """ test inline exceptions """
        try:
            res = yield self._inline_callback_exception()
            print res
        except ValueError, e:
            # this is what we want
            pass
        else:
            self.fail("expected ValueError, got nothing")

    def _inline_callback(self):
        deferred = Deferred()
        deferred.add_callback(lambda: "lala")
        return deferred

    def _inline_callback_exception(self):
        raise ValueError("test exception")

if __name__ == "__main__":
    unittest.main()

# vim: ts=4 et sts=4
