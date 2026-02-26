#!/usr/bin/env python3
"""Simple HTTP server for interactive sequence diagram viewer."""

import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from parser import parse_csv
from svg_renderer import render_svg

#!/usr/bin/env python3
"""Simple HTTP server for interactive sequence diagram viewer."""

import json
import sys
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from parser import parse_csv
from svg_renderer import render_svg

# Configuration - find CSV file and HTML flexibly
def find_csv_file():
    """Search for sample_model.csv in common locations."""
    search_paths = [
        "Source/sample_model.csv",
        "../Source/sample_model.csv",
        "sample_model.csv",
        "../sample_model.csv",
        "Test/sample_model.csv",
        "../Test/sample_model.csv",
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    raise FileNotFoundError("Could not find sample_model.csv in any standard location")

def find_html_file():
    """Search for diagram_viewer.html relative to this script."""
    # First try relative to the Scripts directory where this file is
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_html = os.path.join(script_dir, 'diagram_viewer.html')
    if os.path.exists(script_html):
        return script_html
    
    # Fallback search paths
    search_paths = [
        "Scripts/diagram_viewer.html",
        "../Scripts/diagram_viewer.html",
        "diagram_viewer.html",
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    raise FileNotFoundError("Could not find diagram_viewer.html in any standard location")

CSV_PATH = find_csv_file()
HTML_PATH = find_html_file()
SEQUENCE_ID = "SoftReq0001"

def load_model_and_sequence():
    """Load and return model and sequence from CSV.
    
    This is called on each request to ensure the latest CSV is loaded.
    """
    try:
        model = parse_csv(CSV_PATH)
        sequence = model.get_sequence(SEQUENCE_ID)
        if not sequence:
            raise ValueError(f"Sequence {SEQUENCE_ID} not found")
        return model, sequence
    except Exception as e:
        raise RuntimeError(f"Failed to load CSV: {str(e)}")

class DiagramHandler(SimpleHTTPRequestHandler):
    """Handle requests for diagram generation and static files."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '':
            # Serve the HTML viewer at the root
            try:
                with open(HTML_PATH, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error loading HTML: {str(e)}".encode('utf-8'))
        elif parsed_path.path == '/api/diagram':
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
            # Load model and sequence on each request (fresh from CSV)
            model, sequence = load_model_and_sequence()
            
            svg = render_svg(model, sequence, verbosity_level=verbosity, lanes_filter=lanes_filter)
            
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(svg.encode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def handle_lanes_request(self):
        """Return available lanes."""
        try:
            # Load model and sequence on each request (fresh from CSV)
            model, sequence = load_model_and_sequence()
            
            lanes = sequence.get_lanes()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps({
                "lanes": lanes,
                "verbosity_levels": ["Low", "Normal", "High"]
            }).encode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

def run_server(port=8000):
    """Run the HTTP server."""
    # Validate that CSV can be loaded on startup
    try:
        model, sequence = load_model_and_sequence()
        print(f"[OK] CSV loaded successfully with {len(model.classes)} classes and sequence '{sequence.seq_id}'")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DiagramHandler)
    print(f"Server running at http://localhost:{port}")
    print(f"Open http://localhost:{port}/diagram_viewer.html in your browser")
    print(f"CSV file: {CSV_PATH}")
    print("✓ Server automatically reloads CSV on each request (no restart needed)")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
