import logging
import posixpath
import random
import string
import warnings
import abc
import contextlib

import six

import paramiko
from django.conf import settings

logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Balancer(object):

    @abc.abstractmethod
    def __init__(self, config):
        pass

    @abc.abstractmethod
    def add_nodes(self, pool_name, nodes):
        pass

    @abc.abstractmethod
    def delete_nodes(self, pool_name, nodes):
        pass

    @abc.abstractmethod
    def get_nodes(self, pool_name):
        pass

    def delete_pool(self, pool_name):
        pass

    def delete_pool_if_empty(self, pool):
        nodes = self.get_nodes(pool)
        if not nodes:
            logger.info('Deleting empty pool %s', pool)
            self.delete_pool(pool)


class SshBasedBalancer(Balancer):
    """
    A helper class for writing balancer backends that are configured by SSHing
    to the balancer hosts, writing config files, and reloading config.

    Subclasses should implement _set_host_nodes and _get_host_nodes methods
    that handle reading and writing config files (but not reloading).
    """
    def __init__(self, config):
        self.user = config.get('user', settings.DEPLOY_USER)
        self.password = config.get('password', settings.DEPLOY_PASSWORD)
        self.hosts = config.get('hosts', ['localhost'])
        self.tmpdir = config.get('tmpdir', '/tmp')

    def _get_connection(self, host):
        con = paramiko.SSHClient()
        con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        con.connect(host, username=self.user, password=self.password)
        return contextlib.closing(con)

    def _read_file(self, host, path):
        # create connection
        with self._get_connection(host) as con:
            # read file with SFTP
            sftp = con.open_sftp()
            with contextlib.closing(sftp.open(path, 'rb')) as f:
                contents = f.read()

        return contents

    def _sudo(self, con, cmd):
        stdin, stdout, stderr = con.exec_command('sudo ' + cmd)
        stdin.write(self.password + '\n')
        stdin.flush()
        logger.info(stdout.read())

    def _write_file(self, host, path, contents):
        with self._get_connection(host) as con:
            # read file with SFTP
            sftp = con.open_sftp()
            # write file to temporary location
            name = ''.join(random.choice(string.lowercase) for x in range(10))
            tmppath = posixpath.join(self.tmpdir, name)
            with contextlib.closing(sftp.open(tmppath, 'wb')) as f:
                f.write(contents)
            # set perms
            sftp.chmod(tmppath, 0o644)
            # run sudo cmd to copy file to production location
            self._sudo(con, 'mv %s %s' % (tmppath, path))
            # set owner
            self._sudo(con, 'chown root %s' % path)

    def _reload_config(self, host):
        with self._get_connection(host) as con:
            # run sudo cmd to reload config
            self._sudo(con, self.reload_cmd)

    def _delete_host_nodes(self, host, pool, nodes):
        current = self._get_host_nodes(host, pool)
        correct = current.difference(nodes)
        self._set_host_nodes(host, pool, list(correct))

    def get_nodes(self, pool):
        # Look at the config files of all the hosts.  Raise a warning about any
        # mismatched pools.
        nodes = None
        for host in self.hosts:
            host_nodes = self._get_host_nodes(host, pool)
            if nodes is None:
                nodes = host_nodes
            elif host_nodes != nodes:
                tmpl = (
                    'Host %s has nodes %s for pool %s, but other hosts have %s'
                )
                msg = tmpl % (host, pool, list(host_nodes), list(nodes))
                warnings.warn(msg)
                nodes = nodes.union(host_nodes)
        if nodes:
            return list(nodes)
        return []

    def add_nodes(self, pool, nodes):
        nodeset = set(self.get_nodes(pool)).union(nodes)
        for host in self.hosts:
            self._set_host_nodes(host, pool, list(nodeset))
            self._reload_config(host)

    def delete_nodes(self, pool, nodes):
        for host in self.hosts:
            self._delete_host_nodes(host, pool, nodes)
            self._reload_config(host)
