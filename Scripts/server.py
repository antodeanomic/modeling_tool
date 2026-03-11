#!/usr/bin/env python3
"""Simple HTTP server for interactive diagram viewer."""

import json
import sys
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from parser import parse_csv
from svg_renderer import render_svg
from class_diagram_renderer import render_class_diagram_svg

# Configuration - find CSV files and HTML flexibly
def find_csv_files():
    """Search for all CSV files in common locations relative to this script."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build search paths relative to script directory
    search_dirs = [
        os.path.join(script_dir, '../Source'),              # ../Source from Scripts/
        os.path.join(script_dir, '../Test/tests'),          # ../Test/tests from Scripts/
        os.path.join(script_dir, '../tests'),               # ../tests from Scripts/ (for Test subdir)
        os.path.join(script_dir, '../Process/architecture'), # ../Process/architecture from Scripts/
        os.path.join(script_dir, '.'),                      # Scripts/ itself
        os.path.join(script_dir, '..'),                     # Parent of Scripts/
    ]
    
    # Also check current working directory just in case
    search_dirs.extend([
        "Source",
        "tests",
        "Test/tests",
        "Process/architecture",
        ".",
    ])
    
    csv_files = {}
    for search_dir in search_dirs:
        # Normalize and check if it exists
        normalized_dir = os.path.normpath(search_dir)
        if not os.path.isdir(normalized_dir):
            continue
        try:
            for file in os.listdir(normalized_dir):
                if file.endswith('.csv'):
                    path = os.path.join(normalized_dir, file)
                    abs_path = os.path.abspath(path)
                    # Use filename as key, avoid duplicates
                    if file not in csv_files:
                        csv_files[file] = abs_path
        except (OSError, FileNotFoundError):
            pass
    
    if not csv_files:
        raise FileNotFoundError(f"Could not find any CSV files in: {search_dirs}")
    
    return csv_files

def find_default_csv(csv_files):
    """Find the default CSV to load (prefer test_notes for comprehensive testing)."""
    if 'test_notes.csv' in csv_files:
        return 'test_notes.csv'
    if 'test_success_note.csv' in csv_files:
        return 'test_success_note.csv'
    if 'sample_model.csv' in csv_files:
        return 'sample_model.csv'
    # Fall back to first test CSV
    test_csvs = [f for f in csv_files if f.startswith('test_')]
    if test_csvs:
        return sorted(test_csvs)[0]
    # Last resort: first available
    return list(csv_files.keys())[0]

try:
    CSV_FILES = find_csv_files()
    print(f"[OK] Found {len(CSV_FILES)} CSV file(s): {sorted(CSV_FILES.keys())}")
except Exception as e:
    print(f"[ERROR] Failed to find CSV files: {e}")
    CSV_FILES = {}

DEFAULT_CSV = find_default_csv(CSV_FILES) if CSV_FILES else None

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
            # Serve the HTML viewer at the root, with support for diagram parameter
            try:
                params = parse_qs(parsed_path.query)
                # Handle 'diagram' parameter (e.g., diagram=tests/test_notes.csv)
                diagram_param = params.get('diagram', [''])[0]
                if diagram_param:
                    # Extract just the filename from path
                    csv_name = diagram_param.split('/')[-1] if '/' in diagram_param else diagram_param
                else:
                    csv_name = params.get('csv', [DEFAULT_CSV])[0]
                
                sequence_id = params.get('sequence', [''])[0]
                verbosity = params.get('verbosity', ['High'])[0]
                
                with open(HTML_PATH, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Inject initial parameters as JavaScript variables
                init_script = f'''
                <script>
                window.initialParams = {{
                    csv: "{csv_name}",
                    sequence: "{sequence_id}",
                    verbosity: "{verbosity}"
                }};
                </script>
                '''
                
                # Insert the script before the closing body tag
                html_content = html_content.replace('</body>', init_script + '</body>')
                
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
        elif parsed_path.path == '/render':
            # Serve the HTML viewer with pre-filled parameters from query string
            try:
                params = parse_qs(parsed_path.query)
                csv_name = params.get('csv', [DEFAULT_CSV])[0]
                sequence_id = params.get('sequence', [''])[0]
                verbosity = params.get('verbosity', ['High'])[0]
                
                with open(HTML_PATH, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Inject initial parameters as JavaScript variables
                init_script = f'''
                <script>
                window.initialParams = {{
                    csv: "{csv_name}",
                    sequence: "{sequence_id}",
                    verbosity: "{verbosity}"
                }};
                </script>
                '''
                
                # Insert the script before the closing body tag
                html_content = html_content.replace('</body>', init_script + '</body>')
                
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
        elif parsed_path.path == '/api/all_diagrams':
            self.handle_all_diagrams_request()
        elif parsed_path.path == '/api/csvs':
            self.handle_csvs_request()
        elif parsed_path.path == '/api/lanes':
            self.handle_lanes_request()
        elif parsed_path.path in ['/Scripts/diagram_viewer.html', '/diagram_viewer.html']:
            # Serve diagram viewer with parameter support
            try:
                params = parse_qs(parsed_path.query)
                # Handle 'diagram' parameter
                diagram_param = params.get('diagram', [''])[0]
                if diagram_param:
                    csv_name = diagram_param.split('/')[-1] if '/' in diagram_param else diagram_param
                else:
                    csv_name = params.get('csv', [DEFAULT_CSV])[0]
                
                sequence_id = params.get('sequence', [''])[0]
                verbosity = params.get('verbosity', ['High'])[0]
                
                with open(HTML_PATH, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Inject initial parameters as JavaScript variables
                init_script = f'''
                <script>
                window.initialParams = {{
                    csv: "{csv_name}",
                    sequence: "{sequence_id}",
                    verbosity: "{verbosity}"
                }};
                </script>
                '''
                
                # Insert the script before the closing body tag
                html_content = html_content.replace('</body>', init_script + '</body>')
                
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
        else:
            # Serve static files
            super().do_GET()
    
    def handle_diagram_request(self, query_string):
        """Generate and return an SVG diagram (sequence or class diagram)."""
        params = parse_qs(query_string)
        csv_name = params.get('csv', [DEFAULT_CSV])[0]
        diagram_type = params.get('type', ['sequence'])[0]
        sequence_id = params.get('sequence', [''])[0]
        diagram_id = params.get('diagram_id', [''])[0]
        verbosity = params.get('verbosity', ['High'])[0]
        lanes_str = params.get('lanes', [''])[0]
        
        try:
            model = load_model(csv_name)
            
            if diagram_type == 'class_diagram':
                if not diagram_id:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "diagram_id parameter is required for class diagrams"}).encode('utf-8'))
                    return
                
                class_diagram = model.get_class_diagram(diagram_id)
                if not class_diagram:
                    raise ValueError(f"Class diagram '{diagram_id}' not found")
                
                layers_filter = None
                if lanes_str:
                    layers_filter = lanes_str.split(',')
                
                svg = render_class_diagram_svg(model, class_diagram, verbosity_level=verbosity, layers_filter=layers_filter)
            else:
                # Default: sequence diagram
                if not sequence_id:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "sequence parameter is required"}).encode('utf-8'))
                    return
                
                sequence = model.get_sequence(sequence_id)
                if not sequence:
                    raise ValueError(f"Sequence {sequence_id} not found")
                
                lanes_filter = None
                if lanes_str:
                    lanes_filter = lanes_str.split(',')
                
                svg = render_svg(model, sequence, verbosity_level=verbosity, lanes_filter=lanes_filter)
            
            # Save SVG to disk for debugging
            try:
                output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Test', 'tests')
                os.makedirs(output_dir, exist_ok=True)
                csv_base = csv_name.replace('.csv', '')
                if diagram_type == 'class_diagram':
                    svg_filename = f"{csv_base}_{diagram_id}.svg"
                else:
                    svg_filename = f"{csv_base}_{sequence_id}_{verbosity}.svg"
                svg_path = os.path.join(output_dir, svg_filename)
                with open(svg_path, 'w', encoding='utf-8') as f:
                    f.write(svg)
                print(f"[SVG] Saved: {svg_path}")
            except Exception as e:
                print(f"[SVG] Failed to save: {str(e)}")
            
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
    
    def handle_all_diagrams_request(self):
        """Return all diagrams from all CSVs, aggregated by type."""
        try:
            diagrams = []
            for csv_name, csv_path in sorted(CSV_FILES.items()):
                try:
                    model = load_model(csv_name)
                    for s in model.sequences:
                        diagrams.append({
                            'type': 'sequence',
                            'id': s.seq_id,
                            'name': s.seq_id,
                            'csv': csv_name,
                            'lanes': s.get_lanes()
                        })
                    for d in model.class_diagrams:
                        diagrams.append({
                            'type': 'class_diagram',
                            'id': d.diagram_id,
                            'name': d.description or d.diagram_id,
                            'csv': csv_name,
                            'layers': d.get_layers(),
                            'routing': d.routing
                        })
                except Exception as e:
                    print(f"[all_diagrams] Error loading {csv_name}: {e}")
            
            print(f"[all_diagrams] Found {len(diagrams)} diagram(s) across {len(CSV_FILES)} CSV(s)")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps({'diagrams': diagrams}).encode('utf-8'))
        except Exception as e:
            print(f"[all_diagrams] Error: {str(e)}")
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def handle_csvs_request(self):
        """Return available CSV files."""
        try:
            if not CSV_FILES:
                print(f"[csvs] No CSV files found in CSV_FILES dict")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(json.dumps({"csvs": [], "warning": "No CSV files found"}).encode('utf-8'))
                return
            
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
        """Return available lanes, sequences, and class diagrams for a CSV."""
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
            
            # Get all class diagrams
            class_diagrams = [{'id': d.diagram_id, 'name': d.description or d.diagram_id, 'layers': d.get_layers(), 'routing': d.routing} for d in model.class_diagrams]
            
            print(f"[lanes] CSV '{csv_name}': {len(sequences)} sequence(s), {len(class_diagrams)} class diagram(s)")
            
            # Get lanes from the first sequence (if available)
            lanes = []
            if model.sequences:
                lanes = model.sequences[0].get_lanes()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps({
                "sequences": sequences,
                "class_diagrams": class_diagrams,
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
        if not model.sequences and not model.class_diagrams:
            raise ValueError(f"No sequences or class diagrams found in {DEFAULT_CSV}")
        
        print(f"[OK] Found {len(CSV_FILES)} CSV file(s)")
        print(f"[OK] Default CSV '{DEFAULT_CSV}' loaded: {len(model.classes)} classes, {len(model.sequences)} sequence(s), {len(model.class_diagrams)} class diagram(s)")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DiagramHandler)
    print(f"Server running at http://localhost:{port}")
    print(f"Open http://localhost:{port} in your browser")
    print("[OK] Server automatically reloads CSV on each request (no restart needed)")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
