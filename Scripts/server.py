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

# Configuration - find CSV files and HTML flexibly
def find_csv_files():
    """Search for all CSV files in common locations."""
    search_dirs = [
        "Source",
        "../Source",
        "Test/tests",
        "../Test/tests",
        ".",
        ".."
    ]
    
    csv_files = {}
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        try:
            for file in os.listdir(search_dir):
                if file.endswith('.csv'):
                    path = os.path.join(search_dir, file)
                    abs_path = os.path.abspath(path)
                    # Use filename as key (e.g., "sample_model.csv", "test_layers.csv")
                    csv_files[file] = abs_path
        except (OSError, FileNotFoundError):
            pass
    
    if not csv_files:
        raise FileNotFoundError("Could not find any CSV files")
    
    return csv_files

def find_default_csv(csv_files):
    """Find the default CSV to load (prefer sample_model.csv)."""
    if 'sample_model.csv' in csv_files:
        return 'sample_model.csv'
    # Fall back to first test CSV
    test_csvs = [f for f in csv_files if f.startswith('test_')]
    if test_csvs:
        return sorted(test_csvs)[0]
    # Last resort: first available
    return list(csv_files.keys())[0]

CSV_FILES = find_csv_files()
DEFAULT_CSV = find_default_csv(CSV_FILES)

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

HTML_PATH = find_html_file()

def load_model(csv_name=None):
    """Load model from CSV by name."""
    if csv_name is None:
        csv_name = DEFAULT_CSV
    
    if csv_name not in CSV_FILES:
        raise ValueError(f"CSV not found: {csv_name}")
    
    return parse_csv(CSV_FILES[csv_name])

def load_model_and_sequence(csv_name, sequence_id):
    """Load and return model and sequence from CSV.
    
    This is called on each request to ensure the latest CSV is loaded.
    """
    try:
        model = load_model(csv_name)
        sequence = model.get_sequence(sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")
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
        elif parsed_path.path == '/api/csvs':
            self.handle_csvs_request()
        elif parsed_path.path == '/api/lanes':
            self.handle_lanes_request()
        else:
            # Serve static files
            super().do_GET()
    
    def handle_diagram_request(self, query_string):
        """Generate and return an SVG diagram."""
        params = parse_qs(query_string)
        csv_name = params.get('csv', [DEFAULT_CSV])[0]
        sequence_id = params.get('sequence', [''])[0]
        verbosity = params.get('verbosity', ['High'])[0]
        lanes_str = params.get('lanes', [''])[0]
        
        if not sequence_id:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "sequence parameter is required"}).encode('utf-8'))
            return
        
        lanes_filter = None
        if lanes_str:
            lanes_filter = lanes_str.split(',')
        
        try:
            # Load model and sequence on each request (fresh from CSV)
            model, sequence = load_model_and_sequence(csv_name, sequence_id)
            
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
    
    def handle_csvs_request(self):
        """Return available CSV files."""
        try:
            csvs = []
            for csv_name in sorted(CSV_FILES.keys()):
                # Create a friendly name (remove .csv, replace underscores)
                friendly_name = csv_name.replace('.csv', '').replace('_', ' ').title()
                csvs.append({'id': csv_name, 'name': friendly_name})
            
            print(f"[csvs] Found {len(csvs)} CSV files: {[c['id'] for c in csvs]}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps({"csvs": csvs}).encode('utf-8'))
        except Exception as e:
            print(f"[csvs] Error: {str(e)}")
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def handle_lanes_request(self):
        """Return available lanes and sequences."""
        # Get csv from query params (default to DEFAULT_CSV)
        from urllib.parse import parse_qs, urlparse as parse_urlparse
        parsed = parse_urlparse(self.path)
        params = parse_qs(parsed.query)
        csv_name = params.get('csv', [DEFAULT_CSV])[0]
        
        try:
            # Load model from specified CSV
            model = load_model(csv_name)
            
            # Get all sequences
            sequences = [{'id': s.seq_id, 'name': s.seq_id} for s in model.sequences]
            if not sequences:
                sequences = [{'id': 'default', 'name': 'No sequences found'}]
            
            print(f"[lanes] CSV '{csv_name}': Found {len(sequences)} sequences: {[s['id'] for s in sequences]}")
            
            # Get lanes from the first sequence (if available)
            lanes = []
            if model.sequences:
                lanes = model.sequences[0].get_lanes()
            
            print(f"[lanes] Found {len(lanes)} lanes: {lanes}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps({
                "sequences": sequences,
                "lanes": lanes,
                "verbosity_levels": ["Low", "Normal", "High"]
            }).encode('utf-8'))
        except Exception as e:
            print(f"[lanes] Error: {str(e)}")
            import traceback
            traceback.print_exc()
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
    # Validate that CSVs can be loaded on startup
    try:
        if not CSV_FILES:
            raise ValueError("No CSV files found")
        
        model = load_model(DEFAULT_CSV)
        if not model.sequences:
            raise ValueError(f"No sequences found in {DEFAULT_CSV}")
        
        print(f"[OK] Found {len(CSV_FILES)} CSV file(s)")
        print(f"[OK] Default CSV '{DEFAULT_CSV}' loaded: {len(model.classes)} classes, {len(model.sequences)} sequence(s)")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DiagramHandler)
    print(f"Server running at http://localhost:{port}")
    print(f"Open http://localhost:{port} in your browser")
    print("✓ Server automatically reloads CSV on each request (no restart needed)")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
