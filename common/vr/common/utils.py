from __future__ import print_function

import sys
import os
import subprocess
import shutil
import tempfile
import random
import string
import hashlib
import errno
from datetime import datetime

try:
    import pwd
    import grp
    import fcntl
except ImportError:
    # bypass import failure on Windows
    pass

import isodate
import six


class tmpdir(object):
    """Context manager for putting you into a temporary directory on enter
    and deleting the directory on exit
    """
    def __init__(self):
        self.orig_path = os.getcwd()

    def __enter__(self):
        self.temp_path = tempfile.mkdtemp()
        os.chdir(self.temp_path)
        return self.temp_path

    def __exit__(self, type, value, traceback):
        os.chdir(self.orig_path)
        shutil.rmtree(self.temp_path, ignore_errors=True)


class chdir(object):
    def __init__(self, folder):
        self.orig_path = os.getcwd()
        self.temp_path = folder

    def __enter__(self):
        os.chdir(self.temp_path)

    def __exit__(self, type, value, traceback):
        os.chdir(self.orig_path)


def mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


class CommandException(Exception):
    """
    Custom exception class for displaying nice input from failed commands.
    Accepts an CommandResult object on init.
    """

    def __init__(self, result):
        template = six.text_type(
            "Command '{result.command}' failed with status code "
            "{result.status_code}.\noutput: {result.output}\n"
        )
        message = template.format(result=result)
        super(CommandException, self).__init__(message)


class CommandResult(object):
    def __init__(self, command, output, status_code):
        self.command = command
        self.output = six.text_type(output, 'ascii', 'replace')
        self.status_code = status_code

    def __repr__(self):
        return '<CommandResult: %s,%s>' % (self.status_code, self.command)

    def raise_for_status(self):
        if self.status_code != 0:
            raise CommandException(self)


def run(command, verbose=False):
    """
    Run a shell command.  Capture the stdout and stderr as a single stream.
    Capture the status code.

    If verbose=True (the default), then print command and the output to the
    terminal.

    """
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output = ""
    status_code = None
    if verbose:
        print("run:", command)
    while status_code is None:
        status_code = p.poll()
        line = p.stdout.readline()
        if verbose:
            sys.stdout.write(line)
        output += line
    return CommandResult(command, output, status_code)


def parse_redis_url(url):
    """
    Given a url like redis://localhost:6379/0, return a dict with host, port,
    and db members.
    """
    parsed = six.moves.urllib.parse.urlsplit(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'db': int(parsed.path.replace('/', '')),
    }


utc = isodate.FixedOffset(0, 0, 'UTC')

def utcfromtimestamp(ts):
    """
    Given a UNIX timestamp, return a Python datetime with the tzinfo explicitly
    set to UTC (as opposed to datetime.utcfromtimestamp, which returns a naive
    datetime with UTC values).
    """
    dt = datetime.utcfromtimestamp(ts)
    return dt.replace(tzinfo=utc)


def randchars(num=8):
    return ''.join(random.choice(string.ascii_lowercase) for x in range(num))


def lock_file(f, block=False):
    """
    If block=False (the default), die hard and fast if another process has
    already grabbed the lock for this file.

    If block=True, wait for the lock to be released, then continue.
    """
    try:
        flags = fcntl.LOCK_EX
        if block:
            flags |= fcntl.LOCK_NB
        fcntl.flock(f.fileno(), flags)
    except IOError as e:
        if e.errno in (errno.EACCES, errno.EAGAIN):
            raise SystemExit("ERROR: %s is locked by another process." %
                             f.name)
        raise


def file_md5(filename):
    """
    Given a path to a file, read it chunk-wise and feed each chunk into
    an MD5 file hash.  Avoids having to hold the whole file in memory.
    """
    md5 = hashlib.md5()
    with open(filename,'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def which(name, flags=os.X_OK):
    """
    Search PATH for executable files with the given name.

    Taken from Twisted.
    """
    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    if path is None:
        return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    return result


def chowntree(path, username=None, groupname=None):
    if username is None and groupname is None:
        raise ValueError("Must provide username and/or groupname")

    # os.chown will let you pass -1 to leave user or group unchanged.
    uid = -1
    gid = -1

    if username:
        uid = pwd.getpwnam(username).pw_uid

    if groupname:
        gid = grp.getgrnam(groupname).gr_gid

    os.chown(path, uid, gid)

    for root, dirs, files in os.walk(path):
        for d in dirs:
            dpath = os.path.join(root, d)
            os.chown(dpath, uid, gid)
        for f in files:
            fpath = os.path.join(root, f)
            if not os.path.islink(fpath):
                os.chown(fpath, uid, gid)
