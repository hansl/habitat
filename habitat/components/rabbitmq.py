# Copyright (C) 2014 Coders at Work
from .. import ServerBase

import os


class RabbitMqServer(ServerBase):
    server_bin = 'rabbitmq-server'
    server_args = []
    server_env = {
        'RABBITMQ_NODENAME': '%(rabbitmq_nodename)s',
        'RABBITMQ_NODE_IP_ADDRESS': '%(hostname)s',
        'RABBITMQ_NODE_PORT': '%(port)s',
    }
    wait_for_regex = r'completed with \d+ plugins.$'
