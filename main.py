#!/usr/bin/env python
import errno
import logging
import os
import sys
import threading

from libs.fuse import ( # NOQA
        FUSE,
        FuseOSError,
        Operations,
        LoggingMixIn
)
from libs.rss import RSS

CONFIG_NAME = "rss_config.yaml"


# class RSSOperations(LoggingMixIn, Operations):
class RSSOperations(Operations):

    def __init__(self, root):
        self.root = os.path.realpath(root)
        self.rwlock = threading.Lock()
        self.rss = RSS(CONFIG_NAME)
        self.rss_root = self.rss.get_root()

    def __call__(self, op, path, *args):
        return super(RSSOperations, self).__call__(
                op, self.root + path, *args)

    def access(self, path, mode):
        base = path.split(self.root+"/")[1]
        if base in self.rss_root:
            return
        elif base.split("/")[0] in self.rss.rss_feeds.keys():
            return
        if not os.access(path, mode):
            raise FuseOSError(errno.EACCES)

    def open(self, path, fh):
        return 0

    def getattr(self, path, fh=None):
        base = path.split(self.root+"/")[1]
        is_feed = False
        is_root = False
        if base in self.rss_root:
            st = os.lstat(self.root)
            is_root = True
        if base.split("/")[0] in self.rss.rss_feeds.keys():
            rss_base = base.split("/")
            if len(rss_base) > 1:
                if rss_base[1] in self.rss.rss_feeds[rss_base[0]]:
                    is_feed = True
        if is_feed:
            st = os.lstat("/".join(self.root.split("/")[0:-1])+f"/{CONFIG_NAME}")
        elif not is_root:
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
        if is_feed:
            root, title = base.split("/")
            content = self.rss.get_content(self.rss.rss_feeds[root][title])
            stat["st_size"] = len(content.encode("utf-8"))
        return stat

    def read(self, path, size, offset, fh):
        base = path.split(self.root+"/")[1]
        is_feed = False
        if base.split("/")[0] in self.rss.rss_feeds.keys():
            rss_base = base.split("/")
            if len(rss_base) > 1:
                if rss_base[1] in self.rss.rss_feeds[rss_base[0]]:
                    is_feed = True
            if is_feed:
                content = self.rss.get_content(self.rss.rss_feeds[rss_base[0]][rss_base[1]])
                return content.encode("utf-8")[offset:size]
        with self.rwlock:
            f = open(path, "rb")
            f.seek(offset)
            buf = f.read(size)
            f.close()
            return buf

    def readdir(self, path, fh):
        base = path.split(self.root+"/")[1]
        if base == "":
            return [".", ".."] + self.rss_root
        if base in self.rss_root:
            return [".", ".."] + self.rss.get_titles(base)
        return [".", ".."]

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
    if len(sys.argv) < 3:
        print('usage: %s <base> <mountpoint>' % sys.argv[0])
        sys.exit(1)
    if len(sys.argv) == 4:
        if sys.argv[3].lower() == "true":
            mode = True
        elif sys.argv[3].lower() == "false":
            mode = False
    else:
        mode = True

    logging.basicConfig(level=logging.DEBUG)

    _fuse = FUSE(RSSOperations(
        sys.argv[1]),
        sys.argv[2],
        foreground=mode,
        fsname="rss-feed-mounter")
