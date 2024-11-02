import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

authorization_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_code
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        authorization_code = query.get('code', [None])[0]
        
        logging.info(f"Authorization code received: {authorization_code}")
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'You can close this window now.')

def run_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    logging.info('Starting HTTP server for OAuth callback...')
    httpd.handle_request()
    return authorization_code
