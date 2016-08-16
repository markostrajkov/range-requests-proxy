import json
import unittest

from mock import patch, MagicMock
from rangerequestsproxy.proxy import ProxyHandler, StatsHandler
from tornado.httpclient import HTTPError


class TestStatsHandler(unittest.TestCase):
    @patch('rangerequestsproxy.proxy.START_TIME', 1000)
    @patch('rangerequestsproxy.proxy.time')
    def test_stats(self, time_mock):
        """
            Simulates following request:
            curl -i http://localhost:8000/stats
        """
        stats_handler = StatsHandler(application=MagicMock(), request=MagicMock(uri='/stats'))
        # mock the flush operation so data can be expected later
        stats_handler.finish = MagicMock()
        time_mock.time.return_value = 1050

        stats_handler.get()

        result = stats_handler._write_buffer[0].decode("utf-8")
        result = json.JSONDecoder().decode(result)

        self.assertEqual(result, {"uptime_seconds": 1050 - 1000, "total_bytes_transferred": 0})

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.START_TIME', 1000)
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    @patch('rangerequestsproxy.proxy.tornado.httpclient.AsyncHTTPClient')
    @patch('rangerequestsproxy.proxy.time')
    def test_stats_total_bytes_transferred(self, time_mock, http_client_mock):
        """
            Simulates following request:
            curl -i http://localhost:8000/stats
        """
        self.make_some_valid_request(http_client_mock)

        stats_handler = StatsHandler(application=MagicMock(), request=MagicMock(uri='/stats'))
        stats_handler.finish = MagicMock()
        time_mock.time.return_value = 1050

        stats_handler.get()

        result = stats_handler._write_buffer[0].decode("utf-8")
        result = json.JSONDecoder().decode(result)

        self.assertEqual(result, {"uptime_seconds": 1050 - 1000, "total_bytes_transferred": 10})

    def make_some_valid_request(self, http_client_mock):
        """
            Simulates following request:
            curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg?range=bytes=0-50
        """
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=0-50'},
                                                       uri='/img.jpg?range=bytes=0-50'))
        proxy_handler.finish = MagicMock()
        get_argument_mock = MagicMock()
        get_argument_mock.return_value = 'bytes=0-50'
        proxy_handler.get_argument = get_argument_mock

        def fetch_mock(req, callback, raise_error=False):
            all_headers = MagicMock()
            all_headers.get_all.return_value = [('Content-Type', 'image/jpeg'),
                                                ('Content-Range', 'bytes 50-100/1000'),
                                                ('X-Http-Reason', 'Partial Content')]
            response_mock = MagicMock(error=None, code=206, body=b'0123456789', headers=all_headers)
            callback(response_mock)

        http_client_mock.return_value.fetch = fetch_mock

        proxy_handler.get()

        self.assertEqual(proxy_handler._write_buffer[0], b'0123456789')


class TestProxyHandler(unittest.TestCase):

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.tornado.httpclient.AsyncHTTPClient')
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    def test_successful_206_request_with_valid_ranges(self, http_client_mock):
        """
            Simulates following request:
            curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg?range=bytes=0-50
        """
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=0-50'},
                                                       uri='/img.jpg?range=bytes=0-50'))
        proxy_handler.finish = MagicMock()
        get_argument_mock = MagicMock()
        get_argument_mock.return_value = 'bytes=0-50'
        proxy_handler.get_argument = get_argument_mock

        def fetch_mock(req, callback, raise_error=False):
            all_headers = MagicMock()
            all_headers.get_all.return_value = [('Content-Type', 'image/jpeg'),
                                                ('Content-Range', 'bytes 0-50/1000'),
                                                ('X-Http-Reason', 'Partial Content')]
            response_mock = MagicMock(error=None, code=206, body=b'0123456789', headers=all_headers)
            callback(response_mock)

        http_client_mock.return_value.fetch = fetch_mock

        proxy_handler.get()

        self.assertEqual(proxy_handler._write_buffer[0], b'0123456789')
        self.assertEqual(proxy_handler._status_code, 206)
        self.assertEqual(proxy_handler._headers._dict['Content-Length'], '10')
        self.assertEqual(proxy_handler._headers._dict['Accept-Ranges'], 'bytes')
        self.assertEqual(proxy_handler._headers._dict['Content-Type'], 'image/jpeg')
        self.assertEqual(proxy_handler._headers._dict['Content-Range'], 'bytes 0-50/1000')
        self.assertEqual(proxy_handler._headers._dict['X-Http-Reason'], 'Partial Content')

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    def test_requesterange_not_satisfiable_intervals_do_not_match(self):
        """
            Simulates following request:
            curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg?range=bytes=50-100
        """
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=0-50'},
                                                       uri='/img.jpg?range=bytes=50-100'))
        proxy_handler.finish = MagicMock()
        get_argument_mock = MagicMock()
        get_argument_mock.return_value = 'bytes=50-100'
        proxy_handler.get_argument = get_argument_mock

        proxy_handler.get()

        result = proxy_handler._write_buffer[0].decode("utf-8")
        result = json.JSONDecoder().decode(result)
        self.assertEqual(result, {"error": "Requested Range Not Satisfiable. "})
        self.assertEqual(proxy_handler._status_code, 416)
        self.assertEqual(proxy_handler._headers._dict['Content-Type'], 'application/json')

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    def test_requested_range_not_satisfiable_invalid_range(self):
        """
            Simulates following request:
            curl -i --header "Range: bytes=a-50" http://localhost:8000/img.jpg?range=bytes=50-100
        """
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=a-50'},
                                                       uri='/img.jpg'))
        proxy_handler.finish = MagicMock()

        proxy_handler.get()

        result = proxy_handler._write_buffer[0].decode("utf-8")
        result = json.JSONDecoder().decode(result)
        self.assertEqual(result, {"error": "Requested Range Not Satisfiable. Invalid start or end interval."})
        self.assertEqual(proxy_handler._status_code, 416)
        self.assertEqual(proxy_handler._headers._dict['Content-Type'], 'application/json')

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.tornado.httpclient.AsyncHTTPClient')
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    def test_upstream_server_not_available(self, http_client_mock):
        """
            Simulates following request:
            curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg
        """
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=0-50'},
                                                       uri='/img.jpg'))
        proxy_handler.finish = MagicMock()

        def fetch_mock(req, callback, raise_error=False):
            response_mock = MagicMock(error=HTTPError(code=500), body=None, code=500)
            callback(response_mock)

        http_client_mock.return_value.fetch = fetch_mock

        proxy_handler.get()

        result = proxy_handler._write_buffer[0].decode("utf-8")
        result = json.JSONDecoder().decode(result)
        self.assertEqual(result, {"error": "Service temporary unavailable: Please try again later."})
        self.assertEqual(proxy_handler._status_code, 500)
        self.assertEqual(proxy_handler._headers._dict['Content-Type'], 'application/json')

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.tornado.httpclient.AsyncHTTPClient')
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    def test_file_not_found(self, http_client_mock):
        """
            Simulates following request:
            curl -i --header "Range: bytes=0-50" http://localhost:8000/img.jpg
        """
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=0-50'},
                                                       uri='/img_do_not_exists.jpg'))
        proxy_handler.finish = MagicMock()

        def fetch_mock(req, callback, raise_error=False):
            response_mock = MagicMock(error=HTTPError(code=404),
                                      body=b'{"error": "There is no such file"}',
                                      code=404)
            callback(response_mock)

        http_client_mock.return_value.fetch = fetch_mock

        proxy_handler.get()

        result = proxy_handler._write_buffer[0].decode("utf-8")
        result = json.JSONDecoder().decode(result)
        self.assertEqual(result, {"error": "There is no such file"})
        self.assertEqual(proxy_handler._status_code, 404)
        self.assertEqual(proxy_handler._headers._dict['Content-Type'], 'application/json')

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.tornado.httpclient.AsyncHTTPClient')
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    def test_successful_206_request_with_valid_ranges_and_ifrange(self, http_client_mock):
        """
            Simulates following request:
            curl -i --header "Range: bytes=0-50" \
                    --header "If-Range: Sat, 29 Oct 1994 19:43:31 GMT" \
                    http://localhost:8000/img.jpg?range=bytes=0-50
            P.S. Proxy does not validate IF-Range parameter, it just passes it further
            HTTP Date Format: RFC7231, Chapter 7.1.1.1
        """
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=0-50',
                                                                'If-Range': 'Sat, 29 Oct 1994 19:43:31 GMT'},
                                                       uri='/img.jpg?range=bytes=0-50'))
        proxy_handler.finish = MagicMock()
        get_argument_mock = MagicMock()
        get_argument_mock.return_value = 'bytes=0-50'
        proxy_handler.get_argument = get_argument_mock

        def fetch_mock(req, callback, raise_error=False):
            all_headers = MagicMock()
            all_headers.get_all.return_value = [('Content-Type', 'image/jpeg'),
                                                ('Content-Range', 'bytes 0-50/1000'),
                                                ('X-Http-Reason', 'Partial Content')]
            response_mock = MagicMock(error=None, code=206, body=b'0123456789', headers=all_headers)
            callback(response_mock)

        http_client_mock.return_value.fetch = fetch_mock

        proxy_handler.get()

        self.assertEqual(proxy_handler._write_buffer[0], b'0123456789')
        self.assertEqual(proxy_handler._status_code, 206)
        self.assertEqual(proxy_handler._headers._dict['Content-Length'], '10')
        self.assertEqual(proxy_handler._headers._dict['Accept-Ranges'], 'bytes')
        self.assertEqual(proxy_handler._headers._dict['Content-Type'], 'image/jpeg')
        self.assertEqual(proxy_handler._headers._dict['Content-Range'], 'bytes 0-50/1000')
        self.assertEqual(proxy_handler._headers._dict['X-Http-Reason'], 'Partial Content')
