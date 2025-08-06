#!/usr/bin/env python3
"""
Photo Date Updater Script for macOS

This script updates the metadata creation date of photo files in a directory
to match their EXIF date. It supports common image formats and handles
various EXIF date fields.

Usage:
    python photo_date_updater.py <directory_path>
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import exifread
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supported image and video formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.tiff', '.tif', '.png', '.heic', '.heif', '.cr2', '.nef', '.arw', '.mp4', '.mov', '.avi', '.mkv'}

# EXIF date tags to check in order of preference
EXIF_DATE_TAGS = [
    'EXIF DateTimeOriginal',
    'EXIF DateTime',
    'Image DateTime',
    'EXIF SubSecTimeOriginal',
    'EXIF SubSecTime'
]

# Video metadata tags to check
VIDEO_DATE_TAGS = [
    'QuickTime CreateDate',
    'QuickTime DateTimeOriginal',
    'QuickTime DateTime',
    'QuickTime CreationDate'
]

def is_supported_format(file_path):
    """Check if the file is a supported image format."""
    return Path(file_path).suffix.lower() in SUPPORTED_FORMATS

def get_exif_date(file_path):
    """
    Extract the date from EXIF metadata of an image or video file.
    Returns a datetime object or None if no date found.
    """
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        file_ext = Path(file_path).suffix.lower()
        
        # For video files, check video metadata tags first
        if file_ext in {'.mp4', '.mov', '.avi', '.mkv'}:
            for tag in VIDEO_DATE_TAGS:
                if tag in tags:
                    date_str = str(tags[tag])
                    try:
                        # Video dates might be in different formats
                        # Try common video date formats
                        for fmt in ['%Y:%m:%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S']:
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                        logger.warning(f"Could not parse video date '{date_str}' from {file_path}")
                    except Exception:
                        continue
        
        # For image files, check EXIF tags
        for tag in EXIF_DATE_TAGS:
            if tag in tags:
                date_str = str(tags[tag])
                try:
                    # Parse the date string (format: YYYY:MM:DD HH:MM:SS)
                    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    logger.warning(f"Could not parse date '{date_str}' from {file_path}")
                    continue
        
        # For PNG files, provide specific message
        if file_ext == '.png':
            logger.warning(f"No EXIF date found in PNG file {file_path} - PNG files typically don't contain EXIF metadata")
        else:
            logger.warning(f"No valid date metadata found in {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error reading metadata from {file_path}: {e}")
        return None

def update_creation_date(file_path, date):
    """
    Update the creation date of a file using macOS's SetFile command.
    """
    try:
        # Format date for SetFile command (MM/DD/YYYY HH:MM:SS)
        date_str = date.strftime('%m/%d/%Y %H:%M:%S')
        
        # Use SetFile to update creation date
        cmd = ['SetFile', '-d', date_str, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Updated creation date for {file_path} to {date_str}")
            return True
        else:
            logger.error(f"Failed to update {file_path}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating creation date for {file_path}: {e}")
        return False

def process_directory(directory_path, dry_run=False):
    """
    Process all supported image files in the directory and update their creation dates.
    
    Args:
        directory_path (str): Path to the directory containing images
        dry_run (bool): If True, only show what would be done without making changes
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory_path}")
        return
    
    if not directory.is_dir():
        logger.error(f"Path is not a directory: {directory_path}")
        return
    
    # Find all supported image files
    image_files = []
    for file_path in directory.rglob('*'):
        if file_path.is_file() and is_supported_format(file_path):
            image_files.append(file_path)
    
    if not image_files:
        logger.info(f"No supported image files found in {directory_path}")
        return
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in image_files:
        logger.info(f"Processing: {file_path}")
        
        # Get EXIF date
        exif_date = get_exif_date(file_path)
        
        if exif_date is None:
            logger.warning(f"Skipping {file_path} - no EXIF date found")
            skipped_count += 1
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update {file_path} creation date to {exif_date}")
            updated_count += 1
        else:
            # Update the creation date
            if update_creation_date(file_path, exif_date):
                updated_count += 1
            else:
                error_count += 1
    
    # Summary
    logger.info(f"\nProcessing complete:")
    logger.info(f"  - Files updated: {updated_count}")
    logger.info(f"  - Files skipped: {skipped_count}")
    logger.info(f"  - Errors: {error_count}")

def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Update photo file creation dates to match EXIF dates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python photo_date_updater.py /path/to/photos
  python photo_date_updater.py /path/to/photos --dry-run
        """
    )
    
    parser.add_argument(
        'directory',
        help='Directory containing photo files to process'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.dry_run:
        logger.info("Running in dry-run mode - no changes will be made")
    
    # Check if we're on macOS
    if sys.platform != 'darwin':
        logger.error("This script is designed for macOS only")
        sys.exit(1)
    
    # Check if SetFile command is available
    try:
        subprocess.run(['SetFile', '-h'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("SetFile command not found. This script requires macOS.")
        sys.exit(1)
    
    # Process the directory
    process_directory(args.directory, args.dry_run)

if __name__ == '__main__':
    main() 