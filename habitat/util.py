# Copyright (C) 2013 Coders at Work
import socket

def is_port_in_use(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', port))
    except socket.error, e:
        print "address already in use"
    else:
        s.close()
