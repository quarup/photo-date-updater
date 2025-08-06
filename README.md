# Photo Date Updater for macOS

A Python script that updates the metadata creation date of photo files in a directory to match their EXIF date. This is particularly useful for organizing photos that have been copied or moved, ensuring their creation dates reflect when they were actually taken.

## Features

- Updates file creation dates to match EXIF metadata
- Supports multiple image formats (JPG, PNG, TIFF, HEIC, RAW formats)
- Recursive directory processing
- Dry-run mode for testing
- Comprehensive logging
- macOS-specific implementation using SetFile

## Supported Formats

### Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png) - Note: PNG files typically don't contain EXIF metadata
- TIFF (.tiff, .tif)
- HEIC/HEIF (.heic, .heif)
- RAW formats (.cr2, .nef, .arw)

### Video Formats
- MP4 (.mp4)
- MOV (.mov)
- AVI (.avi)
- MKV (.mkv)

## Requirements

- macOS (uses SetFile command)
- Python 3.6+
- exifread library

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

## Testing

Run the test suite to verify everything works correctly:

```bash
# Run all tests
python3 run_tests.py

# Or run tests directly
python3 -m unittest test_photo_date_updater.py -v
```

## Usage

### Basic Usage

```bash
python3 photo_date_updater.py /path/to/your/photos
```

### Dry Run (Test Mode)

To see what changes would be made without actually making them:

```bash
python3 photo_date_updater.py /path/to/your/photos --dry-run
```

### Verbose Logging

For more detailed output:

```bash
python3 photo_date_updater.py /path/to/your/photos --verbose
```

### Examples

```bash
# Update photos in your Pictures folder
python3 photo_date_updater.py ~/Pictures

# Test run on a specific album
python3 photo_date_updater.py ~/Pictures/Vacation2023 --dry-run

# Verbose output for debugging
python3 photo_date_updater.py ~/Pictures --verbose
```

## Metadata Inspection Tool

Use the included metadata inspector to see what date tags are available in your files:

```bash
# Inspect a single file
python3 inspect_metadata.py photo.jpg
python3 inspect_metadata.py video.mp4

# Inspect all files in a directory
python3 inspect_metadata.py /path/to/photos --recursive
```

This tool will show you all available metadata tags organized by category (date/time, camera, video, etc.), helping you understand what date information is available in your files.

## How It Works

1. **EXIF Date Extraction**: The script reads EXIF metadata from image files and extracts the date when the photo was taken. It checks multiple EXIF date fields in order of preference:
   - EXIF DateTimeOriginal (most accurate)
   - EXIF DateTime
   - Image DateTime
   - EXIF SubSecTimeOriginal
   - EXIF SubSecTime

2. **Creation Date Update**: Uses macOS's `SetFile` command to update the file's creation date to match the EXIF date.

3. **Recursive Processing**: Processes all supported image files in the specified directory and its subdirectories.

## Safety Features

- **Dry-run mode**: Test what changes would be made without making them
- **Comprehensive logging**: See exactly what's happening with each file
- **Error handling**: Gracefully handles files without EXIF data or other issues
- **Format validation**: Only processes supported image formats

## Output

The script provides detailed logging including:
- Number of files found
- Files successfully updated
- Files skipped (no EXIF date found)
- Errors encountered
- Summary statistics

## Troubleshooting

### "SetFile command not found"
This script requires macOS. The SetFile command is part of macOS Developer Tools.

### "No valid EXIF date found"
Some images may not have EXIF metadata, especially if they've been edited or converted. These files will be skipped.

### Permission errors
Make sure you have write permissions for the files you're trying to update.

## License

This project is open source. Feel free to modify and distribute as needed.

## Testing

The project includes comprehensive tests covering:

- **Unit Tests**: Individual function testing with mocked dependencies
- **Integration Tests**: End-to-end workflow testing
- **Edge Cases**: Error handling, invalid inputs, missing data
- **Format Validation**: Supported vs unsupported file types
- **EXIF Processing**: Date extraction and priority order
- **macOS Integration**: SetFile command testing

### Test Coverage

- ✅ File format detection
- ✅ EXIF date extraction with priority order
- ✅ Creation date updates using SetFile
- ✅ Directory processing and recursion
- ✅ Dry-run mode functionality
- ✅ Error handling and logging
- ✅ Command line argument parsing
- ✅ macOS platform detection

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool. 