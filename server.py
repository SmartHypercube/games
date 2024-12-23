from http.server import HTTPServer, SimpleHTTPRequestHandler


class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


if __name__ == '__main__':
    host = 'localhost'
    port = 8000
    server_address = (host, port)

    httpd = HTTPServer(server_address, HTTPRequestHandler)
    httpd.serve_forever()
