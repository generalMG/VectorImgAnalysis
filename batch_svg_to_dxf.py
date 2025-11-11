#!/usr/bin/env python3
"""
Batch SVG to DXF Converter Pipeline

Processes all SVG files in a directory:
1. Extracts vectors from SVG files
2. Converts to DXF format
3. Saves output to specified directory

Supports parallel processing for faster batch conversions.
"""

import sys
import argparse
import os
from pathlib import Path
import json
import subprocess
import shutil
from datetime import datetime
from multiprocessing import Pool, Manager, cpu_count
from functools import partial


def process_single_file_worker(svg_file, output_dir, temp_dir, keep_json):
    """
    Process a single SVG file (worker function for multiprocessing)

    Args:
        svg_file: Path to SVG file
        output_dir: Output directory path
        temp_dir: Temp directory path
        keep_json: Whether to keep JSON files

    Returns:
        dict with result information
    """
    result = {
        'file': svg_file.name,
        'success': False,
        'skipped': False,
        'error': None,
        'dxf_size': 0,
        'stage': None
    }

    try:
        # Check if already exists
        dxf_output = output_dir / f"{svg_file.stem}.dxf"
        if dxf_output.exists():
            result['skipped'] = True
            result['success'] = True
            return result

        # Step 1: Extract vectors
        result['stage'] = 'extraction'
        # svg_vector_extractor.py saves to <output>/json/ subdirectory
        json_output = temp_dir / 'json' / f"{svg_file.stem}_vectors.json"

        cmd = [
            sys.executable,
            'svg_vector_extractor.py',
            str(svg_file),
            '--output', str(temp_dir)
        ]

        extraction_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if extraction_result.returncode != 0:
            # Capture more error details
            stderr = extraction_result.stderr.strip()
            stdout = extraction_result.stdout.strip()
            error_msg = f"Exit code {extraction_result.returncode}"
            if stderr:
                error_msg += f" | {stderr[-500:]}"  # Last 500 chars of stderr
            elif stdout:
                error_msg += f" | {stdout[-500:]}"  # Last 500 chars of stdout
            raise Exception(f"Extraction failed: {error_msg}")

        if not json_output.exists():
            # More detailed error about what happened
            stderr = extraction_result.stderr.strip()
            stdout = extraction_result.stdout.strip()
            error_msg = "JSON not created"
            if stderr:
                error_msg += f" | stderr: {stderr[-300:]}"
            if stdout:
                error_msg += f" | stdout: {stdout[-300:]}"
            raise Exception(error_msg)

        # Step 2: Convert to DXF
        result['stage'] = 'conversion'
        cmd = [
            sys.executable,
            'svg_to_dxf.py',
            str(json_output),
            '-o', str(dxf_output)
        ]

        conversion_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if conversion_result.returncode != 0:
            # Capture more error details
            stderr = conversion_result.stderr.strip()
            stdout = conversion_result.stdout.strip()
            error_msg = f"Exit code {conversion_result.returncode}"
            if stderr:
                error_msg += f" | {stderr[-500:]}"
            elif stdout:
                error_msg += f" | {stdout[-500:]}"
            raise Exception(f"Conversion failed: {error_msg}")

        if not dxf_output.exists():
            # More detailed error about what happened
            stderr = conversion_result.stderr.strip()
            stdout = conversion_result.stdout.strip()
            error_msg = "DXF not created"
            if stderr:
                error_msg += f" | stderr: {stderr[-300:]}"
            if stdout:
                error_msg += f" | stdout: {stdout[-300:]}"
            raise Exception(error_msg)

        # Copy JSON if keeping
        if keep_json:
            json_dest = output_dir / 'json' / json_output.name
            json_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(json_output, json_dest)

        # Clean up temp JSON
        try:
            json_output.unlink()
        except:
            pass

        # Get file size
        result['dxf_size'] = dxf_output.stat().st_size / 1024  # KB
        result['success'] = True

    except Exception as e:
        result['error'] = str(e)

    return result


class SVGToDXFPipeline:
    """Batch conversion pipeline for SVG to DXF with parallel processing"""

    def __init__(self, input_dir, output_dir, temp_dir='outputs/temp', keep_json=False, verbose=True, workers=None):
        """
        Initialize pipeline

        Args:
            input_dir: Directory containing SVG files
            output_dir: Directory for DXF output
            temp_dir: Temporary directory for JSON files
            keep_json: Keep intermediate JSON files
            verbose: Print detailed progress
            workers: Number of parallel workers (default: cpu_count() // 4)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.keep_json = keep_json
        self.verbose = verbose

        # Determine worker count
        if workers is None:
            total_cpus = cpu_count()
            self.workers = max(1, total_cpus // 4)  # Default: n // 4 for safety
        else:
            self.workers = max(1, workers)

        # Statistics
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }

        # Error log
        self.errors = []

    def log(self, message, level='INFO'):
        """Log message if verbose"""
        if self.verbose:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {level}: {message}")

    def setup_directories(self):
        """Create necessary directories"""
        self.log(f"Setting up directories...")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"  Output directory: {self.output_dir.absolute()}")

        # Create temp directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"  Temp directory: {self.temp_dir.absolute()}")

        if self.keep_json:
            json_dir = self.output_dir / 'json'
            json_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"  JSON directory: {json_dir.absolute()}")

    def find_svg_files(self):
        """Find all SVG files in input directory"""
        svg_files = list(self.input_dir.glob('*.svg'))
        self.stats['total_files'] = len(svg_files)

        if not svg_files:
            self.log(f"No SVG files found in {self.input_dir}", 'WARNING')
            return []

        self.log(f"Found {len(svg_files)} SVG file(s)")
        return sorted(svg_files)

    def cleanup(self):
        """Clean up temporary files"""
        if not self.keep_json:
            try:
                shutil.rmtree(self.temp_dir)
                self.log(f"Cleaned up temporary files")
            except Exception as e:
                self.log(f"Failed to cleanup temp directory: {e}", 'WARNING')

    def print_summary(self):
        """Print pipeline execution summary"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        print(f"\n{'='*60}")
        print(f"BATCH CONVERSION SUMMARY")
        print(f"{'='*60}")
        print(f"Total files:        {self.stats['total_files']}")
        print(f"Successful:         {self.stats['successful']}")
        print(f"Failed:             {self.stats['failed']}")
        print(f"Skipped:            {self.stats['skipped']}")
        print(f"Workers:            {self.workers}")
        print(f"Duration:           {duration:.2f} seconds")
        if self.stats['total_files'] > 0:
            print(f"Avg time/file:      {duration/self.stats['total_files']:.2f} seconds")
        print(f"{'='*60}")

        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                stage_info = f"[{error.get('stage', 'unknown')}]"
                error_msg = error['error'][:100] if len(error['error']) > 100 else error['error']
                print(f"  • {error['file']} {stage_info}: {error_msg}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")

            # Optionally save error log to file
            error_log = self.output_dir / 'errors.log'
            try:
                with open(error_log, 'w') as f:
                    f.write(f"SVG to DXF Batch Conversion Errors\n")
                    f.write(f"{'='*60}\n\n")
                    for error in self.errors:
                        f.write(f"File: {error['file']}\n")
                        f.write(f"Stage: {error.get('stage', 'unknown')}\n")
                        f.write(f"Error: {error['error']}\n")
                        f.write(f"{'-'*60}\n\n")
                print(f"\nError log saved: {error_log}")
            except Exception as e:
                print(f"Warning: Could not save error log: {e}")

        print(f"\nOutput directory: {self.output_dir.absolute()}")

        if self.keep_json:
            print(f"JSON directory:   {(self.output_dir / 'json').absolute()}")

    def run(self):
        """Execute the pipeline with parallel processing"""
        self.stats['start_time'] = datetime.now()

        print(f"\n{'='*60}")
        print(f"SVG TO DXF BATCH CONVERSION PIPELINE")
        print(f"{'='*60}")
        print(f"Input directory:  {self.input_dir.absolute()}")
        print(f"Output directory: {self.output_dir.absolute()}")
        print(f"Workers:          {self.workers} (CPU count: {cpu_count()})")
        print(f"{'='*60}\n")

        # Setup
        self.setup_directories()

        # Find SVG files
        svg_files = self.find_svg_files()
        if not svg_files:
            return False

        # Create worker function with fixed parameters
        worker_func = partial(
            process_single_file_worker,
            output_dir=self.output_dir,
            temp_dir=self.temp_dir,
            keep_json=self.keep_json
        )

        # Process files in parallel
        self.log(f"Starting parallel processing with {self.workers} workers...")

        try:
            with Pool(processes=self.workers) as pool:
                results = []
                for i, result in enumerate(pool.imap_unordered(worker_func, svg_files), 1):
                    results.append(result)

                    # Update statistics
                    if result['skipped']:
                        self.stats['skipped'] += 1
                    elif result['success']:
                        self.stats['successful'] += 1
                    else:
                        self.stats['failed'] += 1
                        self.errors.append({
                            'file': result['file'],
                            'stage': result.get('stage', 'unknown'),
                            'error': result['error']
                        })

                    # Print progress
                    if self.verbose:
                        status = "SKIP" if result['skipped'] else ("OK" if result['success'] else "FAIL")
                        size_str = f"{result['dxf_size']:.2f}KB" if result['dxf_size'] > 0 else ""
                        stage_str = f" [{result.get('stage', 'unknown')}]" if not result['success'] and not result['skipped'] else ""
                        self.log(f"[{i}/{len(svg_files)}] {result['file']}: {status}{stage_str} {size_str}")
                        if result['error'] and not result['skipped']:
                            # Show more error details
                            error_display = result['error'][:200] if len(result['error']) > 200 else result['error']
                            self.log(f"    {error_display}", 'ERROR')

        except KeyboardInterrupt:
            self.log("\nPipeline interrupted by user", 'WARNING')
            return False
        except Exception as e:
            self.log(f"Pipeline error: {e}", 'ERROR')
            return False

        # Cleanup
        self.cleanup()

        # Summary
        self.stats['end_time'] = datetime.now()
        self.print_summary()

        return self.stats['failed'] == 0


def main():
    parser = argparse.ArgumentParser(
        description='Batch convert SVG files to DXF format with parallel processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Convert all SVGs in a directory (uses cpu_count // 4 workers)
  python batch_svg_to_dxf.py /path/to/svgs -o /path/to/output

  # Specify number of workers
  python batch_svg_to_dxf.py ./svg_files -o ./dxf_output --workers 8

  # Keep intermediate JSON files
  python batch_svg_to_dxf.py ./svg_files -o ./dxf_output --keep-json

  # Quiet mode (minimal output)
  python batch_svg_to_dxf.py ./input -o ./output --quiet

  # Custom temp directory
  python batch_svg_to_dxf.py ./input -o ./output --temp ./my_temp
        '''
    )

    parser.add_argument(
        'input_dir',
        help='Directory containing SVG files'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output directory for DXF files'
    )

    parser.add_argument(
        '--temp',
        default='outputs/temp',
        help='Temporary directory for intermediate files (default: outputs/temp)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: cpu_count // 4 for safety)'
    )

    parser.add_argument(
        '--keep-json',
        action='store_true',
        help='Keep intermediate JSON files in output/json directory'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output (only show summary)'
    )

    args = parser.parse_args()

    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"✗ Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)

    if not input_dir.is_dir():
        print(f"✗ Error: '{args.input_dir}' is not a directory")
        sys.exit(1)

    # Show worker count info
    if args.workers is None:
        total_cpus = cpu_count()
        default_workers = max(1, total_cpus // 4)
        print(f"Using default workers: {default_workers} (CPU count: {total_cpus}, n // 4)")
    else:
        print(f"Using specified workers: {args.workers} (CPU count: {cpu_count()})")

    # Run pipeline
    pipeline = SVGToDXFPipeline(
        input_dir=args.input_dir,
        output_dir=args.output,
        temp_dir=args.temp,
        keep_json=args.keep_json,
        verbose=not args.quiet,
        workers=args.workers
    )

    success = pipeline.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
