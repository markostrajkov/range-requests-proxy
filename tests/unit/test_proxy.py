import json
import unittest

from mock import patch, MagicMock
from rangerequestsproxy.proxy import ProxyHandler, StatsHandler


class TestStatsHandler(unittest.TestCase):

    @patch('rangerequestsproxy.proxy.START_TIME', 1000)
    @patch('rangerequestsproxy.proxy.time')
    def test_stats(self, time_mock):
        stats_handler = StatsHandler(application=MagicMock(), request=MagicMock(uri='/stats'))
        # mock the flush operation so data can be expected later
        stats_handler.finish = MagicMock()
        time_mock.time.return_value = 1050

        stats_handler.get()

        result = stats_handler._write_buffer[0].decode("utf-8")
        result = json.JSONDecoder().decode(result)

        self.assertEqual(result, {"uptime_seconds": 1050 - 1000, "total_bytes_transferred": 0})


class TestProxyHandler(unittest.TestCase):

    @patch('rangerequestsproxy.proxy.PROXY_ADDRESS', 'http://127.0.0.1:9000')
    @patch('rangerequestsproxy.proxy.tornado.httpclient.AsyncHTTPClient')
    @patch('rangerequestsproxy.proxy.TOTAL_BYTES_TRANSFERRED', 0)
    def test_successful_206_request(self, http_client_mock):
        proxy_handler = ProxyHandler(application=MagicMock(),
                                     request=MagicMock(headers={'Range': 'bytes=50-100'},
                                                       uri='/img.jpg?range=bytes=50-100'))
        proxy_handler.finish = MagicMock()
        get_argument_mock = MagicMock()
        get_argument_mock.return_value = 'bytes=50-100'
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
        self.assertEqual(proxy_handler._status_code, 206)
        self.assertEqual(proxy_handler._headers._dict['Content-Length'], '10')
        self.assertEqual(proxy_handler._headers._dict['Accept-Ranges'], 'bytes')
        self.assertEqual(proxy_handler._headers._dict['Content-Type'], 'image/jpeg')
        self.assertEqual(proxy_handler._headers._dict['Content-Range'], 'bytes 50-100/1000')
        self.assertEqual(proxy_handler._headers._dict['X-Http-Reason'], 'Partial Content')





