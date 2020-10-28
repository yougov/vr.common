import os

from vr.common import repo
from vr.common.utils import tmpdir, run
from vr.common.tests import tmprepo

import pytest


def _exists_exe(exe):
    from distutils.spawn import find_executable
    return find_executable(exe) is not None


skipif_nohg = pytest.mark.skipif(not _exists_exe('hg'), reason="no hg")
skipif_nogit = pytest.mark.skipif(not _exists_exe('git'), reason="no hg")

def _git_config():
    run('git config user.email "you@example.com"')
    run('git config --global user.name "Your Name"')

@pytest.mark.xfail
class TestHg(object):

    def test_hg_folder_detection(self):
        with tmpdir():
            folder = os.path.abspath('.hg')
            run('mkdir -p %s' % folder)
            assert repo.guess_folder_vcs(os.getcwd()) == 'hg'

    # TODO: Run local git/hg servers so we don't have to call out over
    # the network during tests.
    def test_hg_clone(self):
        url = 'https://bitbucket.org/btubbs/vr_python_example'
        with tmpdir():
            hgrepo = repo.Repo('hgrepo', url, 'hg')
            hgrepo.clone()
            assert hgrepo.get_url() == url

    def test_hg_update_norev(self):
        with tmprepo('hg_python_app.tar.gz', 'hg') as r:
            # rev defaults to tip
            r.update()
            assert r.version == '802efadda217'

    def test_hg_get_version(self):
        rev = '496e15fd973f'
        with tmprepo('hg_python_app.tar.gz', 'hg') as r:
            r.update(rev)
            assert r.version == rev

    def test_hg_update(self):
        newrev = '13b6ce1e234a'
        oldrev = '496e15fd973f'
        with tmprepo('hg_python_app.tar.gz', 'hg') as r:
            r.update(newrev)
            f = 'newfile'
            assert os.path.isfile(f)

            r.update(oldrev)
            assert not os.path.isfile(f)

    def test_basename_trailing_space(self):
        # Catches https://bitbucket.org/yougov/velociraptor/issue/10/
        url = "ssh://hg@bitbucket.org/yougov/velociraptor "
        assert repo.basename(url) == 'velociraptor'


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
