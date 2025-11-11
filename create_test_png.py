"""
Create a test PNG with vector-like shapes for testing the extraction tool
"""
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

def create_test_png():
    """Create a simple PNG with vector-like shapes"""

    # Create white background
    width, height = 800, 600
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # Draw some lines
    draw.line([(100, 100), (700, 100)], fill='black', width=3)
    draw.line([(100, 100), (100, 500)], fill='black', width=3)
    draw.line([(700, 100), (700, 500)], fill='black', width=3)
    draw.line([(100, 500), (700, 500)], fill='black', width=3)

    # Draw diagonal lines
    draw.line([(150, 150), (650, 450)], fill='blue', width=2)
    draw.line([(650, 150), (150, 450)], fill='red', width=2)

    # Draw rectangles
    draw.rectangle([(200, 200), (350, 300)], outline='green', width=2)
    draw.rectangle([(450, 200), (600, 300)], outline='purple', width=2)

    # Draw circles (will be detected as curves)
    draw.ellipse([(250, 350), (350, 450)], outline='black', width=2)
    draw.ellipse([(450, 350), (600, 450)], outline='black', width=2)

    # Draw an arc (curve)
    draw.arc([(300, 50), (500, 150)], start=0, end=180, fill='darkblue', width=3)

    # Save
    output_dir = Path('png_files')
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / 'test_vector_like.png'
    img.save(output_file)

    print(f"✓ Created test PNG: {output_file}")
    print(f"  Dimensions: {width} x {height}")
    print(f"  Contains: lines, rectangles, circles, and arcs")
    print(f"\nNow run: python png_vector_extractor.py")

def create_complex_test_png():
    """Create a more complex test PNG with various shapes"""

    width, height = 1000, 800
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # Grid of lines
    for i in range(0, width, 50):
        draw.line([(i, 0), (i, height)], fill='lightgray', width=1)
    for i in range(0, height, 50):
        draw.line([(0, i), (width, i)], fill='lightgray', width=1)

    # Main border
    draw.rectangle([(10, 10), (width-10, height-10)], outline='black', width=5)

    # Various polygons
    # Triangle
    draw.polygon([(100, 100), (200, 100), (150, 50)], outline='red', width=2)

    # Pentagon
    import math
    cx, cy, r = 300, 200, 60
    pentagon = []
    for i in range(5):
        angle = i * 2 * math.pi / 5 - math.pi / 2
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pentagon.append((x, y))
    draw.polygon(pentagon, outline='blue', width=2)

    # Hexagon
    cx, cy, r = 500, 200, 60
    hexagon = []
    for i in range(6):
        angle = i * 2 * math.pi / 6
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        hexagon.append((x, y))
    draw.polygon(hexagon, outline='green', width=2)

    # Multiple circles
    for i, radius in enumerate([30, 50, 70]):
        x = 150 + i * 100
        y = 400
        draw.ellipse([(x-radius, y-radius), (x+radius, y+radius)],
                    outline='purple', width=2)

    # Bezier-like curve using chords
    points = []
    for i in range(50):
        t = i / 49.0
        x = 500 + 200 * t
        y = 400 + 100 * math.sin(t * 4 * math.pi)
        points.append((x, y))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill='darkred', width=2)

    # Text-like elements (as shapes)
    draw.rectangle([(50, 600), (150, 650)], outline='black', width=2)
    draw.rectangle([(170, 600), (270, 650)], outline='black', width=2)
    draw.rectangle([(290, 600), (390, 650)], outline='black', width=2)

    # Save
    output_dir = Path('png_files')
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / 'test_complex_shapes.png'
    img.save(output_file)

    print(f"✓ Created complex test PNG: {output_file}")
    print(f"  Dimensions: {width} x {height}")
    print(f"  Contains: polygons, circles, curves, and grid")

if __name__ == "__main__":
    print("Creating test PNG files...\n")
    create_test_png()
    print()
    create_complex_test_png()
    print("\n" + "="*60)
    print("Test files created successfully!")
    print("="*60)
    print("\nNext step: Run the extraction tool")
    print("  python png_vector_extractor.py")
