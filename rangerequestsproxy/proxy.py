#!/usr/bin/env python

import json
import os
import random
import re
import sys
import time

import tornado.httpclient
import tornado.httpserver
import tornado.httputil
import tornado.ioloop
import tornado.iostream
import tornado.web

from rangerequestsproxy.httprange import RangeNotSatisfiableException, parse_range


__all__ = ['ProxyHandler', 'run_proxy']
MAX_RANGE = 30
PROXY_ADDRESS = os.environ.get('RANGE_REQUESTS_PROXY_ADDRESS', '')
RANGE_REGEX = re.compile('bytes=(.*)-(.*)')
SERVICE_TEMPORARY_UNAVAILABLE = 'Service temporary unavailable: Please try again later.'
START_TIME = int(round(time.time()))
TOTAL_BYTES_TRANSFERRED = 0


class RangeRequestProxyError(Exception):
    code = 500
    message = SERVICE_TEMPORARY_UNAVAILABLE

    def __init__(self, code=500, message=SERVICE_TEMPORARY_UNAVAILABLE):
        self.message = message
        self.code = code


class StatsHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(json.JSONEncoder().encode({
            "total_bytes_transferred": TOTAL_BYTES_TRANSFERRED,
            "uptime_seconds": int(round(time.time())) - START_TIME  # TODO: format it nicely
        }))
        self.finish()


class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self):
        try:
            headers = self._validate_request()
            self._fetch_request(self.request.uri, self._handle_response_callback, body=None, headers=headers)
        except RangeNotSatisfiableException as e:
            self._set_error(code=e.code, message=e.message)
            self.finish()
        except RangeRequestProxyError as e:
            self._set_error(code=e.code, message=e.message)
            self.finish()
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                self.handle_response(e.response)
            else:
                self._set_error(code=500, message='Internal server error: ' + str(e))
                self.finish()

    def _validate_request(self):
        headers = {}
        range_from_header = self.request.headers.get('Range', None)
        range_from_query = self.get_argument("range", None)

        if not range_from_header and not range_from_query:
            headers['Range'] = 'bytes=0-'
        elif range_from_header and not range_from_query:
            _ = parse_range(range_from_header)
            headers['Range'] = range_from_header
        elif not range_from_header and range_from_query:
            _ = parse_range(range_from_query)
            headers['Range'] = range_from_query
        else:
            if parse_range(range_from_header) != parse_range(range_from_query):
                raise RangeNotSatisfiableException
            headers['Range'] = range_from_header
        return headers

    def _fetch_request(self, url, callback, body=None, headers=None):
        upstream_host = ProxyHandler._get_upstream_server_address(PROXY_ADDRESS)
        if upstream_host:
            tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        else:
            raise RangeRequestProxyError(code=500, message=SERVICE_TEMPORARY_UNAVAILABLE)

        full_url = "{}{}".format(upstream_host, url)
        req = tornado.httpclient.HTTPRequest(full_url,
                                             body=body,
                                             headers=headers,
                                             method=self.request.method,
                                             allow_nonstandard_methods=True,
                                             follow_redirects=False)
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(req, callback, raise_error=False)

    def _handle_response_callback(self, response):
        if response.error and isinstance(response.error, tornado.httpclient.HTTPError):
            if response.body:
                self.set_status(response.code)
                for header, val in response.headers.get_all():
                    self.set_header(header, val)
                self.write(response.body.decode("utf-8"))
                self.set_header('Content-Type', 'application/json')
            else:
                self._set_error(code=500, message=SERVICE_TEMPORARY_UNAVAILABLE)
        elif response.error and not isinstance(response.error, tornado.httpclient.HTTPError):
            self._set_error(code=500, message=SERVICE_TEMPORARY_UNAVAILABLE)
        else:
            try:
                self.set_status(response.code)
                for header, val in response.headers.get_all():
                    self.set_header(header, val)

                if response.body:
                    global TOTAL_BYTES_TRANSFERRED
                    total_bytes = len(response.body)
                    TOTAL_BYTES_TRANSFERRED += total_bytes
                    self.set_header('Content-Length', total_bytes)
                    self.set_header('Accept-Ranges', 'bytes')
                    self.write(response.body)
            except Exception:
                self._set_error(code=500, message=SERVICE_TEMPORARY_UNAVAILABLE)
        self.finish()

    @staticmethod
    def _get_upstream_server_address(addresses):
        # Override this method to insert custom logic for selecting upstream server
        addresses_list = addresses.split(',')
        return addresses_list[random.randint(0, len(addresses_list) - 1)] if addresses_list else None

    def _set_error(self, code=500, message=''):
        self.set_status(code)
        self.set_header('Content-Type', 'application/json')
        self.write(json.JSONEncoder().encode({
            "error": message,
        }))


def run_proxy(port):
    app = tornado.web.Application([
        (r"/stats", StatsHandler),
        (r'.*', ProxyHandler),
    ])
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print ("Starting Range Requests HTTP proxy on port %d" % port)
    run_proxy(port)
