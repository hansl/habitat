# Copyright (C) 2013 Coders at Work
from base import ComponentBase

from threading import Thread
from wsgiref.simple_server import make_server
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Hello World!")


class DashboardComponent(ComponentBase):
    def application(self, env, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return ["Hello World 123"]

    def serve(self, host, port):
        self.httpd = make_server(host, port, self.application)
        self.httpd.serve_forever()

    def _start(self):
        self.thread = Thread(target=self.serve, args=[self['host'], int(self['port'])])
        self.thread.start()

    def _stop(self):
        Thread(target=self.httpd.shutdown).start()
        self.thread.join()
