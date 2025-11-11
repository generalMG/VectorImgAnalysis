import sys
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np
import cv2
from scipy import interpolate
from collections import defaultdict

def analyze_png(png_path):
    """Analyze PNG to determine if it's vector-like or raster"""
    img = Image.open(png_path)
    img_array = np.array(img)

    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    results = {
        'file': png_path.name,
        'width': img.width,
        'height': img.height,
        'mode': img.mode,
        'unique_colors': 0,
        'edge_density': 0.0,
        'has_transparency': False,
        'lines': [],
        'curves': [],
        'contours': [],
    }

    # Check for transparency
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        results['has_transparency'] = True

    # Count unique colors
    if len(img_array.shape) == 3:
        pixels = img_array.reshape(-1, img_array.shape[-1])
        unique_colors = np.unique(pixels, axis=0)
        results['unique_colors'] = len(unique_colors)
    else:
        results['unique_colors'] = len(np.unique(img_array))

    # Calculate edge density
    edges = cv2.Canny(gray, 50, 150)
    results['edge_density'] = np.sum(edges > 0) / edges.size * 100

    # Classify the image
    results['classification'] = classify_png(results)

    return results, gray, edges

def classify_png(results):
    """Classify PNG as vector-like or raster"""
    unique_colors = results['unique_colors']
    edge_density = results['edge_density']

    if unique_colors <= 50 and edge_density > 1.0:
        return 'vector_like'
    elif unique_colors <= 256 and edge_density > 0.5:
        return 'semi_vector'
    else:
        return 'raster'

def extract_lines(edges, min_line_length=30, max_line_gap=10):
    """Extract lines using Hough Line Transform"""
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=50,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )

    line_segments = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            line_segments.append({
                'type': 'line',
                'start': (float(x1), float(y1)),
                'end': (float(x2), float(y2)),
                'length': np.sqrt((x2-x1)**2 + (y2-y1)**2)
            })

    return line_segments

def extract_contours(gray, min_area=100):
    """Extract contours and approximate them as curves"""
    # Threshold the image
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, hierarchy = cv2.findContours(
        thresh,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contour_data = []
    for idx, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)

        # Approximate the contour
        epsilon = 0.01 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Extract points
        points = []
        for point in contour:
            px, py = point[0]
            points.append((float(px), float(py)))

        contour_data.append({
            'index': idx,
            'area': float(area),
            'perimeter': float(cv2.arcLength(contour, True)),
            'bbox': (int(x), int(y), int(w), int(h)),
            'num_vertices': len(approx),
            'points': points,
            'simplified_points': [(float(p[0][0]), float(p[0][1])) for p in approx]
        })

    return contour_data

def detect_curves_from_contours(contour_data, curve_threshold=5):
    """Detect curves from contours based on vertex count"""
    curves = []

    for contour in contour_data:
        if contour['num_vertices'] >= curve_threshold:
            # This is likely a curve
            points = contour['points']

            # Sample points for curve fitting
            if len(points) > 10:
                # Use simplified points for curve representation
                curves.append({
                    'type': 'curve',
                    'control_points': contour['simplified_points'],
                    'all_points': points,
                    'num_points': len(points),
                    'bbox': contour['bbox']
                })

    return curves

def fit_bezier_curves(points, num_control_points=4):
    """Fit Bezier curves to a set of points"""
    if len(points) < num_control_points:
        return points

    points = np.array(points)

    # Parametric parameter for the points
    t = np.linspace(0, 1, len(points))

    # Fit spline to x and y separately
    try:
        # Sample control points
        indices = np.linspace(0, len(points)-1, num_control_points, dtype=int)
        control_points = points[indices]
        return control_points.tolist()
    except:
        return points[:num_control_points].tolist() if len(points) >= num_control_points else points.tolist()

def print_analysis(results, lines, curves, contours):
    """Print detailed analysis of the PNG"""
    print(f"\n{'='*60}")
    print(f"File: {results['file']}")
    print(f"{'='*60}")
    print(f"Dimensions:         {results['width']} x {results['height']}")
    print(f"Mode:               {results['mode']}")
    print(f"Unique colors:      {results['unique_colors']}")
    print(f"Has transparency:   {results['has_transparency']}")
    print(f"Edge density:       {results['edge_density']:.2f}%")
    print(f"\n{'='*60}")
    print(f"CLASSIFICATION: {results['classification']}")
    print(f"{'='*60}")

    if results['classification'] == 'vector_like':
        print("\n✓ This PNG appears to be vector-like")
        print("  → Clean edges, limited colors")
        print("  → Good candidate for vector extraction")
    elif results['classification'] == 'semi_vector':
        print("\n✓ This PNG has some vector-like characteristics")
        print("  → May contain mixed raster/vector content")
    else:
        print("\n✓ This PNG appears to be purely raster")
        print("  → High color count or low edge density")
        print("  → Vector extraction may be less accurate")

    print(f"\n{'='*60}")
    print(f"EXTRACTED VECTOR DATA")
    print(f"{'='*60}")
    print(f"Lines detected:     {len(lines)}")
    print(f"Curves detected:    {len(curves)}")
    print(f"Contours detected:  {len(contours)}")

def print_detailed_vectors(lines, curves, contours, max_display=5):
    """Print detailed vector information similar to PDF code"""
    print(f"\n{'='*60}")
    print(f"DETAILED VECTOR INFORMATION")
    print(f"{'='*60}")

    # Print lines
    if lines:
        print(f"\n--- LINES (showing {min(len(lines), max_display)} of {len(lines)}) ---")
        for i, line in enumerate(lines[:max_display]):
            print(f"\nLine {i}:")
            print(f"  Start point: ({line['start'][0]:.2f}, {line['start'][1]:.2f})")
            print(f"  End point:   ({line['end'][0]:.2f}, {line['end'][1]:.2f})")
            print(f"  Length:      {line['length']:.2f} pixels")

    # Print curves
    if curves:
        print(f"\n--- CURVES (showing {min(len(curves), max_display)} of {len(curves)}) ---")
        for i, curve in enumerate(curves[:max_display]):
            print(f"\nCurve {i}:")
            print(f"  Type: {curve['type']}")
            print(f"  Total points: {curve['num_points']}")
            print(f"  Control points ({len(curve['control_points'])}):")

            # Fit Bezier control points
            bezier_controls = fit_bezier_curves(curve['control_points'], num_control_points=4)
            for j, pt in enumerate(bezier_controls):
                print(f"    P{j}: ({pt[0]:.2f}, {pt[1]:.2f})")

            print(f"  Bounding box: {curve['bbox']}")

    # Print contour details
    if contours:
        print(f"\n--- CONTOURS (showing {min(len(contours), max_display)} of {len(contours)}) ---")
        for i, contour in enumerate(contours[:max_display]):
            print(f"\nContour {i}:")
            print(f"  Area: {contour['area']:.2f}")
            print(f"  Perimeter: {contour['perimeter']:.2f}")
            print(f"  Vertices: {contour['num_vertices']}")
            print(f"  Bounding box: {contour['bbox']}")
            print(f"  Simplified points ({len(contour['simplified_points'])}):")
            for j, pt in enumerate(contour['simplified_points'][:5]):
                print(f"    ({pt[0]:.2f}, {pt[1]:.2f})")
            if len(contour['simplified_points']) > 5:
                print(f"    ... and {len(contour['simplified_points']) - 5} more points")

def visualize_extraction(png_path, gray, edges, lines, curves, contours, output_dir='outputs/png_analysis'):
    """Visualize the extraction process"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load original image
    img = Image.open(png_path)
    img_array = np.array(img)

    # Create comprehensive visualization
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f"PNG Vector Extraction: {png_path.name}", fontsize=16, fontweight='bold')

    # 1. Original image
    axes[0, 0].imshow(img_array)
    axes[0, 0].set_title('Original Image')
    axes[0, 0].axis('off')

    # 2. Grayscale
    axes[0, 1].imshow(gray, cmap='gray')
    axes[0, 1].set_title('Grayscale')
    axes[0, 1].axis('off')

    # 3. Edge detection
    axes[0, 2].imshow(edges, cmap='gray')
    axes[0, 2].set_title(f'Edge Detection ({np.sum(edges > 0)} pixels)')
    axes[0, 2].axis('off')

    # 4. Extracted lines
    axes[1, 0].imshow(img_array)
    for line in lines:
        x1, y1 = line['start']
        x2, y2 = line['end']
        axes[1, 0].plot([x1, x2], [y1, y2], 'r-', linewidth=2, alpha=0.7)
    axes[1, 0].set_title(f'Extracted Lines ({len(lines)})')
    axes[1, 0].axis('off')

    # 5. Extracted curves
    axes[1, 1].imshow(img_array)
    for curve in curves:
        points = np.array(curve['all_points'])
        if len(points) > 0:
            axes[1, 1].plot(points[:, 0], points[:, 1], 'g-', linewidth=2, alpha=0.7)
            # Plot control points
            control_pts = np.array(curve['control_points'])
            axes[1, 1].scatter(control_pts[:, 0], control_pts[:, 1], c='blue', s=30, zorder=5)
    axes[1, 1].set_title(f'Extracted Curves ({len(curves)})')
    axes[1, 1].axis('off')

    # 6. All contours
    axes[1, 2].imshow(np.ones_like(gray) * 255, cmap='gray')
    for contour in contours:
        points = np.array(contour['points'])
        if len(points) > 0:
            axes[1, 2].plot(points[:, 0], points[:, 1], 'k-', linewidth=1, alpha=0.8)
    axes[1, 2].set_title(f'All Contours ({len(contours)})')
    axes[1, 2].axis('off')

    plt.tight_layout()

    # Save
    output_file = output_path / f"{png_path.stem}_analysis.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\n✓ Saved visualization: {output_file}")

    return output_file

def visualize_vectors_separately(png_path, lines, curves, contours, output_dir='outputs/png_vectors'):
    """Visualize extracted vectors on white background (similar to PDF code)"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    img = Image.open(png_path)
    width, height = img.size

    # Create figure with white background
    fig, ax = plt.subplots(1, figsize=(12, 12))
    ax.set_facecolor('white')

    # Draw all lines
    for line in lines:
        x1, y1 = line['start']
        x2, y2 = line['end']
        ax.plot([x1, x2], [y1, y2], 'k-', linewidth=1, alpha=0.8)

    # Draw all curves
    for curve in curves:
        points = np.array(curve['all_points'])
        if len(points) > 0:
            ax.plot(points[:, 0], points[:, 1], 'k-', linewidth=1, alpha=0.8)

    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)  # Invert Y axis
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X coordinate', fontsize=12)
    ax.set_ylabel('Y coordinate', fontsize=12)
    ax.set_title(f'Extracted Vectors: {len(lines)} lines, {len(curves)} curves',
                 fontsize=14, fontweight='bold')

    # Save
    output_file = output_path / f"{png_path.stem}_vectors.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved vector visualization: {output_file}")

    return output_file

def export_vectors_to_json(png_path, lines, curves, contours, output_dir='outputs/json'):
    """Export extracted vectors to JSON format"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    import json

    data = {
        'file': str(png_path),
        'lines': lines,
        'curves': curves,
        'contours': contours,
        'summary': {
            'total_lines': len(lines),
            'total_curves': len(curves),
            'total_contours': len(contours)
        }
    }

    output_file = output_path / f"{png_path.stem}_vectors.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Saved JSON export: {output_file}")

    return output_file

def main():
    parser = argparse.ArgumentParser(
        description='Extract vector-like data (lines, curves, contours) from PNG images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python png_vector_extractor.py image.png
  python png_vector_extractor.py /path/to/image.png
  python png_vector_extractor.py image1.png image2.png image3.png
  python png_vector_extractor.py *.png
  python png_vector_extractor.py --dir png_files
        '''
    )

    parser.add_argument(
        'files',
        nargs='*',
        help='PNG file path(s) to analyze. Can specify multiple files.'
    )

    parser.add_argument(
        '--dir',
        type=str,
        help='Directory containing PNG files (will process all *.png files)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='outputs',
        help='Output directory for results (default: outputs)'
    )

    args = parser.parse_args()

    # Collect PNG files to process
    png_files = []

    if args.dir:
        # Process directory
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"✗ Error: Directory '{args.dir}' does not exist")
            sys.exit(1)
        if not dir_path.is_dir():
            print(f"✗ Error: '{args.dir}' is not a directory")
            sys.exit(1)
        png_files = list(dir_path.glob('*.png'))
        if not png_files:
            print(f"✗ No PNG files found in directory '{args.dir}'")
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
            if path.suffix.lower() != '.png':
                print(f"✗ Warning: '{file_path}' is not a PNG file, skipping...")
                continue
            png_files.append(path)
    else:
        # No arguments provided, show help
        print("✗ Error: Please specify PNG file(s) or use --dir option")
        print()
        parser.print_help()
        sys.exit(1)

    if not png_files:
        print("✗ No valid PNG files to process")
        sys.exit(1)

    print(f"Found {len(png_files)} PNG file(s) to process\n")

    for png_file in png_files:
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {png_file.name}")
            print(f"  Path: {png_file.absolute()}")
            print(f"{'='*60}")

            # Analyze PNG
            results, gray, edges = analyze_png(png_file)

            # Extract vectors
            print("\nExtracting vectors...")
            lines = extract_lines(edges)
            contours = extract_contours(gray)
            curves = detect_curves_from_contours(contours)

            # Print analysis
            print_analysis(results, lines, curves, contours)

            # Print detailed vectors
            print_detailed_vectors(lines, curves, contours)

            # Visualize
            print("\nCreating visualizations...")
            visualize_extraction(png_file, gray, edges, lines, curves, contours)
            visualize_vectors_separately(png_file, lines, curves, contours)

            # Export to JSON
            export_vectors_to_json(png_file, lines, curves, contours)

            print(f"\n✓ Completed processing {png_file.name}")

        except Exception as e:
            print(f"✗ Error processing {png_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
