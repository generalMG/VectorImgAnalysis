import sys
import argparse
import json
from pathlib import Path
import numpy as np
import ezdxf
from ezdxf import colors
from ezdxf.math import Vec3

def load_vector_data(json_path):
    """Load vector data from JSON export"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def get_svg_height(vector_data):
    """Extract SVG height from metadata for coordinate transformation"""
    svg_metadata = vector_data.get('svg_metadata', {})

    # Try to get height from metadata
    height_str = svg_metadata.get('height', 'not specified')
    viewBox_str = svg_metadata.get('viewBox', 'not specified')

    # Try parsing height attribute
    if height_str != 'not specified':
        try:
            # Remove units like 'px', 'pt', etc.
            height = float(''.join(c for c in str(height_str) if c.isdigit() or c == '.'))
            return height
        except:
            pass

    # Try parsing viewBox (format: "min-x min-y width height")
    if viewBox_str != 'not specified':
        try:
            parts = str(viewBox_str).split()
            if len(parts) == 4:
                height = float(parts[3])
                return height
        except:
            pass

    # Default: try to determine from data bounds
    print("  Warning: Could not determine SVG height from metadata, calculating from bounds...")
    return None

def flip_y(point, height):
    """Flip Y coordinate for SVG to DXF conversion"""
    if height is None:
        return point
    return (point[0], height - point[1])

def flip_y_list(points, height):
    """Flip Y coordinates for a list of points"""
    if height is None:
        return points
    return [flip_y(p, height) for p in points]

def create_dxf_from_vectors(vector_data, output_path, layer_by_type=True):
    """Convert vector data to DXF file"""

    # Get SVG height for coordinate transformation
    svg_height = get_svg_height(vector_data)
    if svg_height:
        print(f"  SVG height detected: {svg_height}")
        print(f"  Applying Y-axis flip for CAD coordinate system...")
    else:
        print(f"  Warning: Could not determine SVG height, coordinates may be flipped")

    # Create a new DXF document
    doc = ezdxf.new('R2010')  # AutoCAD 2010 format
    msp = doc.modelspace()

    # Create layers if organizing by type
    if layer_by_type:
        doc.layers.add('LINES', color=colors.WHITE)
        doc.layers.add('CURVES', color=colors.GREEN)
        doc.layers.add('SHAPES', color=colors.CYAN)
        doc.layers.add('PATHS', color=colors.YELLOW)

    stats = {
        'lines': 0,
        'curves': 0,
        'arcs': 0,
        'circles': 0,
        'ellipses': 0,
        'polylines': 0,
        'splines': 0
    }

    print(f"\nConverting vectors to DXF...")

    # Process path elements
    paths = vector_data.get('paths', [])
    for path_idx, path in enumerate(paths):
        print(f"  Processing path {path_idx + 1}/{len(paths)}...")

        segments = path.get('segments', [])
        if not segments:
            continue

        # Determine layer
        layer = 'PATHS' if layer_by_type else '0'

        # Process each segment in the path
        current_point = None
        polyline_points = []

        for segment in segments:
            operation = segment.get('operation', '')
            data = segment.get('data', {})

            if operation == 'm':
                # Move operation - start new polyline
                if polyline_points and len(polyline_points) > 1:
                    # Save previous polyline
                    add_polyline(msp, polyline_points, layer, svg_height)
                    stats['polylines'] += 1
                    polyline_points = []

                end_point = data.get('end', (0, 0))
                current_point = end_point
                polyline_points.append(end_point)

            elif operation == 'l':
                # Line segment
                start = data.get('start', (0, 0))
                end = data.get('end', (0, 0))

                if not polyline_points:
                    polyline_points.append(start)
                polyline_points.append(end)
                current_point = end
                stats['lines'] += 1

            elif operation == 'c':
                # Cubic Bezier curve - approximate with polyline or spline
                start = data.get('start', (0, 0))
                control1 = data.get('control1', (0, 0))
                control2 = data.get('control2', (0, 0))
                end = data.get('end', (0, 0))

                # Flip Y coordinates
                start = flip_y(start, svg_height)
                control1 = flip_y(control1, svg_height)
                control2 = flip_y(control2, svg_height)
                end = flip_y(end, svg_height)

                # Create spline through cubic Bezier
                points = approximate_cubic_bezier(start, control1, control2, end)

                # Add spline
                spline = msp.add_spline(points, degree=3)
                spline.dxf.layer = layer
                stats['splines'] += 1

                current_point = end

            elif operation == 'q':
                # Quadratic Bezier curve
                start = data.get('start', (0, 0))
                control = data.get('control', (0, 0))
                end = data.get('end', (0, 0))

                # Flip Y coordinates
                start = flip_y(start, svg_height)
                control = flip_y(control, svg_height)
                end = flip_y(end, svg_height)

                # Approximate with polyline
                points = approximate_quadratic_bezier(start, control, end)

                # Add as polyline (coordinates already flipped)
                add_polyline(msp, points, layer, None)
                stats['polylines'] += 1

                current_point = end

            elif operation == 'a':
                # Arc segment
                # For now, approximate with polyline
                start = data.get('start', (0, 0))
                end = data.get('end', (0, 0))

                # Simple arc approximation
                points = [start, end]  # Simplified - could be improved
                add_polyline(msp, points, layer, svg_height)
                stats['arcs'] += 1

                current_point = end

            elif operation == 'z':
                # Close path
                if polyline_points and len(polyline_points) > 1:
                    # Close the polyline
                    add_polyline(msp, polyline_points, layer, svg_height, closed=True)
                    stats['polylines'] += 1
                    polyline_points = []

        # Add remaining polyline if any
        if polyline_points and len(polyline_points) > 1:
            add_polyline(msp, polyline_points, layer, svg_height)
            stats['polylines'] += 1

    # Process shape elements
    shapes = vector_data.get('shapes', [])
    for shape_idx, shape in enumerate(shapes):
        shape_type = shape.get('type', '')
        layer = 'SHAPES' if layer_by_type else '0'

        if shape_type == 'line':
            start = shape.get('start', (0, 0))
            end = shape.get('end', (0, 0))
            add_line(msp, start, end, layer, svg_height)
            stats['lines'] += 1

        elif shape_type == 'rectangle':
            corners = shape.get('corners', [])
            if len(corners) == 4:
                add_polyline(msp, corners, layer, svg_height, closed=True)
                stats['polylines'] += 1

        elif shape_type == 'circle':
            center = shape.get('center', (0, 0))
            radius = shape.get('radius', 0)
            add_circle(msp, center, radius, layer, svg_height)
            stats['circles'] += 1

        elif shape_type == 'ellipse':
            center = shape.get('center', (0, 0))
            rx = shape.get('radius_x', 0)
            ry = shape.get('radius_y', 0)
            add_ellipse(msp, center, rx, ry, layer, svg_height)
            stats['ellipses'] += 1

        elif shape_type in ['polyline', 'polygon']:
            points = shape.get('points', [])
            closed = shape.get('closed', False)
            if points:
                add_polyline(msp, points, layer, svg_height, closed=closed)
                stats['polylines'] += 1

    # Process extracted lines (from categorization)
    lines = vector_data.get('lines', [])
    layer = 'LINES' if layer_by_type else '0'
    for line in lines:
        start = line.get('start', (0, 0))
        end = line.get('end', (0, 0))
        add_line(msp, start, end, layer, svg_height)

    # Process extracted curves (from categorization)
    curves = vector_data.get('curves', [])
    layer = 'CURVES' if layer_by_type else '0'
    for curve in curves:
        curve_type = curve.get('type', '')
        curve_data = curve.get('data', {})

        if curve_type == 'circle' and 'center' in curve_data:
            center = curve_data.get('center', (0, 0))
            radius = curve_data.get('radius', 0)
            add_circle(msp, center, radius, layer, svg_height)
            stats['circles'] += 1

        elif curve_type == 'ellipse' and 'center' in curve_data:
            center = curve_data.get('center', (0, 0))
            rx = curve_data.get('radius_x', 0)
            ry = curve_data.get('radius_y', 0)
            add_ellipse(msp, center, rx, ry, layer, svg_height)
            stats['ellipses'] += 1

    # Save DXF file
    doc.saveas(output_path)

    return stats

def add_line(msp, start, end, layer, height=None):
    """Add a line to the modelspace"""
    # Flip Y coordinates
    start = flip_y(start, height)
    end = flip_y(end, height)

    msp.add_line(
        Vec3(start[0], start[1], 0),
        Vec3(end[0], end[1], 0),
        dxfattribs={'layer': layer}
    )

def add_polyline(msp, points, layer, height=None, closed=False):
    """Add a polyline to the modelspace"""
    if len(points) < 2:
        return

    # Flip Y coordinates
    points = flip_y_list(points, height)

    points_3d = [Vec3(p[0], p[1], 0) for p in points]
    polyline = msp.add_lwpolyline(
        points_3d,
        dxfattribs={'layer': layer}
    )
    if closed:
        polyline.close()

def add_circle(msp, center, radius, layer, height=None):
    """Add a circle to the modelspace"""
    if radius <= 0:
        return

    # Flip Y coordinate
    center = flip_y(center, height)

    msp.add_circle(
        Vec3(center[0], center[1], 0),
        radius,
        dxfattribs={'layer': layer}
    )

def add_ellipse(msp, center, rx, ry, layer, height=None):
    """Add an ellipse to the modelspace"""
    if rx <= 0 or ry <= 0:
        return

    # Flip Y coordinate
    center = flip_y(center, height)

    # Calculate major axis vector
    if rx >= ry:
        major_axis = Vec3(rx, 0, 0)
        ratio = ry / rx
    else:
        major_axis = Vec3(0, ry, 0)
        ratio = rx / ry

    msp.add_ellipse(
        Vec3(center[0], center[1], 0),
        major_axis,
        ratio,
        dxfattribs={'layer': layer}
    )

def approximate_cubic_bezier(p0, p1, p2, p3, num_points=20):
    """Approximate a cubic Bezier curve with points"""
    points = []
    for i in range(num_points + 1):
        t = i / num_points

        # Cubic Bezier formula
        x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]

        points.append((x, y))

    return points

def approximate_quadratic_bezier(p0, p1, p2, num_points=15):
    """Approximate a quadratic Bezier curve with points"""
    points = []
    for i in range(num_points + 1):
        t = i / num_points

        # Quadratic Bezier formula
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]

        points.append((x, y))

    return points

def print_stats(stats):
    """Print conversion statistics"""
    print(f"\n{'='*60}")
    print(f"DXF CONVERSION STATISTICS")
    print(f"{'='*60}")
    print(f"Lines:              {stats['lines']}")
    print(f"Polylines:          {stats['polylines']}")
    print(f"Splines:            {stats['splines']}")
    print(f"Circles:            {stats['circles']}")
    print(f"Ellipses:           {stats['ellipses']}")
    print(f"Arcs:               {stats['arcs']}")
    print(f"{'='*60}")
    total = sum(stats.values())
    print(f"Total entities:     {total}")
    print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(
        description='Convert SVG vector data (JSON) to DXF format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python svg_to_dxf.py outputs/json/drawing_vectors.json
  python svg_to_dxf.py input.json -o output.dxf
  python svg_to_dxf.py input.json --no-layers
  python svg_to_dxf.py --dir outputs/json
        '''
    )

    parser.add_argument(
        'input',
        nargs='?',
        help='JSON file with vector data from svg_vector_extractor.py'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output DXF file path (default: same name as input with .dxf extension)'
    )

    parser.add_argument(
        '--dir',
        type=str,
        help='Process all JSON files in directory'
    )

    parser.add_argument(
        '--no-layers',
        action='store_true',
        help='Do not organize entities by type into separate layers'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs/dxf',
        help='Output directory for DXF files (default: outputs/dxf)'
    )

    args = parser.parse_args()

    # Collect JSON files to process
    json_files = []

    if args.dir:
        # Process directory
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"✗ Error: Directory '{args.dir}' does not exist")
            sys.exit(1)
        if not dir_path.is_dir():
            print(f"✗ Error: '{args.dir}' is not a directory")
            sys.exit(1)
        json_files = list(dir_path.glob('*_vectors.json'))
        if not json_files:
            print(f"✗ No vector JSON files found in directory '{args.dir}'")
            sys.exit(1)
    elif args.input:
        # Process single file
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"✗ Error: File '{args.input}' does not exist")
            sys.exit(1)
        if not input_path.is_file():
            print(f"✗ Error: '{args.input}' is not a file")
            sys.exit(1)
        json_files.append(input_path)
    else:
        # No arguments provided, show help
        print("✗ Error: Please specify JSON file or use --dir option")
        print()
        parser.print_help()
        sys.exit(1)

    if not json_files:
        print("✗ No valid JSON files to process")
        sys.exit(1)

    print(f"Found {len(json_files)} JSON file(s) to convert\n")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_file in json_files:
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {json_file.name}")
            print(f"  Path: {json_file.absolute()}")
            print(f"{'='*60}")

            # Load vector data
            print("\nLoading vector data from JSON...")
            vector_data = load_vector_data(json_file)

            # Determine output path
            if args.output and len(json_files) == 1:
                output_path = Path(args.output)
            else:
                # Use same name as JSON but with .dxf extension
                output_name = json_file.stem.replace('_vectors', '') + '.dxf'
                output_path = output_dir / output_name

            # Convert to DXF
            layer_by_type = not args.no_layers
            stats = create_dxf_from_vectors(vector_data, output_path, layer_by_type)

            # Print statistics
            print_stats(stats)

            print(f"\n✓ DXF file saved: {output_path.absolute()}")
            print(f"  Size: {output_path.stat().st_size / 1024:.2f} KB")

        except Exception as e:
            print(f"✗ Error processing {json_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
