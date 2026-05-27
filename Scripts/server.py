#!/usr/bin/env python3
"""Simple HTTP server for interactive diagram viewer."""

import json
import csv
import sys
import os
import tempfile
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from parser import parse_csv
from svg_renderer import render_svg
from class_diagram_renderer import render_class_diagram_svg

# Configuration - find CSV files and HTML flexibly
def find_csv_files_hierarchical():
    """Scan diagrams/ and Process/ folders for CSVs with hierarchy including numeric prefixes for proper sorting."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    csv_files_with_hierarchy = []
    
    # Scan diagrams/ folder
    diagrams_dir = os.path.join(script_dir, '../diagrams')
    diagrams_dir = os.path.normpath(diagrams_dir)
    if os.path.isdir(diagrams_dir):
        for root, dirs, files in os.walk(diagrams_dir):
            for file in files:
                if file.endswith('.csv'):
                    abs_path = os.path.abspath(os.path.join(root, file))
                    # Calculate relative path from diagrams/ folder
                    rel_path = os.path.relpath(root, diagrams_dir)
                    # Extract hierarchy from path, preserving numeric prefixes for sorting
                    path_parts = rel_path.split(os.sep)
                    hierarchy = []
                    for part in path_parts:
                        if part != '.':
                            # Keep folder name exactly as is (with numeric prefix for proper sorting)
                            hierarchy.append(part)
                    
                    csv_files_with_hierarchy.append({
                        'name': file,
                        'path': abs_path,
                        'hierarchy': hierarchy,
                        'relative_path': os.path.join(rel_path, file).replace(os.sep, '/'),
                        'csv_id': os.path.join('diagrams', rel_path, file).replace(os.sep, '/').replace('./', '')
                    })
    
    # Scan Process/ folder to capture System/Architecture/Design hierarchy
    process_dir = os.path.join(repo_root, 'Process')
    if os.path.isdir(process_dir):
        for root, dirs, files in os.walk(process_dir):
            for file in files:
                if file.endswith('.csv'):
                    abs_path = os.path.abspath(os.path.join(root, file))
                    # Calculate relative path from Process/ folder
                    rel_path = os.path.relpath(root, process_dir)
                    # Extract hierarchy from path, preserving numeric prefixes for sorting
                    path_parts = rel_path.split(os.sep)
                    hierarchy = []
                    for part in path_parts:
                        if part != '.' and part:
                            # Keep folder name exactly as is (with numeric prefix for proper sorting)
                            hierarchy.append(part)
                    
                    # Check if already exists in diagrams (avoid duplicates)
                    if not any(item['name'] == file and item['path'] == abs_path for item in csv_files_with_hierarchy):
                        csv_files_with_hierarchy.append({
                            'name': file,
                            'path': abs_path,
                            'hierarchy': hierarchy,
                            'relative_path': os.path.join(rel_path, file).replace(os.sep, '/'),
                            'csv_id': os.path.join('Process', rel_path, file).replace(os.sep, '/').replace('./', '')
                        })
    
    # Scan Test/tests/ folder for test diagrams
    test_dir = os.path.join(repo_root, 'Test', 'tests')
    if os.path.isdir(test_dir):
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.csv'):
                    abs_path = os.path.abspath(os.path.join(root, file))
                    # Calculate relative path from Test/ folder
                    rel_path = os.path.relpath(root, test_dir)
                    hierarchy = ['Test'] if rel_path == '.' else ['Test', rel_path]
                    
                    # Check if already exists (avoid duplicates)
                    if not any(item['name'] == file and item['path'] == abs_path for item in csv_files_with_hierarchy):
                        csv_files_with_hierarchy.append({
                            'name': file,
                            'path': abs_path,
                            'hierarchy': hierarchy,
                            'relative_path': os.path.join(rel_path, file).replace(os.sep, '/'),
                            'csv_id': os.path.join('Test', 'tests', rel_path, file).replace(os.sep, '/').replace('./', '')
                        })
    
    return csv_files_with_hierarchy

def find_csv_files():
    """Search for all CSV files and return a unique-key map."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)  # Parent of Scripts/
    
    csv_files = {}

    # Add CSV files from hierarchical folders with stable relative IDs
    hierarchical = find_csv_files_hierarchical()
    for item in hierarchical:
        csv_files[item['csv_id']] = item['path']

    # Include additional top-level folders not covered by hierarchical scan.
    extra_dirs = [
        os.path.join(repo_root, 'Source'),
        os.path.join(repo_root, 'Test'),
        os.path.join(repo_root, 'tests'),
        script_dir,
    ]
    found_dirs = []
    for search_dir in extra_dirs:
        search_dir = os.path.normpath(search_dir)
        if not os.path.isdir(search_dir):
            continue
        found_dirs.append(search_dir)
        try:
            for file in os.listdir(search_dir):
                if not file.endswith('.csv'):
                    continue
                path = os.path.join(search_dir, file)
                abs_path = os.path.abspath(path)
                rel_key = os.path.relpath(abs_path, repo_root).replace(os.sep, '/')
                csv_files[rel_key] = abs_path
        except (OSError, FileNotFoundError) as e:
            print(f"[warn] Error listing {search_dir}: {e}")

    # Remove mirrored legacy architecture CSVs when canonical nested copies exist.
    process_arch_root = 'Process/02_Architecture/'
    shallow_arch_keys = [
        key for key in csv_files
        if key.startswith(process_arch_root) and key.count('/') == 2
    ]
    deep_arch_basenames = {
        os.path.basename(key)
        for key in csv_files
        if key.startswith(process_arch_root) and key.count('/') > 2
    }
    pruned_count = 0
    for key in shallow_arch_keys:
        if os.path.basename(key) in deep_arch_basenames:
            del csv_files[key]
            pruned_count += 1
    if pruned_count:
        print(f"[OK] Pruned {pruned_count} mirrored Process/02_Architecture CSV(s)")
    
    if not csv_files:
        raise FileNotFoundError(f"Could not find any CSV files in: {found_dirs}")
    
    print(f"[OK] Found {len(csv_files)} CSV file(s) in {len(found_dirs)} directories")
    return csv_files

def find_default_csv(csv_files):
    """Find the default CSV to load.

    Prefer familiar samples, but only if they parse into at least one
    renderable sequence or class diagram. This avoids startup failures when a
    CSV contains only supporting rows such as classes or orphan sequence steps.
    """

    def _is_renderable(csv_key):
        try:
            model = parse_csv(csv_files[csv_key])
        except Exception as exc:
            print(f"[warn] Skipping default candidate '{csv_key}': {exc}")
            return False
        return bool(model.sequences or model.class_diagrams)

    preferred_keys = []
    for suffix in ('/system_main.csv', '/test_notes.csv', '/test_success_note.csv', '/sample_model.csv'):
        preferred_keys.extend(key for key in sorted(csv_files) if key.endswith(suffix))

    for key in preferred_keys:
        if _is_renderable(key):
            return key

    test_csvs = [key for key in sorted(csv_files) if os.path.basename(key).startswith('test_')]
    for key in test_csvs:
        if _is_renderable(key):
            return key

    for key in sorted(csv_files):
        if _is_renderable(key):
            return key

    return list(csv_files.keys())[0]


def resolve_csv_key(csv_name):
    """Resolve a CSV key from path-like or legacy filename input."""
    if not csv_name:
        return DEFAULT_CSV

    normalized = str(csv_name).replace('\\', '/').strip()
    if normalized in CSV_FILES:
        return normalized

    basename = os.path.basename(normalized)
    matches = [key for key in CSV_FILES if os.path.basename(key) == basename]
    if len(matches) == 1:
        return matches[0]

    return None


def resolve_csv_registry_key(csv_id):
    """Resolve a CSV id strictly from the known registry keys."""
    if not csv_id:
        return None

    normalized = str(csv_id).replace('\\', '/').strip()
    if not normalized or normalized.startswith('/'):
        return None
    if '..' in normalized:
        return None

    if normalized in CSV_FILES:
        return normalized
    return None


def find_include_target_csv_keys():
    """Return CSV registry keys that are referenced by top-level Include rows."""
    include_targets = set()
    if not CSV_FILES:
        return include_targets

    abs_to_key = {os.path.abspath(path): key for key, path in CSV_FILES.items()}

    for source_key, source_path in CSV_FILES.items():
        try:
            with open(source_path, newline="", encoding="utf-8-sig") as handle:
                reader = csv.reader(handle, delimiter=';')
                first_row = next(reader, None)

                def _rows():
                    if first_row is not None:
                        first_type = clean(first_row[0]) if len(first_row) > 0 else ""
                        first_name = clean(first_row[1]) if len(first_row) > 1 else ""
                        has_header = first_type == "Type" and first_name == "Name"
                        if not has_header:
                            yield first_row
                    for row in reader:
                        yield row

                for row in _rows():
                    if not row or not clean(row[0]):
                        continue
                    level, type_name = parse_indent(row[0])
                    if level != 0 or type_name != "Include":
                        continue

                    include_ref = clean(row[1]) if len(row) > 1 else ""
                    if not include_ref:
                        continue

                    include_path = os.path.normpath(
                        os.path.join(os.path.dirname(os.path.abspath(source_path)), include_ref)
                    )
                    target_key = abs_to_key.get(os.path.abspath(include_path))
                    if target_key:
                        include_targets.add(target_key)
        except Exception:
            # Best-effort metadata only; ignore malformed files here.
            continue

    return include_targets


def read_csv_text(csv_id):
    """Read CSV source text from a known CSV id."""
    registry_key = resolve_csv_registry_key(csv_id)
    if not registry_key:
        raise ValueError("Unknown csv id")

    csv_path = CSV_FILES[registry_key]
    with open(csv_path, 'r', encoding='utf-8') as handle:
        return handle.read()


def write_csv_text(csv_id, content):
    """Validate and atomically write CSV source text for a known CSV id."""
    registry_key = resolve_csv_registry_key(csv_id)
    if not registry_key:
        raise ValueError("Unknown csv id")

    csv_path = CSV_FILES[registry_key]
    csv_dir = os.path.dirname(csv_path)
    fd, temp_path = tempfile.mkstemp(prefix='csv_edit_', suffix='.tmp', dir=csv_dir, text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(content)

        # Validate by parsing the staged content before replacing the real file.
        parse_csv(temp_path)
        os.replace(temp_path, csv_path)
    except Exception:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        raise

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

    resolved_csv = resolve_csv_key(csv_name)
    if not resolved_csv:
        raise ValueError(f"CSV not found: {csv_name}")

    return parse_csv(CSV_FILES[resolved_csv])

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
                    csv_name = diagram_param.replace('\\', '/')
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
            self.handle_all_diagrams_request(parsed_path.query)
        elif parsed_path.path == '/api/csvs':
            self.handle_csvs_request()
        elif parsed_path.path == '/api/csv_text':
            self.handle_csv_text_read_request(parsed_path.query)
        elif parsed_path.path == '/api/lanes':
            self.handle_lanes_request()
        elif parsed_path.path == '/api/class_metadata':
            self.handle_class_metadata_request()
        elif parsed_path.path in ['/Scripts/diagram_viewer.html', '/diagram_viewer.html']:
            # Serve diagram viewer with parameter support
            try:
                params = parse_qs(parsed_path.query)
                # Handle 'diagram' parameter
                diagram_param = params.get('diagram', [''])[0]
                if diagram_param:
                    csv_name = diagram_param.replace('\\', '/')
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

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/csv_text':
            self.handle_csv_text_write_request()
            return

        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': False, 'error': 'Not found'}).encode('utf-8'))
    
    def handle_diagram_request(self, query_string):
        """Generate and return an SVG diagram (sequence or class diagram)."""
        params = parse_qs(query_string, keep_blank_values=True)
        csv_name = params.get('csv', [DEFAULT_CSV])[0]
        diagram_type = params.get('type', ['sequence'])[0]
        sequence_id = params.get('sequence', [''])[0]
        diagram_id = params.get('diagram_id', [''])[0]
        verbosity = params.get('verbosity', ['High'])[0]
        routing = params.get('routing', [''])[0]  # Override diagram routing if specified
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

                if routing:
                    routing_value = routing.strip().lower()
                    if routing_value == 'orthogonal':
                        class_diagram.routing = routing_value
                
                # Handle layers filter: if 'lanes' parameter is present (even if empty),
                # treat it as an explicit filter. If absent, show all.
                layers_filter = None
                if 'lanes' in params:  # Parameter was explicitly provided
                    lanes_str = params.get('lanes', [''])[0]
                    if lanes_str:  # Non-empty: filter to specific layers
                        layers_filter = lanes_str.split(',')
                    else:  # Empty: show no layers (empty diagram)
                        layers_filter = []
                
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
                # Handle lanes filter: if 'lanes' parameter is present (even if empty),
                # treat it as an explicit filter. If absent, show all.
                if 'lanes' in params:  # Parameter was explicitly provided
                    if lanes_str:  # Non-empty: filter to specific lanes
                        lanes_filter = lanes_str.split(',')
                    else:  # Empty: show no lanes (empty diagram)
                        lanes_filter = []
                
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
    
    def handle_all_diagrams_request(self, query_string=''):
        """Return all diagrams from all CSVs with hierarchy information."""
        try:
            params = parse_qs(query_string, keep_blank_values=True)
            include_test = params.get('include_test', ['0'])[0] == '1'

            # Get hierarchical CSV information
            hierarchical_csvs = find_csv_files_hierarchical()
            hierarchy_lookup = {item['csv_id']: item['hierarchy'] for item in hierarchical_csvs}

            def is_test_csv_key(csv_key):
                hierarchy = hierarchy_lookup.get(csv_key, [])
                normalized = str(csv_key).replace('\\', '/').lower()
                return (
                    (hierarchy and hierarchy[0] == 'Test') or
                    normalized.startswith('test/tests/') or
                    '/40_tests/' in normalized
                )

            # If multiple test CSV copies exist for the same filename, keep only
            # one source to avoid duplicate test diagrams in the palette.
            test_groups = {}
            for key in CSV_FILES.keys():
                if is_test_csv_key(key):
                    test_groups.setdefault(os.path.basename(key).lower(), []).append(key)

            suppressed_test_csvs = set()
            for basename, keys in test_groups.items():
                if len(keys) <= 1:
                    continue
                preferred = next((k for k in keys if str(k).replace('\\', '/').lower().startswith('test/tests/')), None)
                if preferred is None:
                    preferred = sorted(keys, key=lambda k: (len(k), k))[0]
                for key in keys:
                    if key != preferred:
                        suppressed_test_csvs.add(key)
            
            diagrams = []
            seen_keys = set()
            skipped_non_renderable = 0

            def append_if_visible(entry):
                """Apply list hygiene rules for the viewer payload."""
                if not entry.get('id') or not entry.get('csv'):
                    return

                hierarchy = entry.get('hierarchy') or []
                csv_key = str(entry.get('csv') or '').replace('\\', '/').lower()
                is_test_entry = (
                    (hierarchy and hierarchy[0] == 'Test') or
                    csv_key.startswith('test/tests/') or
                    '/40_tests/' in csv_key
                )
                if not include_test and is_test_entry:
                    return

                entry_type = str(entry.get('type') or '')
                entry_id = str(entry.get('id') or '')
                entry_name = str(entry.get('name') or '')

                # Semantic dedupe across mirrored CSV sources.
                # Prefer first entry encountered in sorted CSV key order.
                if entry_type == 'sequence':
                    key = (entry_type, entry_id)
                else:
                    key = (entry_type, entry_id, entry_name)
                if key in seen_keys:
                    return

                seen_keys.add(key)
                diagrams.append(entry)

            for csv_name in sorted(CSV_FILES.keys()):
                if csv_name in suppressed_test_csvs:
                    continue
                try:
                    model = load_model(csv_name)
                    # Get hierarchy for this CSV if it exists
                    hierarchy = hierarchy_lookup.get(csv_name, [])
                    
                    for s in model.sequences:
                        sequence_lanes = s.get_lanes()
                        # Hide non-renderable sequence entries (e.g., malformed test
                        # fixtures with no lanes/steps), which otherwise show up as
                        # selectable items that fail at render time.
                        if not sequence_lanes:
                            skipped_non_renderable += 1
                            continue
                        append_if_visible({
                            'type': 'sequence',
                            'id': s.seq_id,
                            'name': s.seq_id,
                            'csv': csv_name,
                            'lanes': sequence_lanes,
                            'symbols': sequence_lanes,
                            'hierarchy': hierarchy,
                            'parent_diagram': s.parent_diagram,
                            'child_diagrams': s.child_diagrams
                        })
                    for d in model.class_diagrams:
                        append_if_visible({
                            'type': 'class_diagram',
                            'id': d.diagram_id,
                            'name': d.description or d.diagram_id,
                            'csv': csv_name,
                            'layers': d.get_layers(),
                            'symbols': d.get_element_names(),
                            'routing': d.routing,
                            'hierarchy': hierarchy,
                            'parent_diagram': d.parent_diagram,
                            'child_diagrams': d.child_diagrams
                        })
                except Exception as e:
                    print(f"[all_diagrams] Error loading {csv_name}: {e}")
            
            print(f"[all_diagrams] Found {len(diagrams)} diagram(s) across {len(CSV_FILES)} CSV(s)")
            if suppressed_test_csvs:
                print(f"[all_diagrams] Suppressed {len(suppressed_test_csvs)} duplicate test CSV source(s)")
            if skipped_non_renderable:
                print(f"[all_diagrams] Skipped {skipped_non_renderable} non-renderable sequence diagram(s)")
            
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

            hierarchical_csvs = find_csv_files_hierarchical()
            hierarchy_lookup = {item['csv_id']: item['hierarchy'] for item in hierarchical_csvs}
            include_target_keys = find_include_target_csv_keys()
            
            csvs = []
            for csv_name in sorted(CSV_FILES.keys()):
                # Create a friendly name (remove .csv, replace underscores)
                friendly_name = csv_name.replace('.csv', '').replace('_', ' ').title()
                csvs.append({
                    'id': csv_name,
                    'name': friendly_name,
                    'hierarchy': hierarchy_lookup.get(csv_name, []),
                    'is_include_target': csv_name in include_target_keys
                })
            
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
        params = parse_qs(parsed.query, keep_blank_values=True)
        csv_name = params.get('csv', [DEFAULT_CSV])[0]
        
        try:
            # Load model from specified CSV
            model = load_model(csv_name)
            
            # Get all sequences
            sequences = [{'id': s.seq_id, 'name': s.seq_id} for s in model.sequences]
            
            # Get all class diagrams
            class_diagrams = [{'id': d.diagram_id, 'name': d.diagram_id, 'layers': d.get_layers(), 'routing': d.routing} for d in model.class_diagrams]
            
            print(f"[lanes] CSV '{csv_name}': {len(sequences)} sequence(s), {len(class_diagrams)} class diagram(s)")
            
            # Get lanes from the first sequence (if available)
            lanes = []
            if model.sequences:
                lanes = model.sequences[0].get_lanes()
            
            # Get all layers from classes
            layers = model.get_layers()
            
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
                "layers": layers,
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

    def handle_csv_text_read_request(self, query_string):
        """Return raw CSV text for a known CSV id."""
        params = parse_qs(query_string, keep_blank_values=True)
        csv_id = params.get('csv', [''])[0]

        if not resolve_csv_registry_key(csv_id):
            self.send_response(400)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(b'Unknown csv id')
            return

        try:
            text = read_csv_text(csv_id)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(text.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            self.wfile.write(f'Read failure: {str(e)}'.encode('utf-8'))

    def handle_csv_text_write_request(self):
        """Validate and persist CSV text for a known CSV id."""
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            content_length = 0

        if content_length <= 0:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': 'Request body is required'}).encode('utf-8'))
            return

        try:
            raw = self.rfile.read(content_length)
            payload = json.loads(raw.decode('utf-8'))
        except Exception:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': 'Invalid JSON payload'}).encode('utf-8'))
            return

        csv_id = payload.get('csv')
        content = payload.get('content')

        if not isinstance(csv_id, str) or not resolve_csv_registry_key(csv_id):
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': 'Unknown csv id'}).encode('utf-8'))
            return

        if not isinstance(content, str):
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': 'content must be a string'}).encode('utf-8'))
            return

        try:
            write_csv_text(csv_id, content)
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': str(e)}).encode('utf-8'))
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
    
    def handle_class_metadata_request(self):
        """Return class metadata from the model for a specific class diagram."""
        try:
            # Parse query parameters
            query_string = urlparse(self.path).query
            params = parse_qs(query_string, keep_blank_values=True)
            csv_name = params.get('csv', [DEFAULT_CSV])[0]
            diagram_id = params.get('diagram_id', [''])[0]
            
            # Load the model for the specified CSV
            model = load_model(csv_name)

            # Build traceability indexes once per request.
            script_dir_local = os.path.dirname(os.path.abspath(__file__))
            repo_root_local = os.path.dirname(script_dir_local)
            req_index = {}
            req_rows = []
            trace_rows = []

            req_path = os.path.join(repo_root_local, 'Source', 'requirements.csv')
            if os.path.isfile(req_path):
                try:
                    with open(req_path, 'r', encoding='utf-8-sig', newline='') as req_file:
                        reader = csv.reader(req_file, delimiter=';')
                        next(reader, None)
                        for row in reader:
                            if not row:
                                continue
                            entry = {
                                'id': row[0].strip() if len(row) > 0 else '',
                                'level': row[1].strip() if len(row) > 1 else '',
                                'type': row[2].strip() if len(row) > 2 else '',
                                'title': row[3].strip() if len(row) > 3 else '',
                                'linked_from': row[4].strip() if len(row) > 4 else '',
                                'linked_to': row[5].strip() if len(row) > 5 else '',
                                'status': row[6].strip() if len(row) > 6 else '',
                                'source': 'Source/requirements.csv'
                            }
                            req_rows.append(entry)
                            if entry['id']:
                                req_index[entry['id']] = entry
                except Exception as req_err:
                    print(f"[class_metadata] requirements traceability parse error: {req_err}")

            trace_path = os.path.join(repo_root_local, 'Process', 'traceability.csv')
            if os.path.isfile(trace_path):
                try:
                    with open(trace_path, 'r', encoding='utf-8-sig', newline='') as trace_file:
                        reader = csv.DictReader(trace_file, delimiter=';')
                        for row in reader:
                            trace_rows.append({
                                'requirement_id': str(row.get('Customer_Req_ID', '')).strip(),
                                'user_story_id': str(row.get('User_Story_ID', '')).strip(),
                                'feature_id': str(row.get('Feature_ID', '')).strip(),
                                'test_case_id': str(row.get('Test_Case_ID', '')).strip(),
                                'title': str(row.get('Description', '')).strip(),
                                'source': 'Process/traceability.csv'
                            })
                except Exception as trace_err:
                    print(f"[class_metadata] process traceability parse error: {trace_err}")

            def _collect_class_traceability(class_name, class_def):
                """Collect traceability links for a class.

                Priority:
                  1) explicit IDs declared in the class DSL row (strict matching)
                  2) legacy inferred matching by class name when no explicit IDs exist
                """
                normalized = str(class_name or '').strip().lower()
                traceability = {
                    'requirements': [],
                    'user_stories': [],
                    'test_cases': [],
                    'features': []
                }

                def _add_unique(bucket, item):
                    existing_keys = {(entry.get('id'), entry.get('source')) for entry in bucket}
                    key = (item.get('id'), item.get('source'))
                    if key not in existing_keys:
                        bucket.append(item)

                explicit_req_ids = list(getattr(class_def, 'trace_requirement_ids', []) or [])
                explicit_story_ids = list(getattr(class_def, 'trace_user_story_ids', []) or [])
                explicit_test_ids = list(getattr(class_def, 'trace_test_case_ids', []) or [])
                explicit_feature_ids = list(getattr(class_def, 'trace_feature_ids', []) or [])
                has_explicit = bool(explicit_req_ids or explicit_story_ids or explicit_test_ids or explicit_feature_ids)

                if has_explicit:
                    # Requirements: prefer direct Source/requirements.csv match.
                    for req_id in explicit_req_ids:
                        if req_id in req_index:
                            req_entry = req_index[req_id]
                            _add_unique(traceability['requirements'], {
                                'id': req_entry['id'],
                                'title': req_entry['title'],
                                'type': req_entry['type'],
                                'level': req_entry['level'],
                                'status': req_entry['status'],
                                'source': req_entry['source']
                            })
                        else:
                            _add_unique(traceability['requirements'], {
                                'id': req_id,
                                'title': 'Explicit requirement ID (unresolved)',
                                'source': 'explicit'
                            })

                    # Process traceability table exact-ID lookups.
                    for row in trace_rows:
                        if row['requirement_id'] in explicit_req_ids and row['requirement_id'] and row['requirement_id'] != 'N/A':
                            _add_unique(traceability['requirements'], {
                                'id': row['requirement_id'],
                                'title': row['title'],
                                'type': 'Customer Requirement',
                                'source': row['source']
                            })
                        if row['user_story_id'] in explicit_story_ids and row['user_story_id'] and row['user_story_id'] != 'N/A':
                            _add_unique(traceability['user_stories'], {
                                'id': row['user_story_id'],
                                'title': row['title'],
                                'source': row['source']
                            })
                        if row['test_case_id'] in explicit_test_ids and row['test_case_id'] and row['test_case_id'] != 'N/A':
                            _add_unique(traceability['test_cases'], {
                                'id': row['test_case_id'],
                                'title': row['title'],
                                'source': row['source']
                            })
                        if row['feature_id'] in explicit_feature_ids and row['feature_id'] and row['feature_id'] != 'N/A':
                            _add_unique(traceability['features'], {
                                'id': row['feature_id'],
                                'title': row['title'],
                                'source': row['source']
                            })

                    # Preserve unresolved explicit IDs so users can spot typos/missing rows.
                    resolved_story_ids = {entry.get('id') for entry in traceability['user_stories']}
                    for story_id in explicit_story_ids:
                        if story_id not in resolved_story_ids:
                            _add_unique(traceability['user_stories'], {
                                'id': story_id,
                                'title': 'Explicit user story ID (unresolved)',
                                'source': 'explicit'
                            })

                    resolved_test_ids = {entry.get('id') for entry in traceability['test_cases']}
                    for test_id in explicit_test_ids:
                        if test_id not in resolved_test_ids:
                            _add_unique(traceability['test_cases'], {
                                'id': test_id,
                                'title': 'Explicit test case ID (unresolved)',
                                'source': 'explicit'
                            })

                    resolved_feature_ids = {entry.get('id') for entry in traceability['features']}
                    for feature_id in explicit_feature_ids:
                        if feature_id not in resolved_feature_ids:
                            _add_unique(traceability['features'], {
                                'id': feature_id,
                                'title': 'Explicit feature ID (unresolved)',
                                'source': 'explicit'
                            })

                    return traceability

                # Legacy fallback: inferred matching by class name.
                for req_entry in req_rows:
                    searchable = ' '.join([
                        req_entry.get('id', ''),
                        req_entry.get('title', ''),
                        req_entry.get('linked_from', ''),
                        req_entry.get('linked_to', '')
                    ]).lower()
                    if normalized and normalized in searchable:
                        _add_unique(traceability['requirements'], {
                            'id': req_entry.get('id', ''),
                            'title': req_entry.get('title', ''),
                            'type': req_entry.get('type', ''),
                            'level': req_entry.get('level', ''),
                            'status': req_entry.get('status', ''),
                            'source': req_entry.get('source', 'Source/requirements.csv')
                        })

                for row in trace_rows:
                    searchable = ' '.join([
                        row.get('title', ''),
                        row.get('feature_id', ''),
                        row.get('test_case_id', ''),
                        row.get('user_story_id', ''),
                        row.get('requirement_id', '')
                    ]).lower()
                    if normalized and normalized not in searchable:
                        continue

                    if row['requirement_id'] and row['requirement_id'] != 'N/A':
                        _add_unique(traceability['requirements'], {
                            'id': row['requirement_id'],
                            'title': row['title'],
                            'type': 'Customer Requirement',
                            'source': row['source']
                        })
                    if row['user_story_id'] and row['user_story_id'] != 'N/A':
                        _add_unique(traceability['user_stories'], {
                            'id': row['user_story_id'],
                            'title': row['title'],
                            'source': row['source']
                        })
                    if row['feature_id'] and row['feature_id'] != 'N/A':
                        _add_unique(traceability['features'], {
                            'id': row['feature_id'],
                            'title': row['title'],
                            'source': row['source']
                        })
                    if row['test_case_id'] and row['test_case_id'] != 'N/A':
                        _add_unique(traceability['test_cases'], {
                            'id': row['test_case_id'],
                            'title': row['title'],
                            'source': row['source']
                        })

                return traceability
            
            # Get the class diagram
            if not diagram_id:
                metadata = {}
            else:
                class_diagram = model.get_class_diagram(diagram_id)
                if not class_diagram:
                    metadata = {}
                else:
                    # Get all element names in this diagram
                    element_names = class_diagram.get_element_names()
                    
                    # Build metadata for each element
                    metadata = {}
                    for element_name in element_names:
                        class_def = model.get_class(element_name)
                        if class_def:
                            # Extract metadata from the class definition
                            responsibilities = []
                            # Parse responsibilities from the description if available
                            if class_def.description:
                                # Split description by common markers for responsibilities
                                lines = class_def.description.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line and not line.startswith('- '):
                                        responsibilities.append(line)
                            
                            # Extract attributes from members
                            attributes = []
                            for member in class_def.members:
                                attr_str = member.name
                                if member.description:
                                    attr_str += f" ({member.description})"
                                attributes.append(attr_str)
                            
                            # Extract methods from functions
                            methods = []
                            for func in class_def.functions:
                                # Format: visibility name(params) : returntype
                                method_str = func.name
                                if func.description:
                                    method_str += f" - {func.description}"
                                methods.append(method_str)
                            
                            # Extract notes (not used in this version)
                            notes = []
                            if class_def.state_machines:
                                notes.append(f"{len(class_def.state_machines)} state machine(s)")

                            traceability = _collect_class_traceability(element_name, class_def)
                            
                            metadata[element_name] = {
                                'description': class_def.description or '',
                                'responsibilities': responsibilities,
                                'attributes': attributes,
                                'methods': methods,
                                'notes': notes,
                                'traceability': traceability
                            }
            
            if not metadata:
                print(f"[class_metadata] No metadata for diagram {diagram_id}")
            else:
                print(f"[class_metadata] Loaded metadata for {len(metadata)} classes in diagram {diagram_id}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps({'metadata': metadata}).encode('utf-8'))
        except Exception as e:
            print(f"[class_metadata] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    

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
