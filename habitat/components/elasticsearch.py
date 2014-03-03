# Copyright (C) 2014 Coders at Work
from .. import ServerBase

import os


class ElasticSearchServer(ServerBase):
    server_bin = 'elasticsearch'

    server_args = [
        '--config=%(elasticsearch_config_path)s',
        '%(http_port_arg)s',
        '-Des.network.host=%(host)s'
    ]

    server_env = {
    }

    # This server waits for this before being considered started.
    wait_for_regex = r' started$'

    class KeyValueDefault:
        nb_ports = 2

    def http_port_arg(self):
        port = self['port']
        if not port:
            self['port'] = self.random_port(2)
            port = self['port']
        print port
        if isinstance(port, list):
            http_port = port[0]
        elif isinstance(port, dict):
            http_port = port['http']
        else:
            http_port = port

        return '-Des.http.port=%d' % http_port
