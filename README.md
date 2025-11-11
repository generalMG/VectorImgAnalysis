# PNG Vector Extraction Tool

A Python tool to analyze PNG images and extract vector-like data (lines, curves, contours) similar to PDF vector extraction.

## Important Note

**PNG is a raster format**, meaning it stores pixel data, not actual vector information like PDFs. This tool uses computer vision techniques to:
- Detect if a PNG appears "vector-like" (clean edges, limited colors)
- Extract lines using Hough Transform
- Extract curves and contours using edge detection and contour approximation
- Provide coordinates similar to PDF vector extraction

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Process a single PNG file
python png_vector_extractor.py /path/to/your/image.png

# Process multiple PNG files
python png_vector_extractor.py image1.png image2.png image3.png

# Process all PNG files in a directory
python png_vector_extractor.py --dir /path/to/directory

# Using wildcards (in bash/zsh)
python png_vector_extractor.py *.png

# Show help
python png_vector_extractor.py --help
```

### Command-Line Arguments

- **files**: One or more PNG file paths to process
- **--dir**: Directory containing PNG files (processes all *.png files)
- **--output**: Output directory for results (default: outputs)

## Output

The tool creates several output directories:

- `outputs/png_analysis/` - Comprehensive visualizations showing the extraction process
- `outputs/png_vectors/` - Clean vector visualizations on white background
- `outputs/json/` - JSON exports of extracted vector data

## Features

### Analysis
- **Classification**: Determines if PNG is vector-like, semi-vector, or raster
- **Edge Detection**: Uses Canny edge detection
- **Unique Color Count**: Helps determine vector-like characteristics
- **Transparency Detection**: Identifies if image has alpha channel

### Vector Extraction
- **Lines**: Extracted using Hough Line Transform
  - Start and end coordinates
  - Length calculation
- **Curves**: Detected from contours
  - Control points (Bezier approximation)
  - All curve points
  - Bounding boxes
- **Contours**: Full contour extraction
  - Area and perimeter
  - Simplified vertex representation
  - Bounding boxes

### Output Format

Similar to your PDF extraction code, this provides:
- Move to (m) operations
- Line to (l) operations
- Curve (c) operations with control points
- Coordinate pairs (x, y) for all points

## Example Output

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

## Comparison with PDF Extraction

### PDF (using PyMuPDF):
- Extracts actual vector paths from PDF structure
- 100% accurate vector data
- Native support for lines, curves, rectangles

### PNG (this tool):
- Reconstructs vectors from raster pixels
- Accuracy depends on image quality
- May have false positives/negatives
- Best results with: clean lines, high contrast, limited colors

## Tips for Best Results

1. **Use high-resolution PNGs** - More pixels = better detection
2. **Clean images** - Fewer artifacts, cleaner edges
3. **High contrast** - Dark lines on light background (or vice versa)
4. **Limited colors** - Vector-like images work best
5. **Adjust parameters** - Modify edge detection thresholds in code if needed

## Adjustable Parameters

In the code, you can modify:

```python
# Line detection sensitivity
extract_lines(edges, min_line_length=30, max_line_gap=10)

# Contour minimum area
extract_contours(gray, min_area=100)

# Edge detection thresholds
cv2.Canny(gray, 50, 150)  # Lower/upper thresholds
```

## Limitations

- Cannot detect true vector data (PNG doesn't store it)
- Approximates curves from pixel data
- May miss or incorrectly detect shapes in noisy images
- Not suitable for photographs or complex raster images
