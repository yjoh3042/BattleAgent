"""Serve local_analyzer.html as the root page on port 8766."""
import http.server, os, sys

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB, **kw)
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/local_analyzer.html"
        super().do_GET()
    def log_message(self, *a):
        pass

print("Serving local_analyzer.html on http://localhost:8766", flush=True)
http.server.HTTPServer(("", 8766), Handler).serve_forever()
