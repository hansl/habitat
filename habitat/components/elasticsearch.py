# Copyright (C) 2014 Coders at Work
from .. import ServerBase

import os


class ElasticSearchServer(ServerBase):
    server_bin = 'elasticsearch'

    server_args = [
        '--config=%(elasticsearch_config_path)s',
        '-Des.http.port=%(port)d',
        '-Des.network.host=%(host)s'
    ]

    server_env = {
    }

    # This server waits for this before being considered started.
    wait_for_regex = r'\] started'
