#!/usr/bin/env python3
"""
Metadata Inspector Tool

This script inspects all metadata tags in image and video files to help
identify which tags contain date information for different file types.

Usage:
    python3 inspect_metadata.py <file_path>
    python3 inspect_metadata.py <directory_path> --recursive
"""

import os
import sys
import argparse
from pathlib import Path
import exifread
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supported formats to inspect
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.tiff', '.tif', '.png', '.heic', '.heif', '.cr2', '.nef', '.arw', '.mp4', '.mov', '.avi', '.mkv'}

def is_supported_format(file_path):
    """Check if the file is a supported format."""
    return Path(file_path).suffix.lower() in SUPPORTED_FORMATS

def inspect_file_metadata(file_path):
    """
    Inspect all metadata tags in a file and return them organized by category.
    """
    try:
        logger.debug(f"Attempting to read metadata from: {file_path}")
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=True)
        logger.debug(f"Opened: {file_path}")
        
        if not tags:
            logger.warning(f"No metadata tags found in {file_path}")
            return None
        
        # Organize tags by category
        date_tags = []
        camera_tags = []
        video_tags = []
        other_tags = []
        
        for tag, value in tags.items():
            tag_str = str(tag)
            value_str = str(value)
            
            # Categorize tags
            if any(date_word in tag_str.lower() for date_word in ['date', 'time', 'create', 'original']):
                date_tags.append((tag_str, value_str))
            elif any(camera_word in tag_str.lower() for camera_word in ['make', 'model', 'lens', 'focal', 'aperture', 'iso', 'exposure']):
                camera_tags.append((tag_str, value_str))
            elif any(video_word in tag_str.lower() for video_word in ['quicktime', 'video', 'audio', 'codec', 'bitrate', 'frame']):
                video_tags.append((tag_str, value_str))
            else:
                other_tags.append((tag_str, value_str))
        
        return {
            'date_tags': sorted(date_tags),
            'camera_tags': sorted(camera_tags),
            'video_tags': sorted(video_tags),
            'other_tags': sorted(other_tags),
            'total_tags': len(tags)
        }
        
    except Exception as e:
        error_msg = str(e)
        if "File format not recognized" in error_msg:
            logger.warning(f"File format not recognized by exifread: {file_path}")
            logger.debug(f"Full error: {error_msg}")
        else:
            logger.error(f"Error reading metadata from {file_path}: {error_msg}")
        return None

def print_metadata_summary(file_path, metadata):
    """Print a formatted summary of the metadata."""
    if not metadata:
        return
    
    print(f"\n{'='*80}")
    print(f"METADATA INSPECTION: {file_path}")
    print(f"{'='*80}")
    print(f"Total tags found: {metadata['total_tags']}")
    
    # Date tags
    if metadata['date_tags']:
        print(f"\n📅 DATE/TIME TAGS ({len(metadata['date_tags'])}):")
        print("-" * 40)
        for tag, value in metadata['date_tags']:
            print(f"  {tag}: {value}")
    else:
        print(f"\n📅 DATE/TIME TAGS: None found")
    
    # Camera tags
    if metadata['camera_tags']:
        print(f"\n📷 CAMERA TAGS ({len(metadata['camera_tags'])}):")
        print("-" * 40)
        for tag, value in metadata['camera_tags']:
            print(f"  {tag}: {value}")
    else:
        print(f"\n📷 CAMERA TAGS: None found")
    
    # Video tags
    if metadata['video_tags']:
        print(f"\n🎥 VIDEO TAGS ({len(metadata['video_tags'])}):")
        print("-" * 40)
        for tag, value in metadata['video_tags']:
            print(f"  {tag}: {value}")
    else:
        print(f"\n🎥 VIDEO TAGS: None found")
    
    # Other tags
    if metadata['other_tags']:
        print(f"\n📋 OTHER TAGS ({len(metadata['other_tags'])}):")
        print("-" * 40)
        for tag, value in metadata['other_tags'][:10]:  # Show first 10
            print(f"  {tag}: {value}")
        if len(metadata['other_tags']) > 10:
            print(f"  ... and {len(metadata['other_tags']) - 10} more tags")
    else:
        print(f"\n📋 OTHER TAGS: None found")

def inspect_directory(directory_path, recursive=False):
    """Inspect all supported files in a directory."""
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory_path}")
        return
    
    if not directory.is_dir():
        logger.error(f"Path is not a directory: {directory_path}")
        return
    
    # Find all supported files
    if recursive:
        files = list(directory.rglob('*'))
    else:
        files = list(directory.glob('*'))
    
    supported_files = [f for f in files if f.is_file() and is_supported_format(f)]
    
    if not supported_files:
        logger.info(f"No supported files found in {directory_path}")
        return
    
    logger.info(f"Found {len(supported_files)} supported files to inspect")
    
    for file_path in supported_files:
        metadata = inspect_file_metadata(file_path)
        print_metadata_summary(file_path, metadata)

def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Inspect metadata tags in image and video files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 inspect_metadata.py photo.jpg
  python3 inspect_metadata.py video.mp4
  python3 inspect_metadata.py /path/to/photos --recursive
        """
    )
    
    parser.add_argument(
        'path',
        help='File or directory to inspect'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Recursively inspect directories'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    path = Path(args.path)
    
    if path.is_file():
        # Inspect single file
        if not is_supported_format(path):
            logger.error(f"Unsupported file format: {path}")
            sys.exit(1)
        
        metadata = inspect_file_metadata(path)
        print_metadata_summary(path, metadata)
        
    elif path.is_dir():
        # Inspect directory
        inspect_directory(path, args.recursive)
        
    else:
        logger.error(f"Path does not exist: {path}")
        sys.exit(1)

if __name__ == '__main__':
    main() 