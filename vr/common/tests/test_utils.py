import redis


def test_parse_redis_url():
    r = redis.StrictRedis.from_url('redis://:password@localhost:6379/0')
    expected = {
        'db': 0,
        'host': 'localhost',
        'port': 6379,
        'password': 'password',
    }

    for k, v in expected.items():
        assert k in r.connection_pool.connection_kwargs.keys()
        assert v == r.connection_pool.connection_kwargs[k]
