<<<<<<< HEAD
<<<<<<< HEAD
# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
.. moduleauthor:: Marmaduke Woodman <mw@eml.cc>

=======

"""
>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
=======

"""
>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
This module provides an interface to part of the MATLAB Engine API. 

Startup is a little slow as with the existing MATLAB adapter, but the subsequent calls
complete very quickly, making this suitable for interactive use.

Note: this code isn't yet adapted for use in TVB, and requires cross-platform adaptation
as well.

"""

# import the FFI
from ctypes import *

<<<<<<< HEAD
<<<<<<< HEAD
try:
    # open the engine library
    lib = CDLL('libeng.so')
except OSError:
    ## TODO What to do in this case? Should work cross-platform.
    pass


class MATLABEngine(object):
    _buffer, _buffer_size = None, 0


    def _set_buffer_size(self, val):
        self._buffer_size = val
        self._buffer = create_string_buffer(val + 1)


    def _get_buffer_size(self):
        return self._buffer_size


    buffer_size = property(_get_buffer_size, _set_buffer_size)


=======
=======
>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
# open the engine library
lib = CDLL('libeng.so')

class MATLABEngine(object):

    _buffer, _buffer_size = None, 0

    def _set_buffer_size(self, val):
        self._buffer_size = val 
        self._buffer = create_string_buffer(val + 1)

    def _get_buffer_size(self):
        return self._buffer_size

    buffer_size = property(_get_buffer_size, _set_buffer_size)

<<<<<<< HEAD
>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
=======
>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
    @property
    def output(self):
        b = self._buffer
        out = b.raw.split(b.raw[-1])[0]
        if len(out) == self._buffer_size:
            print 'MLEng output buffer filled'
        return out

<<<<<<< HEAD
<<<<<<< HEAD

    def __init__(self, startcmd="", bufsize=100 * 1024):
=======
    def __init__(self, startcmd="", bufsize=100*1024):
>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
=======
    def __init__(self, startcmd="", bufsize=100*1024):
>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
        self._eng = lib.engOpen(startcmd)
        self.buffer_size = bufsize
        lib.engOutputBuffer(self._eng, self._buffer, self.buffer_size)

<<<<<<< HEAD
<<<<<<< HEAD

    def __del__(self):
        lib.engClose(self._eng)


=======
    def __del__(self):
        lib.engClose(self._eng)

>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
=======
    def __del__(self):
        lib.engClose(self._eng)

>>>>>>> bcbe888501607d2593180265b7432448f21b31ea
    def __call__(self, cmd, out='print'):
        if not type(cmd) in (str,):
            cmd = str(cmd)

        print '>> ', cmd
        lib.engEvalString(self._eng, cmd)

        if out == 'print':
            print self.output
        elif out == 'return':
            return self.output
        else:
            pass
