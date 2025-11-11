# Vector Image Analysis Tools

Python tools to extract vector data from images (SVG and PNG) with detailed coordinate information, similar to PDF vector extraction.

## Supported Formats

### SVG (Recommended) - `svg_vector_extractor.py`
**SVG is a true vector format** - this tool extracts actual vector paths with 100% accuracy:
- Extract path elements with precise coordinates
- Parse lines, curves (cubic/quadratic Bézier), arcs
- Extract basic shapes (rectangles, circles, ellipses, polygons)
- Get exact control points for all curves
- Native vector data - no approximation needed

### PNG - `png_vector_extractor.py`
**PNG is a raster format** - this tool reconstructs vector-like data using computer vision:
- Detect if a PNG appears "vector-like" (clean edges, limited colors)
- Extract lines using Hough Transform
- Extract curves and contours using edge detection
- Approximate vector coordinates from pixels
- Works best with clean, high-contrast images

## Installation

### Using pip

```bash
pip install -r requirements.txt
```

### Using uv (faster alternative)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt

# Or use uv to run the script directly (creates venv automatically)
uv run png_vector_extractor.py /path/to/image.png
```

## Usage

### SVG Vector Extraction (Recommended)

```bash
# Process a single SVG file
python svg_vector_extractor.py /path/to/your/image.svg

# Process multiple SVG files
python svg_vector_extractor.py image1.svg image2.svg image3.svg

# Process all SVG files in a directory
python svg_vector_extractor.py --dir /path/to/directory

# Using wildcards (in bash/zsh)
python svg_vector_extractor.py *.svg

# With uv
uv run svg_vector_extractor.py image.svg

# Show help
python svg_vector_extractor.py --help
```

### PNG Vector-like Extraction

```bash
# Process a single PNG file
python png_vector_extractor.py /path/to/your/image.png

# Process multiple PNG files
python png_vector_extractor.py image1.png image2.png image3.png

# Process all PNG files in a directory
python png_vector_extractor.py --dir /path/to/directory

# Using wildcards (in bash/zsh)
python png_vector_extractor.py *.png

# With uv
uv run png_vector_extractor.py image.png

# Show help
python png_vector_extractor.py --help
```

### Command-Line Arguments (both tools)

- **files**: One or more file paths to process
- **--dir**: Directory containing files (processes all matching files)
- **--output**: Output directory for results (default: outputs)

## Output

Both tools create output directories:

- `outputs/svg_analysis/` or `outputs/png_analysis/` - Comprehensive visualizations
- `outputs/png_vectors/` - Clean vector visualizations on white background (PNG tool only)
- `outputs/json/` - JSON exports of extracted vector data with coordinates

## Features

### SVG Vector Extraction (True Vectors)
- **Path Elements**: Parse SVG `<path>` elements with d attribute
  - Lines (L, l commands)
  - Cubic Bézier curves (C, c commands) with 2 control points
  - Quadratic Bézier curves (Q, q commands) with 1 control point
  - Arcs (A, a commands)
  - Move (M, m) and Close (Z, z) operations
- **Shape Elements**: Extract basic SVG shapes
  - Rectangles (`<rect>`)
  - Circles (`<circle>`)
  - Ellipses (`<ellipse>`)
  - Lines (`<line>`)
  - Polylines and Polygons (`<polyline>`, `<polygon>`)
- **Accurate Coordinates**: Extract exact coordinates from SVG definition
- **Styling Info**: Capture fill, stroke, stroke-width attributes

### PNG Vector-like Extraction (Approximated)
- **Classification**: Determines if PNG is vector-like, semi-vector, or raster
- **Edge Detection**: Uses Canny edge detection
- **Lines**: Extracted using Hough Line Transform
- **Curves**: Detected from contours with Bézier approximation
- **Contours**: Full contour extraction with simplified vertices

### Output Format

Similar to PDF extraction code, both tools provide:
- Move to (m) operations
- Line to (l) operations
- Curve operations (c=cubic, q=quadratic) with control points
- Exact coordinate pairs (x, y) for all points

## Example Output

### SVG Output Example

```
==========================================================
File: drawing.svg
==========================================================
ViewBox:            0 0 800 600
Width:              800
Height:             600

==========================================================
EXTRACTED ELEMENTS
==========================================================
Path elements:      24
Shape elements:     15
Total lines:        156
Total curves:       12

--- PATHS (showing 3 of 24) ---

Path 0:
  Fill: none
  Stroke: black
  Stroke width: 2
  Segments: 5

  Segment 0 (operation: m):
    Move to (100.00, 200.00)

  Segment 1 (operation: l):
    Line from (100.00, 200.00) to (300.00, 200.00)
    Length: 200.00

  Segment 2 (operation: c):
    Cubic Bézier curve:
      Start: (300.00, 200.00)
      Control 1: (350.00, 150.00)
      Control 2: (400.00, 150.00)
      End: (450.00, 200.00)
```

### PNG Output Example

```
==========================================================
File: example.png
==========================================================
Dimensions:         800 x 600
Mode:               RGB
Unique colors:      45
Has transparency:   False
Edge density:       2.34%

==========================================================
CLASSIFICATION: vector_like
==========================================================

✓ This PNG appears to be vector-like
  → Clean edges, limited colors
  → Good candidate for vector extraction

==========================================================
EXTRACTED VECTOR DATA
==========================================================
Lines detected:     156
Curves detected:    12
Contours detected:  45

--- LINES (showing 5 of 156) ---

Line 0:
  Start point: (120.00, 340.00)
  End point:   (450.00, 340.00)
  Length:      330.00 pixels
```

## Format Comparison

### SVG (Recommended):
- ✅ True vector format with actual path data
- ✅ 100% accurate coordinates
- ✅ Native support for all curve types
- ✅ Preserves exact control points
- ✅ No quality loss or approximation
- **Use when**: You have SVG files or can convert to SVG

### PNG:
- ⚠️ Raster format requiring reconstruction
- ⚠️ Accuracy depends on image quality
- ⚠️ May have false positives/negatives
- ⚠️ Approximates curves from pixels
- **Use when**: Only PNG available and image is vector-like

### PDF (using PyMuPDF):
- ✅ Extracts actual vector paths from PDF structure
- ✅ 100% accurate vector data
- ✅ Native support for lines, curves, rectangles
- **Use when**: Working with PDF files

## Tips for Best Results

### For SVG Files (Best Option):
1. **Use SVG when available** - Most accurate vector extraction
2. **Check SVG structure** - Tool supports standard SVG elements
3. **Works with any complexity** - Handles complex paths and shapes
4. **No quality requirements** - SVG is already vector data

### For PNG Files:
1. **Use high-resolution PNGs** - More pixels = better detection
2. **Clean images** - Fewer artifacts, cleaner edges
3. **High contrast** - Dark lines on light background (or vice versa)
4. **Limited colors** - Vector-like images work best
5. **Adjust parameters** - Modify edge detection thresholds in code if needed
6. **Consider conversion** - If possible, convert PNG to SVG first for better accuracy

## Adjustable Parameters (PNG Only)

For PNG extraction, you can modify detection thresholds in the code:

```python
# Line detection sensitivity
extract_lines(edges, min_line_length=30, max_line_gap=10)

# Contour minimum area
extract_contours(gray, min_area=100)

# Edge detection thresholds
cv2.Canny(gray, 50, 150)  # Lower/upper thresholds
```

## Limitations

### SVG Extraction:
- Requires valid XML structure
- Complex transformations may need additional processing
- Group elements are flattened (hierarchy not preserved)

### PNG Extraction:
- Cannot detect true vector data (PNG doesn't store it)
- Approximates curves from pixel data
- May miss or incorrectly detect shapes in noisy images
- Not suitable for photographs or complex raster images
- Accuracy varies with image quality
