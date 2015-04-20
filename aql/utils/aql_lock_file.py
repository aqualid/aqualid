#
# Copyright (c) 2011-2015 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
#  OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import time
import errno

__all__ = ('FileLock', 'ErrorFileLocked')

# ==============================================================================


class ErrorFileLocked(Exception):

    def __init__(self, filename):
        msg = 'File "%s" is locked.' % (filename,)
        super(ErrorFileLocked, self).__init__(msg)

# ==============================================================================
#   General implementation
# ==============================================================================


class GeneralFileLock (object):

    __slots__ = ('lockfilename', 'filename', 'retries', 'interval')

    def __init__(self, filename, interval=0.25, timeout=5 * 60):
        filename = os.path.normcase(os.path.abspath(filename))
        self.filename = filename
        self.lockfilename = filename + '.lock'
        self.interval = interval
        self.retries = int(timeout / interval)

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_value, traceback):
        self.release_lock()

    def read_lock(self, wait=True, force=False):
        return self.write_lock(wait=wait, force=force)

    def write_lock(self, wait=True, force=False):
        if wait:
            index = self.retries
        else:
            index = 0

        while True:
            try:
                self.__lock(force=force)
                break
            except ErrorFileLocked:
                if index <= 0:
                    raise

            index -= 1
            time.sleep(self.interval)

        return self

    def __lock(self, force=False):
        try:
            os.mkdir(self.lockfilename)
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                if force:
                    return
                raise ErrorFileLocked(self.filename)

            raise

    def release_lock(self):
        try:
            os.rmdir(self.lockfilename)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise

try:
    # ==============================================================================
    #   Unix implementation
    # ==============================================================================

    import fcntl

    class UnixFileLock (object):

        __slots__ = ('fd', 'filename')

        def __init__(self, filename):
            filename = os.path.normcase(os.path.abspath(filename))
            self.filename = filename
            self.fd = None

        def __enter__(self):
            return self

        # noinspection PyUnusedLocal
        def __exit__(self, exc_type, exc_value, traceback):
            self.release_lock()

        def __open(self):

            if self.fd is None:
                self.fd = os.open(self.filename, os.O_CREAT | os.O_RDWR)

        # -----------------------------------------------------------

        def __close(self):
            os.close(self.fd)
            self.fd = None

        def read_lock(self, wait=True, force=False):
            self.__lock(write=False, wait=wait)
            return self

        def write_lock(self, wait=True, force=False):
            self.__lock(write=True, wait=wait)
            return self

        def __lock(self, write, wait):

            self.__open()

            if write:
                flags = fcntl.LOCK_EX
            else:
                flags = fcntl.LOCK_SH

            if not wait:
                flags |= fcntl.LOCK_NB

            try:
                fcntl.lockf(self.fd, flags)
            except IOError as ex:
                if ex.errno in (errno.EACCES, errno.EAGAIN):
                    raise ErrorFileLocked(self.filename)
                raise

        def release_lock(self):
            fcntl.lockf(self.fd, fcntl.LOCK_UN)
            self.__close()

    FileLock = UnixFileLock

except ImportError:
    try:
        import msvcrt
        import ctypes
        import ctypes.wintypes

        class WindowsFileLock (object):

            def __init_win_types(self):
                self.LOCKFILE_FAIL_IMMEDIATELY = 0x1
                self.LOCKFILE_EXCLUSIVE_LOCK = 0x2

                # is 64 bit
                if ctypes.sizeof(ctypes.c_ulong) !=\
                   ctypes.sizeof(ctypes.c_void_p):

                    ULONG_PTR = ctypes.c_int64
                else:
                    ULONG_PTR = ctypes.c_ulong

                PVOID = ctypes.c_void_p
                DWORD = ctypes.wintypes.DWORD
                HANDLE = ctypes.wintypes.HANDLE

                class _OFFSET(ctypes.Structure):
                    _fields_ = [
                        ('Offset', DWORD),
                        ('OffsetHigh', DWORD)
                    ]

                class _OFFSET_UNION(ctypes.Union):
                    _anonymous_ = ['_offset']

                    _fields_ = [
                        ('_offset', _OFFSET),
                        ('Pointer', PVOID)
                    ]

                class OVERLAPPED(ctypes.Structure):
                    _anonymous_ = ['_offset_union']

                    _fields_ = [
                        ('Internal', ULONG_PTR),
                        ('InternalHigh', ULONG_PTR),
                        ('_offset_union', _OFFSET_UNION),
                        ('hEvent', HANDLE)
                    ]

                LPOVERLAPPED = ctypes.POINTER(OVERLAPPED)

                self.overlapped = OVERLAPPED()
                self.poverlapped = LPOVERLAPPED(self.overlapped)

                self.LockFileEx = ctypes.windll.kernel32.LockFileEx
                self.UnlockFileEx = ctypes.windll.kernel32.UnlockFileEx

            # -----------------------------------------------------------

            def __init__(self, filename):

                self.__init_win_types()
                filename = os.path.normcase(os.path.abspath(filename))
                self.filename = filename
                self.fd = None
                self.handle = None

            # -----------------------------------------------------------

            def __enter__(self):
                return self

            # noinspection PyUnusedLocal
            def __exit__(self, exc_type, exc_value, traceback):
                self.release_lock()

            # -----------------------------------------------------------

            def __open(self):

                if self.fd is None:
                    lockfilename = self.filename + ".lock"
                    self.fd = os.open(
                        lockfilename, os.O_CREAT | os.O_RDWR | os.O_NOINHERIT)
                    self.handle = msvcrt.get_osfhandle(self.fd)

            # -----------------------------------------------------------

            def __close(self):
                os.close(self.fd)
                self.fd = None
                self.handle = None

            # -----------------------------------------------------------

            def __lock(self, write, wait):
                self.__open()

                if write:
                    flags = self.LOCKFILE_EXCLUSIVE_LOCK
                else:
                    flags = 0

                if not wait:
                    flags |= self.LOCKFILE_FAIL_IMMEDIATELY

                result = self.LockFileEx(
                    self.handle, flags, 0, 0, 4096, self.poverlapped)
                if not result:
                    raise ErrorFileLocked(self.filename)

            # -----------------------------------------------------------

            def read_lock(self, wait=True, force=False):
                self.__lock(write=False, wait=wait)
                return self

            def write_lock(self, wait=True, force=False):
                self.__lock(write=True, wait=wait)
                return self

            def release_lock(self):
                self.UnlockFileEx(self.handle, 0, 0, 4096, self.poverlapped)
                self.__close()

        FileLock = WindowsFileLock

    except ImportError:
        FileLock = GeneralFileLock
