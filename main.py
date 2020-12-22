#!/usr/bin/env python
import errno
import logging
import os
import sys
import threading

from fuse.fuse import ( # NOQA
        FUSE,
        FuseOSError,
        Operations,
        LoggingMixIn
)


class RSSOperations(LoggingMixIn, Operations):

    def __init__(self, root):
        self.root = os.path.realpath(root)
        self.rwlock = threading.Lock()

    def __call__(self, op, path, *args):
        return super(RSSOperations, self).__call__(
                op, self.root + path, *args)

    def access(self, path, mode):
        path = path
        if not os.access(path, mode):
            raise FuseOSError(errno.EACCES)

    def open(self, path, fh):
        return 0

    def getattr(self, path, fh=None):
        path = path
        st = os.lstat(path)
        stat = dict(
                (key, getattr(st, key))
                for key in (
                    'st_atime',
                    'st_ctime',
                    'st_gid',
                    'st_mode',
                    'st_mtime',
                    'st_nlink',
                    'st_size',
                    'st_uid'))
        return stat

    def read(self, path, size, offset, fh):
        with self.rwlock:
            f = open(path, "rb")
            f.seek(offset)
            return f.read(size)

    def readdir(self, path, fh):
        base = path.split(self.root)[1]
        basepath = "/".join(
                [branch
                 for branch in base.split("/") if branch])
        path = self.root + "/" + basepath
        return ['.', '..'] + [
                name for name in os.listdir(path)]

    readlink = os.readlink

    def statfs(self, path):
        stv = os.statvfs(path)
        stat = dict((
            key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                'f_blocks', 'f_bsize',
                                                'f_favail', 'f_ffree',
                                                'f_files', 'f_flag',
                                                'f_frsize', 'f_namemax'))
        return stat

    def symlink(self, target, source):
        return os.symlink(source, target)

    def link(self, target, source):
        return os.link(source, target)

    # Disable unused operations:
    flush = None
    getxattr = None
    listxattr = None
    opendir = None
    releasedir = None
    release = None
    chmod = None
    chown = None
    write = None
    utimens = None
    unlink = None
    truncate = None
    rmdir = None
    rename = None
    mkdir = None
    create = None
    mknod = None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: %s <mountpoint>' % sys.argv[0])
        sys.exit(1)
    if len(sys.argv) == 3:
        if sys.argv[2].lower() == "true":
            mode = True
        elif sys.argv[2].lower() == "false":
            mode = False
    else:
        mode = True

    logging.basicConfig(level=logging.DEBUG)

    _fuse = FUSE(RSSOperations(
        "rss_base"),
        sys.argv[1],
        foreground=mode,
        fsname="rss-feed-mounter")
