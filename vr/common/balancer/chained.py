from . import base


def import_class(path):
    try:
        module, dot, klass = path.rpartition('.')
        imported = __import__(module, globals(), locals(), [klass, ], -1)
        return getattr(imported, klass)
    except Exception as e:
        raise ImportError(e)


class ChainedBalancer(base.Balancer):
    """A balancer that interfaces with multiple balancers.

    Configure with:

        my-balancer:
            BACKEND: vr.common.balancer.chained.ChainedBalancer
            BALANCERS:
            - BACKEND: vr.common.balancer.stingray.StingrayBalancer
              PASSWORD: secret
              POOL_PREFIX: Auto vraptor-
              URL: https://some-url/
              USER: user
            - BACKEND: vr.common.balancer.stingray.StingrayBalancer
              PASSWORD: more-secret
              POOL_PREFIX: Auto vraptor-
              URL: https://some-other-url/
              USER: other-user
    """

    def __init__(self, config):
        balancers = []
        for cfg in config['BALANCERS']:
            cls = import_class(cfg['BACKEND'])
            balancers.append(cls(cfg))
        self._balancers = balancers

    def _foreach_balancer(self, method, args=None, kwargs=None):
        args = args if args else ()
        kwargs = kwargs if kwargs else {}
        for b in self._balancers:
            getattr(b, method)(*args, **kwargs)

    def add_nodes(self, pool_name, nodes):
        self._foreach_balancer('add_nodes', (pool_name, nodes))

    def delete_nodes(self, pool_name, nodes):
        self._foreach_balancer('delete_nodes', (pool_name, nodes))

    def get_nodes(self, pool_name):
        nodes = []
        for b in self._balancers:
            nodes.extend(b.get_nodes(pool_name))
        return sorted(set(nodes))

    def delete_pool(self, pool):
        self._foreach_balancer('delete_pool', (pool, ))
