# Copyright (C) 2014 Coders at Work
from .. import ServerBase

import os


class ElasticSearchServer(ServerBase):
    server_bin = 'elasticsearch'
    server_args = ['--config=%(elasticsearch_config_path)s']
    server_env = {
    }
