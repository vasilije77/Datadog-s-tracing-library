"""Instrument Cassandra to report Cassandra queries.

Patch your Cluster instance to make it work.

    from ddtrace import Pin, patch
    from cassandra.cluster import Cluster

    # Instrument Cassandra
    patch(cassandra=True)

    # This will report spans with the default instrumentation
    cluster = Cluster(contact_points=["127.0.0.1"], port=9042)
    session = cluster.connect("my_keyspace")
    # Example of instrumented query
    session.execute("select id from my_table limit 10;")

    # To customize one cluster instance instrumentation
    cluster = Cluster(contact_points=['10.1.1.3', '10.1.1.4', '10.1.1.5'], port=9042)
    Pin(service='cassandra-backend').onto(cluster)
    session = cluster.connect("my_keyspace")
    session.execute("select id from my_table limit 10;")
"""
from ..util import require_modules

required_modules = ['cassandra.cluster']

with require_modules(required_modules) as missing_modules:
    if not missing_modules:
        from .session import get_traced_cassandra, patch
        __all__ = [
            'get_traced_cassandra',
            'patch',
        ]
