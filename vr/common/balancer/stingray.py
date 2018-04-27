import collections
import logging
import os
import time

import suds.xsd.doctor
import suds.client
from suds.plugin import MessagePlugin
from suds import WebFault

from . import base

logger = logging.getLogger(__name__)


# Suds has broken array marshaling.  See these links:
# http://stackoverflow.com/questions/3519818/suds-incorrect-marshaling-of-array-of-arrays
# https://fedorahosted.org/suds/ticket/340
class FixArrayPlugin(MessagePlugin):
    def marshalled(self, context):
        command = context.envelope.getChild('Body').getChildren()[0]
        # TODO: instead of blacklisting the affected types here, check the
        # actual WSDL and fix up any *ArrayArray types.
        affected = ('addNodes',
                    'addDrainingNodes',
                    'removeNodes',
                    'removeDrainingNodes',
                    'disableNodes',
                    'enableNodes',
                    'addPool',
                    )
        if command.name in affected:
            context.envelope.addPrefix(
                'xsd', 'http://www.w3.org/1999/XMLSchema',
            )
            child_spec = collections.defaultdict(
                lambda: 'values',
                addPool='nodes', disableNodes='nodes')
            values = command.getChild(child_spec[command.name])
            values.set('SOAP-ENC:arrayType', 'xsd:list[1]')
            values.set('xsi:type', 'SOAP-ENC:Array')
            item = values[0]
            item.set('SOAP-ENC:arrayType', 'xsd:list[%s]' % len(item.children))
            item.set('xsi:type', 'SOAP-ENC:Array')


class StingrayBalancer(base.Balancer):
    def __init__(self, config):
        self.url = config['URL']
        imp = suds.xsd.doctor.Import(
            'http://schemas.xmlsoap.org/soap/encoding/')
        imp.filter.add('http://soap.zeus.com/zxtm/1.0/')
        doctor = suds.xsd.doctor.ImportDoctor(imp)

        # zxtm_pool.wsdl must be present in the same directory as this file.
        here = os.path.dirname(os.path.realpath(__file__))
        wsdl = os.path.join(here, 'stingray_pool.wsdl')
        self.client = suds.client.Client(
            'file:' + wsdl,
            username=config['USER'], password=config['PASSWORD'],
            location=self.url, plugins=[doctor, FixArrayPlugin()])

        # All pool names will be prefixed with this string.
        self.pool_prefix = config.get('POOL_PREFIX', '')

        # Stingray has separate calls for disableNodes and removeNodes.  The
        # latter will interrupt current connections.  To minimize disruption,
        # we'll call disableNodes first, wait a configurable amount of time,
        # and then call removeNodes.
        self.grace_period = config.get('GRACE_PERIOD', 2)

    def _call_node_func(self, func, pool, nodes):
        # Generic function for calling any of the Stingray pool functions that
        # accept an array of pools, and an arrayarray of nodes.  This function
        # will take a single pool and nodelist and do all the necessary
        # wrapping.
        nodes_wrapper = self.client.factory.create('StringArrayArray')
        nodes_array = self.client.factory.create('StringArray')
        nodes_array.item = nodes
        nodes_wrapper.item = [nodes_array]
        func([self.pool_prefix + pool], nodes_wrapper)

    def add_nodes(self, pool, nodes):
        # Stingray will kindly avoid creating duplicates if you submit a node
        # that is already in the pool.
        logger.info('Adding nodes %s to pool %s', nodes, pool)
        try:
            self._call_node_func(self.client.service.addNodes, pool, nodes)
        except WebFault as wf:
            if 'Unknown pool' in wf.message:
                # If pool doesn't exist, create it.
                self.add_pool(pool, nodes)
            else:
                raise

    def delete_nodes(self, pool, nodes):
        existing_nodes = set(self.get_nodes(pool))
        nodes = list(existing_nodes.intersection(nodes))
        if not nodes:
            logger.info('No nodes to delete from pool %s', pool)
            return
        logger.info('Deleting nodes %s from pool %s', nodes, pool)
        try:
            self._call_node_func(self.client.service.disableNodes, pool, nodes)
            # wait <grace_period> seconds for connections to finish before
            # zapping nodes completely.
            time.sleep(self.grace_period)
            self._call_node_func(self.client.service.removeNodes, pool, nodes)
        except WebFault as wf:
            if 'Unknown pool' in wf.message:
                # If you try to delete nodes from a pool, and it doesn't exist,
                # that's fine.
                pass
            else:
                raise

        # Clean up pool in StingRay
        self.delete_pool_if_empty(pool)

    def add_pool(self, pool, nodes):
        logger.info('Adding new pool %s', pool)
        self._call_node_func(self.client.service.addPool, pool, nodes)

    def delete_pool(self, pool):
        logger.info('Deleting pool %s', pool)
        try:
            self.client.service.deletePool([self.pool_prefix + pool])
        except WebFault as wf:
            if 'Unknown pool' in str(wf):
                pass
            else:
                raise

    def delete_pool_if_empty(self, pool):
        nodes = self.get_nodes(pool)
        if not nodes:
            logger.info('Pool %s is empty', pool)
            self.delete_pool(pool)

    def get_nodes(self, pool):
        logger.info('Getting nodes for pool %s', pool)
        try:
            # get just the first item from the arrayarray
            nodes = self.client.service.getNodes([self.pool_prefix + pool])[0]
        except WebFault as wf:
            if 'Unknown pool' in wf.message:
                return []
            else:
                raise
        # convert the sax text things into real strings
        return [str(n) for n in nodes]
