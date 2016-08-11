import json
import os
import sys

import tornado.ioloop
import tornado.web

from rangerequestsproxy.httprange import parse_range, RangeNotSatisfiableException

DEFAULT_RANGE_SIZE = 40
PROXY_DATA = os.environ.get('RANGE_REQUESTS_PROXY_DATA')


class FileHandler(tornado.web.RequestHandler):
    def get(self):
        start = 0
        end = DEFAULT_RANGE_SIZE - 1

        try:
            range_dict = parse_range(self.request.headers.get('Range', None))
            start = range_dict['start_range']
            end = range_dict['end_range']
        except (KeyError, RangeNotSatisfiableException):
            pass

        try:
            print(PROXY_DATA + self.request.uri)
            file_size = os.stat(PROXY_DATA + self.request.uri).st_size
            with open(PROXY_DATA + self.request.uri, 'rb') as f:
                data = f.read()[start:end]

            self.set_header('Content-Type', 'image/jpeg')
            self.set_header('Content-Range', 'bytes {}-{}/{}'.format(start, end, file_size))
            self.set_status(206)
            self.write(data)
        except OSError:
            self.set_header('Content-Type', 'application/json')
            self.set_status(404)
            self.write(json.JSONEncoder().encode({
                'error': 'There is no such file',
            }))

        self.finish()


def run_proxy(port):
    app = tornado.web.Application([
        (r'.*', FileHandler),
    ])
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    port = 9000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print ("Starting HTTP Callback Server on port %d" % port)
    run_proxy(port)
