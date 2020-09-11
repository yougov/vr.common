import os

from vr.common import repo
from vr.common.utils import tmpdir, run
from vr.common.tests import tmprepo

import pytest


def _exists_exe(exe):
    from distutils.spawn import find_executable
    return find_executable(exe) is not None


skipif_nogit = pytest.mark.skipif(not _exists_exe('git'), reason="no hg")


def _git_config():
    run('git config user.email "you@example.com"')
    run('git config --global user.name "Your Name"')


@skipif_nogit
class TestGit(object):

    def test_git_folder_detection(self):
        with tmpdir():
            folder = os.path.abspath('.git')
            run('mkdir -p %s' % folder)
            assert repo.guess_folder_vcs(os.getcwd()) == 'git'

    def test_git_scheme_detection(self):
        url = 'git://github.com/heroku/heroku-buildpack-python'
        assert repo.guess_url_vcs(url) == 'git'

    def test_git_suffix_detection(self):
        url = 'https://github.com/heroku/heroku-buildpack-python.git'
        assert repo.guess_url_vcs(url) == 'git'

    def test_basename(self):
        url = 'https://github.com/heroku/heroku-buildpack-python.git'
        assert repo.basename(url) == 'heroku-buildpack-python'

    def test_basename_fragment(self):
        url = 'https://github.com/heroku/heroku-buildpack-python.git#123456'
        assert repo.basename(url) == 'heroku-buildpack-python'

    def test_git_clone(self):
        url = 'https://github.com/btubbs/vr_python_example.git'
        with tmpdir():
            gitrepo = repo.Repo('gitrepo', url, 'git')
            gitrepo.clone()
            assert gitrepo.get_url() == url

    def test_git_get_version(self):
        rev = '16c1dba07ee78d5dbee1f965d91d3d61942ccb67'
        with tmprepo('git_python_app.tar.gz', 'git') as r:
            _git_config()
            r.update(rev)
            assert r.version == rev

    def test_git_get_short_version(self):
        rev = '16c1dba07'
        with tmprepo('git_python_app.tar.gz', 'git') as r:
            _git_config()
            r.update(rev)
            assert r.version.startswith(rev)

    def test_git_detached_tag(self):
        with tmprepo('git_python_app.tar.gz', 'git') as r:
            _git_config()
            r.update('detached-tag')
            assert r.version.startswith('1418411')

    def test_diverged_branch(self):
        with tmprepo('git_python_app.tar.gz', 'git') as r:
            _git_config()
            r.update('master')
            assert r.version.startswith('9913c8a')

    def test_git_update(self):
        newrev = '6c79fb7d071a9054542114eea70f69d5361a61ff'
        oldrev = '16c1dba07ee78d5dbee1f965d91d3d61942ccb67'
        with tmprepo('git_python_app.tar.gz', 'git') as r:
            _git_config()

            r.update(newrev)
            f = 'newfile'
            assert os.path.isfile(f)

            r.update(oldrev)
            assert not os.path.isfile(f)


class TestSvn(object):

    def test_svn_folder_detection(self):
        with tmpdir():
            folder = os.path.abspath('.svn')
            run('mkdir -p %s' % folder)

            assert repo.guess_folder_vcs(os.getcwd()) == 'svn'
