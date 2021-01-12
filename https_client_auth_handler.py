import ssl

import http.client
import urllib.request


class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
    def __init__(self):
        super().__init__()
        self.context = ssl.create_default_context()
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE

    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(self.getConnection, req)

    def getConnection(self, host: str, timeout=120) -> http.client.HTTPSConnection:
        return http.client.HTTPSConnection(host,
                                           context=self.context,
                                           timeout=timeout)
