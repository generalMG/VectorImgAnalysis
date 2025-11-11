import sys
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import xml.etree.ElementTree as ET
from svg.path import parse_path
from svg.path.path import Line, CubicBezier, QuadraticBezier, Arc, Move, Close
import json

def parse_svg(svg_path):
    """Parse SVG file and extract vector data"""
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Handle SVG namespace
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    # Try to get namespace from root
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'
        namespaces['svg'] = ns[1:-1]

    results = {
        'file': svg_path.name,
        'viewBox': root.get('viewBox', 'not specified'),
        'width': root.get('width', 'not specified'),
        'height': root.get('height', 'not specified'),
        'paths': [],
        'lines': [],
        'curves': [],
        'shapes': [],
        'total_elements': 0
    }

    return results, root, namespaces

def extract_path_elements(root, namespaces):
    """Extract all <path> elements from SVG"""
    paths = []

    # Find all path elements (with and without namespace)
    for path_elem in root.iter():
        if path_elem.tag.endswith('path') or path_elem.tag == 'path':
            d = path_elem.get('d')
            if d:
                try:
                    parsed_path = parse_path(d)
                    path_data = {
                        'type': 'path',
                        'd': d,
                        'fill': path_elem.get('fill', 'none'),
                        'stroke': path_elem.get('stroke', 'none'),
                        'stroke_width': path_elem.get('stroke-width', '1'),
                        'segments': []
                    }

                    # Parse each segment
                    for segment in parsed_path:
                        segment_data = parse_segment(segment)
                        path_data['segments'].append(segment_data)

                    paths.append(path_data)
                except Exception as e:
                    print(f"Warning: Could not parse path: {e}")

    return paths

def parse_segment(segment):
    """Parse individual path segment"""
    segment_data = {
        'type': type(segment).__name__,
        'data': {}
    }

    if isinstance(segment, Line):
        segment_data['operation'] = 'l'
        segment_data['data'] = {
            'start': (segment.start.real, segment.start.imag),
            'end': (segment.end.real, segment.end.imag),
            'length': abs(segment.end - segment.start)
        }

    elif isinstance(segment, CubicBezier):
        segment_data['operation'] = 'c'
        segment_data['data'] = {
            'start': (segment.start.real, segment.start.imag),
            'control1': (segment.control1.real, segment.control1.imag),
            'control2': (segment.control2.real, segment.control2.imag),
            'end': (segment.end.real, segment.end.imag)
        }

    elif isinstance(segment, QuadraticBezier):
        segment_data['operation'] = 'q'
        segment_data['data'] = {
            'start': (segment.start.real, segment.start.imag),
            'control': (segment.control.real, segment.control.imag),
            'end': (segment.end.real, segment.end.imag)
        }

    elif isinstance(segment, Arc):
        segment_data['operation'] = 'a'
        segment_data['data'] = {
            'start': (segment.start.real, segment.start.imag),
            'radius': (segment.radius.real, segment.radius.imag),
            'rotation': segment.rotation,
            'arc': segment.arc,
            'sweep': segment.sweep,
            'end': (segment.end.real, segment.end.imag)
        }

    elif isinstance(segment, Move):
        segment_data['operation'] = 'm'
        segment_data['data'] = {
            'start': (segment.start.real, segment.start.imag),
            'end': (segment.end.real, segment.end.imag)
        }

    elif isinstance(segment, Close):
        segment_data['operation'] = 'z'
        segment_data['data'] = {
            'start': (segment.start.real, segment.start.imag),
            'end': (segment.end.real, segment.end.imag)
        }

    return segment_data

def extract_shape_elements(root):
    """Extract basic shapes (rect, circle, ellipse, line, polyline, polygon)"""
    shapes = []

    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag == 'rect':
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            width = float(elem.get('width', 0))
            height = float(elem.get('height', 0))

            shapes.append({
                'type': 'rectangle',
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'corners': [
                    (x, y),
                    (x + width, y),
                    (x + width, y + height),
                    (x, y + height)
                ],
                'fill': elem.get('fill', 'none'),
                'stroke': elem.get('stroke', 'none')
            })

        elif tag == 'circle':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))

            shapes.append({
                'type': 'circle',
                'center': (cx, cy),
                'radius': r,
                'fill': elem.get('fill', 'none'),
                'stroke': elem.get('stroke', 'none')
            })

        elif tag == 'ellipse':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            rx = float(elem.get('rx', 0))
            ry = float(elem.get('ry', 0))

            shapes.append({
                'type': 'ellipse',
                'center': (cx, cy),
                'radius_x': rx,
                'radius_y': ry,
                'fill': elem.get('fill', 'none'),
                'stroke': elem.get('stroke', 'none')
            })

        elif tag == 'line':
            x1 = float(elem.get('x1', 0))
            y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0))
            y2 = float(elem.get('y2', 0))

            shapes.append({
                'type': 'line',
                'start': (x1, y1),
                'end': (x2, y2),
                'length': np.sqrt((x2-x1)**2 + (y2-y1)**2),
                'stroke': elem.get('stroke', 'none')
            })

        elif tag == 'polyline' or tag == 'polygon':
            points_str = elem.get('points', '')
            points = []
            if points_str:
                coords = points_str.replace(',', ' ').split()
                for i in range(0, len(coords)-1, 2):
                    points.append((float(coords[i]), float(coords[i+1])))

            shapes.append({
                'type': tag,
                'points': points,
                'num_points': len(points),
                'closed': tag == 'polygon',
                'fill': elem.get('fill', 'none'),
                'stroke': elem.get('stroke', 'none')
            })

    return shapes

def categorize_vectors(paths, shapes):
    """Categorize extracted vectors into lines and curves"""
    lines = []
    curves = []

    # From path segments
    for path in paths:
        for segment in path['segments']:
            if segment['operation'] == 'l':
                lines.append({
                    'type': 'line',
                    'start': segment['data']['start'],
                    'end': segment['data']['end'],
                    'length': segment['data']['length'],
                    'source': 'path'
                })
            elif segment['operation'] in ['c', 'q', 'a']:
                curves.append({
                    'type': segment['type'],
                    'operation': segment['operation'],
                    'data': segment['data'],
                    'source': 'path'
                })

    # From shapes
    for shape in shapes:
        if shape['type'] == 'line':
            lines.append({
                'type': 'line',
                'start': shape['start'],
                'end': shape['end'],
                'length': shape['length'],
                'source': 'shape'
            })
        elif shape['type'] == 'rectangle':
            # Rectangle as 4 lines
            corners = shape['corners']
            for i in range(4):
                start = corners[i]
                end = corners[(i + 1) % 4]
                lines.append({
                    'type': 'line',
                    'start': start,
                    'end': end,
                    'length': np.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2),
                    'source': 'rectangle'
                })
        elif shape['type'] in ['circle', 'ellipse']:
            curves.append({
                'type': shape['type'],
                'data': shape,
                'source': 'shape'
            })
        elif shape['type'] in ['polyline', 'polygon']:
            # Polyline/polygon as connected lines
            points = shape['points']
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]
                lines.append({
                    'type': 'line',
                    'start': start,
                    'end': end,
                    'length': np.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2),
                    'source': shape['type']
                })
            # Close polygon
            if shape['closed'] and len(points) > 2:
                start = points[-1]
                end = points[0]
                lines.append({
                    'type': 'line',
                    'start': start,
                    'end': end,
                    'length': np.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2),
                    'source': shape['type']
                })

    return lines, curves

def print_analysis(results, paths, shapes, lines, curves):
    """Print analysis of SVG file"""
    print(f"\n{'='*60}")
    print(f"File: {results['file']}")
    print(f"{'='*60}")
    print(f"ViewBox:            {results['viewBox']}")
    print(f"Width:              {results['width']}")
    print(f"Height:             {results['height']}")
    print(f"\n{'='*60}")
    print(f"EXTRACTED ELEMENTS")
    print(f"{'='*60}")
    print(f"Path elements:      {len(paths)}")
    print(f"Shape elements:     {len(shapes)}")
    print(f"Total lines:        {len(lines)}")
    print(f"Total curves:       {len(curves)}")

    # Shape breakdown
    if shapes:
        shape_types = {}
        for shape in shapes:
            shape_types[shape['type']] = shape_types.get(shape['type'], 0) + 1
        print(f"\nShape breakdown:")
        for shape_type, count in sorted(shape_types.items()):
            print(f"  {shape_type}: {count}")

def print_detailed_vectors(paths, shapes, lines, curves, max_display=5):
    """Print detailed vector information"""
    print(f"\n{'='*60}")
    print(f"DETAILED VECTOR INFORMATION")
    print(f"{'='*60}")

    # Print path details
    if paths:
        print(f"\n--- PATHS (showing {min(len(paths), max_display)} of {len(paths)}) ---")
        for i, path in enumerate(paths[:max_display]):
            print(f"\nPath {i}:")
            print(f"  Fill: {path['fill']}")
            print(f"  Stroke: {path['stroke']}")
            print(f"  Stroke width: {path['stroke_width']}")
            print(f"  Segments: {len(path['segments'])}")

            for j, segment in enumerate(path['segments'][:3]):
                print(f"\n  Segment {j} (operation: {segment['operation']}):")
                if segment['operation'] == 'l':
                    data = segment['data']
                    print(f"    Line from ({data['start'][0]:.2f}, {data['start'][1]:.2f}) "
                          f"to ({data['end'][0]:.2f}, {data['end'][1]:.2f})")
                    print(f"    Length: {data['length']:.2f}")

                elif segment['operation'] == 'c':
                    data = segment['data']
                    print(f"    Cubic Bézier curve:")
                    print(f"      Start: ({data['start'][0]:.2f}, {data['start'][1]:.2f})")
                    print(f"      Control 1: ({data['control1'][0]:.2f}, {data['control1'][1]:.2f})")
                    print(f"      Control 2: ({data['control2'][0]:.2f}, {data['control2'][1]:.2f})")
                    print(f"      End: ({data['end'][0]:.2f}, {data['end'][1]:.2f})")

                elif segment['operation'] == 'q':
                    data = segment['data']
                    print(f"    Quadratic Bézier curve:")
                    print(f"      Start: ({data['start'][0]:.2f}, {data['start'][1]:.2f})")
                    print(f"      Control: ({data['control'][0]:.2f}, {data['control'][1]:.2f})")
                    print(f"      End: ({data['end'][0]:.2f}, {data['end'][1]:.2f})")

                elif segment['operation'] == 'm':
                    data = segment['data']
                    print(f"    Move to ({data['end'][0]:.2f}, {data['end'][1]:.2f})")

                elif segment['operation'] == 'z':
                    print(f"    Close path")

            if len(path['segments']) > 3:
                print(f"\n  ... and {len(path['segments']) - 3} more segments")

    # Print lines
    if lines:
        print(f"\n--- LINES (showing {min(len(lines), max_display)} of {len(lines)}) ---")
        for i, line in enumerate(lines[:max_display]):
            print(f"\nLine {i} (from {line['source']}):")
            print(f"  Start: ({line['start'][0]:.2f}, {line['start'][1]:.2f})")
            print(f"  End: ({line['end'][0]:.2f}, {line['end'][1]:.2f})")
            print(f"  Length: {line['length']:.2f}")

    # Print curves
    if curves:
        print(f"\n--- CURVES (showing {min(len(curves), max_display)} of {len(curves)}) ---")
        for i, curve in enumerate(curves[:max_display]):
            print(f"\nCurve {i} (type: {curve['type']}, from {curve['source']}):")
            if curve['type'] == 'circle':
                data = curve['data']
                print(f"  Center: ({data['center'][0]:.2f}, {data['center'][1]:.2f})")
                print(f"  Radius: {data['radius']:.2f}")
            elif curve['type'] == 'ellipse':
                data = curve['data']
                print(f"  Center: ({data['center'][0]:.2f}, {data['center'][1]:.2f})")
                print(f"  Radius X: {data['radius_x']:.2f}")
                print(f"  Radius Y: {data['radius_y']:.2f}")
            else:
                print(f"  Data: {curve['data']}")

def visualize_svg(svg_path, paths, shapes, lines, curves, output_dir='outputs/svg_analysis'):
    """Visualize SVG extraction"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))

    # Left: All extracted paths
    ax1.set_facecolor('white')
    ax1.set_aspect('equal')

    # Draw all lines
    for line in lines:
        x1, y1 = line['start']
        x2, y2 = line['end']
        ax1.plot([x1, x2], [y1, y2], 'b-', linewidth=1, alpha=0.6)

    # Draw curve control points
    for curve in curves:
        if 'control1' in curve.get('data', {}):
            data = curve['data']
            # Draw control points
            if 'start' in data:
                ax1.plot(data['start'][0], data['start'][1], 'ro', markersize=3)
            if 'control1' in data:
                ax1.plot(data['control1'][0], data['control1'][1], 'go', markersize=3)
            if 'control2' in data:
                ax1.plot(data['control2'][0], data['control2'][1], 'go', markersize=3)
            if 'end' in data:
                ax1.plot(data['end'][0], data['end'][1], 'ro', markersize=3)

    ax1.invert_yaxis()
    ax1.grid(True, alpha=0.3)
    ax1.set_title(f'Extracted Vectors\n{len(lines)} lines, {len(curves)} curves', fontweight='bold')

    # Right: Statistics
    ax2.axis('off')
    stats_text = f"""
SVG Vector Extraction Summary
{'='*40}

File: {svg_path.name}

Vector Elements:
  • Path elements: {len(paths)}
  • Shape elements: {len(shapes)}
  • Total lines: {len(lines)}
  • Total curves: {len(curves)}

Line Sources:
"""

    # Count line sources
    line_sources = {}
    for line in lines:
        source = line['source']
        line_sources[source] = line_sources.get(source, 0) + 1

    for source, count in sorted(line_sources.items()):
        stats_text += f"  • {source}: {count}\n"

    stats_text += f"\nCurve Types:\n"

    # Count curve types
    curve_types = {}
    for curve in curves:
        ctype = curve['type']
        curve_types[ctype] = curve_types.get(ctype, 0) + 1

    for ctype, count in sorted(curve_types.items()):
        stats_text += f"  • {ctype}: {count}\n"

    ax2.text(0.1, 0.5, stats_text, fontsize=12, family='monospace',
             verticalalignment='center')

    plt.tight_layout()

    # Save
    output_file = output_path / f"{svg_path.stem}_analysis.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\n✓ Saved visualization: {output_file}")

    return output_file

def export_to_json(svg_path, results, paths, shapes, lines, curves, output_dir='outputs/json'):
    """Export vectors to JSON"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    data = {
        'file': str(svg_path),
        'svg_metadata': {
            'viewBox': results.get('viewBox', 'not specified'),
            'width': results.get('width', 'not specified'),
            'height': results.get('height', 'not specified')
        },
        'paths': paths,
        'shapes': shapes,
        'lines': lines,
        'curves': curves,
        'summary': {
            'total_paths': len(paths),
            'total_shapes': len(shapes),
            'total_lines': len(lines),
            'total_curves': len(curves)
        }
    }

    output_file = output_path / f"{svg_path.stem}_vectors.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Saved JSON export: {output_file}")

    return output_file

def main():
    parser = argparse.ArgumentParser(
        description='Extract vector data (paths, lines, curves) from SVG files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python svg_vector_extractor.py image.svg
  python svg_vector_extractor.py /path/to/image.svg
  python svg_vector_extractor.py image1.svg image2.svg
  python svg_vector_extractor.py *.svg
  python svg_vector_extractor.py --dir svg_files
        '''
    )

    parser.add_argument(
        'files',
        nargs='*',
        help='SVG file path(s) to analyze. Can specify multiple files.'
    )

    parser.add_argument(
        '--dir',
        type=str,
        help='Directory containing SVG files (will process all *.svg files)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='outputs',
        help='Output directory for results (default: outputs)'
    )

    args = parser.parse_args()

    # Collect SVG files to process
    svg_files = []

    if args.dir:
        # Process directory
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"✗ Error: Directory '{args.dir}' does not exist")
            sys.exit(1)
        if not dir_path.is_dir():
            print(f"✗ Error: '{args.dir}' is not a directory")
            sys.exit(1)
        svg_files = list(dir_path.glob('*.svg'))
        if not svg_files:
            print(f"✗ No SVG files found in directory '{args.dir}'")
            sys.exit(1)
    elif args.files:
        # Process individual files
        for file_path in args.files:
            path = Path(file_path)
            if not path.exists():
                print(f"✗ Warning: File '{file_path}' does not exist, skipping...")
                continue
            if not path.is_file():
                print(f"✗ Warning: '{file_path}' is not a file, skipping...")
                continue
            if path.suffix.lower() != '.svg':
                print(f"✗ Warning: '{file_path}' is not an SVG file, skipping...")
                continue
            svg_files.append(path)
    else:
        # No arguments provided, show help
        print("✗ Error: Please specify SVG file(s) or use --dir option")
        print()
        parser.print_help()
        sys.exit(1)

    if not svg_files:
        print("✗ No valid SVG files to process")
        sys.exit(1)

    print(f"Found {len(svg_files)} SVG file(s) to process\n")

    for svg_file in svg_files:
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {svg_file.name}")
            print(f"  Path: {svg_file.absolute()}")
            print(f"{'='*60}")

            # Parse SVG
            results, root, namespaces = parse_svg(svg_file)

            # Extract elements
            print("\nExtracting vector elements...")
            paths = extract_path_elements(root, namespaces)
            shapes = extract_shape_elements(root)

            # Categorize
            lines, curves = categorize_vectors(paths, shapes)

            # Print analysis
            print_analysis(results, paths, shapes, lines, curves)

            # Print detailed vectors
            print_detailed_vectors(paths, shapes, lines, curves)

            # Visualize
            print("\nCreating visualizations...")
            svg_analysis_dir = Path(args.output) / 'svg_analysis'
            visualize_svg(svg_file, paths, shapes, lines, curves, output_dir=svg_analysis_dir)

            # Export to JSON
            json_output_dir = Path(args.output) / 'json'
            export_to_json(svg_file, results, paths, shapes, lines, curves, output_dir=json_output_dir)

            print(f"\n✓ Completed processing {svg_file.name}")

        except Exception as e:
            print(f"✗ Error processing {svg_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
