#!/usr/bin/env python3
"""Simple HTTP server for interactive sequence diagram viewer."""

import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from parser import parse_csv
from svg_renderer import render_svg

# Global model and sequence (loaded once)
MODEL = None
SEQUENCE = None

class DiagramHandler(SimpleHTTPRequestHandler):
    """Handle requests for diagram generation and static files."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/diagram':
            self.handle_diagram_request(parsed_path.query)
        elif parsed_path.path == '/api/lanes':
            self.handle_lanes_request()
        else:
            # Serve static files
            super().do_GET()
    
    def handle_diagram_request(self, query_string):
        """Generate and return an SVG diagram."""
        params = parse_qs(query_string)
        verbosity = params.get('verbosity', ['High'])[0]
        lanes_str = params.get('lanes', [''])[0]
        
        lanes_filter = None
        if lanes_str:
            lanes_filter = lanes_str.split(',')
        
        try:
            svg = render_svg(MODEL, SEQUENCE, verbosity_level=verbosity, lanes_filter=lanes_filter)
            
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(svg.encode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def handle_lanes_request(self):
        """Return available lanes."""
        lanes = SEQUENCE.get_lanes()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "lanes": lanes,
            "verbosity_levels": ["Low", "Normal", "High"]
        }).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

def run_server(port=8000):
    """Run the HTTP server."""
    global MODEL, SEQUENCE
    
    MODEL = parse_csv("sample_model.csv")
    SEQUENCE = MODEL.get_sequence("SoftReq0001")
    
    if not SEQUENCE:
        print("Error: Sequence SoftReq0001 not found")
        sys.exit(1)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DiagramHandler)
    print(f"Server running at http://localhost:{port}")
    print(f"Open http://localhost:{port}/diagram_viewer.html in your browser")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
