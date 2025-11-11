# SVG to DXF Converter

Python tools to extract vector data from SVG files and convert to CAD formats (DXF), with batch processing support for high-volume conversions.

## Dataset

This tool is designed for converting the **FloorPlanCAD dataset**: [https://floorplancad.github.io/](https://floorplancad.github.io/)

The FloorPlanCAD dataset contains large-scale floor plan data in SVG format with CAD annotations. This converter processes these SVG files into DXF format for CAD applications, preserving vector accuracy including proper arc handling for architectural elements like door swings.

## Features

### SVG Vector Extraction - `svg_vector_extractor.py`
**SVG is a true vector format** - this tool extracts actual vector paths with 100% accuracy:
- Extract path elements with precise coordinates
- Parse lines, curves (cubic/quadratic Bézier), arcs with proper radius/sweep handling
- Extract basic shapes (rectangles, circles, ellipses, polygons)
- Get exact control points for all curves
- Native vector data - no approximation needed

### DXF Export - `svg_to_dxf.py`
**DXF is the standard CAD interchange format** - convert extracted SVG vectors to DXF:
- AutoCAD R2010 compatible format
- Proper arc conversion with center parameterization
- Preserves lines, polylines, splines, circles, ellipses, arcs
- Automatic layer organization by entity type
- Y-axis flip for correct CAD coordinate system
- Compatible with AutoCAD, LibreCAD, QCAD, FreeCAD, SolidWorks
- Direct import into CAD applications for editing

### Batch Processing - `batch_svg_to_dxf.py`
**Process thousands of SVG files with parallel execution**:
- Multi-worker parallel processing (default: cpu_count // 4)
- Automatic pipeline: SVG → JSON → DXF
- Progress tracking with real-time status updates
- Error logging with detailed diagnostics
- Skip existing files to resume interrupted batches
- Optional intermediate JSON file retention

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
uv run svg_vector_extractor.py /path/to/image.svg
```

## Usage

### Single File Processing

#### SVG Vector Extraction

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

#### SVG to DXF Conversion

After extracting vectors from SVG, convert to DXF (CAD format):

```bash
# Convert a single JSON file to DXF
python svg_to_dxf.py outputs/json/drawing_vectors.json

# Specify output file
python svg_to_dxf.py outputs/json/drawing_vectors.json -o output.dxf

# Convert all JSON files in a directory
python svg_to_dxf.py --dir outputs/json

# Without layer organization
python svg_to_dxf.py input.json --no-layers

# Specify output directory
python svg_to_dxf.py --dir outputs/json --output-dir my_dxf_files

# With uv
uv run svg_to_dxf.py outputs/json/drawing_vectors.json

# Show help
python svg_to_dxf.py --help
```

### Batch Processing (Recommended for Multiple Files)

Process entire directories with parallel workers:

```bash
# Basic batch conversion (auto-detects worker count: cpu_count // 4)
python batch_svg_to_dxf.py /path/to/svg_directory -o /path/to/output

# Specify number of workers
python batch_svg_to_dxf.py ./svg_files -o ./dxf_output --workers 12

# Keep intermediate JSON files
python batch_svg_to_dxf.py ./svg_files -o ./dxf_output --keep-json

# Custom temp directory
python batch_svg_to_dxf.py ./input -o ./output --temp ./my_temp

# Quiet mode (only show summary)
python batch_svg_to_dxf.py ./input -o ./output --quiet

# Show help
python batch_svg_to_dxf.py --help
```

### Command-Line Arguments

**Vector Extraction (svg_vector_extractor.py):**
- **files**: One or more SVG file paths to process
- **--dir**: Directory containing SVG files (processes all *.svg files)
- **--output**: Output directory for results (default: outputs)

**DXF Conversion (svg_to_dxf.py):**
- **input**: JSON file with vector data from svg_vector_extractor.py
- **-o, --output**: Output DXF file path (default: same name as input)
- **--dir**: Process all JSON files in directory
- **--no-layers**: Do not organize entities by type into separate layers
- **--output-dir**: Output directory for DXF files (default: outputs/dxf)

**Batch Processing (batch_svg_to_dxf.py):**
- **input_dir**: Directory containing SVG files (required)
- **-o, --output**: Output directory for DXF files (required)
- **--temp**: Temporary directory for intermediate files (default: outputs/temp)
- **--workers**: Number of parallel workers (default: cpu_count // 4)
- **--keep-json**: Keep intermediate JSON files in output/json directory
- **--quiet**: Minimal output (only show summary)

## Output

The tools create various output directories:

**Vector Extraction:**
- `outputs/svg_analysis/` - Comprehensive visualizations
- `outputs/json/` - JSON exports of extracted vector data with coordinates

**DXF Conversion:**
- `outputs/dxf/` - DXF files ready for CAD applications (AutoCAD, LibreCAD, etc.)

**Batch Processing:**
- `<output_dir>/` - DXF files
- `<output_dir>/json/` - JSON files (if --keep-json specified)
- `<output_dir>/errors.log` - Error log with detailed diagnostics (if errors occurred)

## Features

### SVG Vector Extraction (True Vectors)
- **Path Elements**: Parse SVG `<path>` elements with d attribute
  - Lines (L, l commands)
  - Cubic Bézier curves (C, c commands) with 2 control points
  - Quadratic Bézier curves (Q, q commands) with 1 control point
  - Arcs (A, a commands) with proper radius, rotation, and sweep flags
  - Move (M, m) and Close (Z, z) operations
- **Shape Elements**: Extract basic SVG shapes
  - Rectangles (`<rect>`)
  - Circles (`<circle>`)
  - Ellipses (`<ellipse>`)
  - Lines (`<line>`)
  - Polylines and Polygons (`<polyline>`, `<polygon>`)
- **Accurate Coordinates**: Extract exact coordinates from SVG definition
- **Styling Info**: Capture fill, stroke, stroke-width attributes

### DXF Conversion (CAD Export)
- **Lines**: Direct line entity export
- **Polylines**: Multi-segment connected lines (closed or open)
- **Circles**: Perfect circle entities
- **Ellipses**: True ellipse entities with major/minor axes
- **Arcs**: Proper arc entities with center, radius, start/end angles
  - SVG endpoint to DXF center parameterization conversion
  - Correct Y-axis flip and sweep direction handling
  - Support for circular arcs (elliptical arcs approximated with polylines)
- **Splines**: Cubic Bézier curves converted to splines (degree 3)
- **Layer Organization**: Automatic grouping by entity type (LINES, CURVES, SHAPES, PATHS)
- **Coordinate System**: Automatic Y-axis flip for CAD coordinate system compatibility
- **Format**: AutoCAD R2010 DXF format (widely compatible)
- **Supported Applications**: AutoCAD, LibreCAD, QCAD, FreeCAD, SolidWorks, etc.

### Batch Processing
- **Parallel Execution**: Multi-worker processing for faster batch conversions
- **Smart Workers**: Default worker count = cpu_count // 4 for system stability
- **Progress Tracking**: Real-time status updates for each file
- **Error Handling**: Detailed error logging with stage information (extraction/conversion)
- **Resume Support**: Skip existing DXF files to resume interrupted batches
- **Statistics**: Completion summary with success/failure counts and timing

## Example Output

### SVG Extraction Output

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

  Segment 3 (operation: a):
    Arc:
      Start: (450.00, 200.00)
      Radius: (50.00, 50.00)
      Rotation: 0.0
      Arc flag: False
      Sweep flag: True
      End: (500.00, 250.00)
```

### DXF Conversion Output

```
==========================================================
Processing: drawing_vectors.json
==========================================================

Loading vector data from JSON...
  SVG height detected: 600.0
  Applying Y-axis flip for CAD coordinate system...

Converting vectors to DXF...
  Processing path 1/24...
  Processing path 2/24...
  ...

==========================================================
DXF CONVERSION STATISTICS
==========================================================
Lines:              156
Polylines:          45
Splines:            12
Circles:            8
Ellipses:           3
Arcs:               5
==========================================================
Total entities:     229
==========================================================

✓ DXF file saved: outputs/dxf/drawing.dxf
  Size: 45.23 KB
```

### Batch Processing Output

```
Using default workers: 8 (CPU count: 32, n // 4)

============================================================
SVG TO DXF BATCH CONVERSION PIPELINE
============================================================
Input directory:  /path/to/svg_files
Output directory: /path/to/dxf_output
Workers:          8 (CPU count: 32)
============================================================

[15:30:45] INFO: Found 5502 SVG file(s)
[15:30:45] INFO: Starting parallel processing with 8 workers...
[15:30:46] INFO: [1/5502] drawing_001.svg: OK 45.23KB
[15:30:46] INFO: [2/5502] drawing_002.svg: OK 38.15KB
[15:30:46] INFO: [3/5502] drawing_003.svg: FAIL [extraction]
[15:30:46] ERROR:    Exit code 1 | ParseError: mismatched tag: line 42
...

============================================================
BATCH CONVERSION SUMMARY
============================================================
Total files:        5502
Successful:         5489
Failed:             13
Skipped:            0
Workers:            8
Duration:           245.67 seconds
Avg time/file:      0.04 seconds
============================================================

ERRORS (13):
  • drawing_003.svg [extraction]: Exit code 1 | ParseError...
  • drawing_042.svg [extraction]: Exit code 1 | ParseError...
  ...

Error log saved: /path/to/dxf_output/errors.log

Output directory: /path/to/dxf_output
```

## Workflow Examples

### Single File Workflow

Complete workflow from SVG to DXF:

```bash
# Step 1: Extract vectors from SVG file
python svg_vector_extractor.py my_drawing.svg

# Step 2: Convert extracted vectors to DXF
python svg_to_dxf.py outputs/json/my_drawing_vectors.json

# Step 3: Open the DXF file in your CAD application
# The file will be at: outputs/dxf/my_drawing.dxf
```

### Batch Processing Workflow (Recommended)

Process entire directories in one command:

```bash
# One-step batch conversion (SVG → DXF)
python batch_svg_to_dxf.py /path/to/svg_directory -o /path/to/dxf_output --workers 12

# With JSON retention for debugging
python batch_svg_to_dxf.py /path/to/svg_directory -o /path/to/dxf_output --workers 12 --keep-json

# Check error log for failures
cat /path/to/dxf_output/errors.log
```

### Directory Processing (Manual)

Or process files step-by-step:

```bash
# Extract all SVG files in a directory
python svg_vector_extractor.py --dir drawings/

# Convert all JSON outputs to DXF
python svg_to_dxf.py --dir outputs/json
```

## Tips for Best Results

### For SVG Files:
1. **Use SVG when available** - Most accurate vector extraction
2. **Check SVG structure** - Tool supports standard SVG elements
3. **Works with any complexity** - Handles complex paths and shapes
4. **No quality requirements** - SVG is already vector data
5. **Batch processing** - Use batch_svg_to_dxf.py for directories with many files

### For CAD Applications:
1. **Check coordinate system** - Y-axis is automatically flipped for CAD compatibility
2. **Layer organization** - Entities grouped by type (LINES, CURVES, SHAPES, PATHS)
3. **Arc display** - Door swings and circular arcs render as proper arcs, not polylines
4. **Import settings** - Use AutoCAD R2010 or later compatibility mode

### Performance Optimization:
1. **Worker count** - Default (cpu_count // 4) is conservative; increase for faster systems
2. **Temp directory** - Use SSD location for faster I/O
3. **Resume batches** - Existing DXF files are automatically skipped
4. **Error handling** - Check errors.log for detailed diagnostics on failures

## Limitations

### SVG Extraction:
- Requires valid XML structure
- Complex transformations may need additional processing
- Group elements are flattened (hierarchy not preserved)

### DXF Conversion:
- Elliptical arcs are approximated with 20-point polylines
- Text elements not yet supported
- Complex gradients/patterns not preserved
- SVG transforms must be pre-applied

### Batch Processing:
- Large batches may require significant disk space for temp files
- Malformed SVG files will be logged but not crash the pipeline
- Progress display may be out of order due to parallel processing

## Troubleshooting

### Common Issues:

**"JSON output not created" errors:**
- Check SVG file validity (valid XML structure)
- Verify SVG contains actual vector elements (paths, shapes)
- Check error log for detailed parsing errors

**Arc direction reversed:**
- Fixed in latest version with proper Y-axis flip and sweep handling
- Update to ensure arcs render correctly in CAD applications

**Out of memory on large batches:**
- Reduce worker count: `--workers 4`
- Process in smaller batches
- Use `--quiet` to reduce console output overhead

**Slow processing:**
- Increase worker count: `--workers 16`
- Use SSD for temp directory
- Disable JSON retention: remove `--keep-json`
