#!/usr/bin/env python3
"""
Test suite for photo_date_updater.py

This module contains comprehensive tests for the photo date updater functionality,
including unit tests for individual functions and integration tests for the full workflow.
"""

import unittest
import tempfile
import os
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add the current directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from photo_date_updater import (
    is_supported_format,
    get_exif_date,
    update_creation_date,
    process_directory,
    SUPPORTED_FORMATS,
    EXIF_DATE_TAGS
)


class TestPhotoDateUpdater(unittest.TestCase):
    """Test cases for the photo date updater functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test files
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Remove temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_file(self, filename, content=b''):
        """Create a test file in the temp directory."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        self.test_files.append(file_path)
        return file_path

    def test_is_supported_format(self):
        """Test the is_supported_format function."""
        # Test supported formats
        for ext in SUPPORTED_FORMATS:
            filename = f"test{ext}"
            self.assertTrue(is_supported_format(filename), f"Should support {ext}")
            self.assertTrue(is_supported_format(filename.upper()), f"Should support {ext.upper()}")

        # Test unsupported formats
        unsupported_formats = ['.txt', '.pdf', '.doc', '.wmv', '.flv', '.webm']
        for ext in unsupported_formats:
            filename = f"test{ext}"
            self.assertFalse(is_supported_format(filename), f"Should not support {ext}")

    @patch('photo_date_updater.exifread.process_file')
    def test_get_exif_date_success(self, mock_process_file):
        """Test successful EXIF date extraction."""
        # Mock EXIF data with a valid date
        mock_tags = {
            'EXIF DateTimeOriginal': '2023:05:15 14:30:25',
            'EXIF DateTime': '2023:05:15 14:30:25'
        }
        mock_process_file.return_value = mock_tags

        test_file = self.create_test_file('test.jpg')
        result = get_exif_date(test_file)

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 5)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)
        self.assertEqual(result.second, 25)

    @patch('photo_date_updater.exifread.process_file')
    def test_get_exif_date_no_date_found(self, mock_process_file):
        """Test EXIF date extraction when no date is found."""
        # Mock EXIF data without date tags
        mock_tags = {
            'EXIF Make': 'Canon',
            'EXIF Model': 'EOS R5'
        }
        mock_process_file.return_value = mock_tags

        test_file = self.create_test_file('test.jpg')
        result = get_exif_date(test_file)

        self.assertIsNone(result)

    @patch('photo_date_updater.exifread.process_file')
    def test_get_exif_date_invalid_format(self, mock_process_file):
        """Test EXIF date extraction with invalid date format."""
        # Mock EXIF data with invalid date format
        mock_tags = {
            'EXIF DateTimeOriginal': 'invalid-date-format'
        }
        mock_process_file.return_value = mock_tags

        test_file = self.create_test_file('test.jpg')
        result = get_exif_date(test_file)

        self.assertIsNone(result)

    @patch('photo_date_updater.exifread.process_file')
    def test_get_exif_date_priority_order(self, mock_process_file):
        """Test that EXIF date tags are checked in priority order."""
        # Mock EXIF data with multiple date tags
        mock_tags = {
            'EXIF DateTime': '2023:05:15 14:30:25',  # Lower priority
            'EXIF DateTimeOriginal': '2023:06:20 10:15:30'  # Higher priority
        }
        mock_process_file.return_value = mock_tags

        test_file = self.create_test_file('test.jpg')
        result = get_exif_date(test_file)

        # Should use the higher priority tag (DateTimeOriginal)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 20)

    @patch('photo_date_updater.subprocess.run')
    def test_update_creation_date_success(self, mock_run):
        """Test successful creation date update."""
        # Mock successful SetFile command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        test_file = self.create_test_file('test.jpg')
        test_date = datetime(2023, 5, 15, 14, 30, 25)
        
        result = update_creation_date(test_file, test_date)

        self.assertTrue(result)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertEqual(call_args[0][0][0], 'SetFile')
        self.assertEqual(call_args[0][0][1], '-d')
        self.assertEqual(call_args[0][0][3], test_file)

    @patch('photo_date_updater.subprocess.run')
    def test_update_creation_date_failure(self, mock_run):
        """Test creation date update failure."""
        # Mock failed SetFile command
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result

        test_file = self.create_test_file('test.jpg')
        test_date = datetime(2023, 5, 15, 14, 30, 25)
        
        result = update_creation_date(test_file, test_date)

        self.assertFalse(result)

    def test_process_directory_nonexistent(self):
        """Test processing a non-existent directory."""
        with self.assertLogs(level='ERROR') as log:
            process_directory('/nonexistent/directory')
        
        self.assertTrue(any('Directory does not exist' in msg for msg in log.output))

    def test_process_directory_not_directory(self):
        """Test processing a file instead of a directory."""
        test_file = self.create_test_file('test.txt')
        
        with self.assertLogs(level='ERROR') as log:
            process_directory(test_file)
        
        self.assertTrue(any('Path is not a directory' in msg for msg in log.output))

    def test_process_directory_no_images(self):
        """Test processing a directory with no supported images."""
        # Create a directory with only text files
        test_file = self.create_test_file('test.txt')
        
        with self.assertLogs(level='INFO') as log:
            process_directory(self.temp_dir)
        
        self.assertTrue(any('No supported image files found' in msg for msg in log.output))

    @patch('photo_date_updater.get_exif_date')
    @patch('photo_date_updater.update_creation_date')
    def test_process_directory_with_images(self, mock_update, mock_get_exif):
        """Test processing a directory with images."""
        # Create test image files
        test_jpg = self.create_test_file('test1.jpg')
        test_png = self.create_test_file('test2.png')
        test_txt = self.create_test_file('test3.txt')  # Should be ignored

        # Mock EXIF date extraction
        test_date = datetime(2023, 5, 15, 14, 30, 25)
        mock_get_exif.return_value = test_date
        
        # Mock successful date update
        mock_update.return_value = True

        with self.assertLogs(level='INFO') as log:
            process_directory(self.temp_dir)

        # Should process 2 image files (jpg and png)
        self.assertEqual(mock_get_exif.call_count, 2)
        self.assertEqual(mock_update.call_count, 2)

        # Check that the correct files were processed
        processed_files = [str(call[0][0]) for call in mock_get_exif.call_args_list]
        self.assertIn(test_jpg, processed_files)
        self.assertIn(test_png, processed_files)
        self.assertNotIn(test_txt, processed_files)

    @patch('photo_date_updater.get_exif_date')
    @patch('photo_date_updater.update_creation_date')
    def test_process_directory_dry_run(self, mock_update, mock_get_exif):
        """Test processing in dry-run mode."""
        # Create test image file
        test_jpg = self.create_test_file('test.jpg')

        # Mock EXIF date extraction
        test_date = datetime(2023, 5, 15, 14, 30, 25)
        mock_get_exif.return_value = test_date

        with self.assertLogs(level='INFO') as log:
            process_directory(self.temp_dir, dry_run=True)

        # Should not call update_creation_date in dry-run mode
        mock_update.assert_not_called()

        # Should log dry-run message
        self.assertTrue(any('DRY RUN' in msg for msg in log.output))

    @patch('photo_date_updater.get_exif_date')
    def test_process_directory_no_exif_data(self, mock_get_exif):
        """Test processing images without EXIF data."""
        # Create test image file
        test_jpg = self.create_test_file('test.jpg')

        # Mock no EXIF date found
        mock_get_exif.return_value = None

        with self.assertLogs(level='WARNING') as log:
            process_directory(self.temp_dir)

        # Should log warning about no EXIF date
        self.assertTrue(any('no EXIF date found' in msg for msg in log.output))

    def test_supported_formats(self):
        """Test that all expected formats are supported."""
        expected_formats = {'.jpg', '.jpeg', '.tiff', '.tif', '.png', '.heic', '.heif', '.cr2', '.nef', '.arw', '.mp4', '.mov', '.avi', '.mkv'}
        self.assertEqual(SUPPORTED_FORMATS, expected_formats)

    def test_exif_date_tags_order(self):
        """Test that EXIF date tags are in the correct priority order."""
        expected_order = [
            'EXIF DateTimeOriginal',
            'EXIF DateTime',
            'Image DateTime',
            'EXIF SubSecTimeOriginal',
            'EXIF SubSecTime'
        ]
        self.assertEqual(EXIF_DATE_TAGS, expected_order)


class TestIntegration(unittest.TestCase):
    """Integration tests for the photo date updater."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []

    def tearDown(self):
        """Clean up test fixtures."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_image(self, filename, exif_date_str=None):
        """Create a test image file with optional EXIF data."""
        file_path = os.path.join(self.temp_dir, filename)
        
        # Create a minimal JPEG file structure
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
        
        with open(file_path, 'wb') as f:
            f.write(jpeg_header)
            f.write(b'\x00' * 1000)  # Add some content
        
        self.test_files.append(file_path)
        return file_path

    @patch('photo_date_updater.subprocess.run')
    def test_full_workflow(self, mock_run):
        """Test the complete workflow from directory processing to date update."""
        # Create test images
        test_jpg = self.create_test_image('test1.jpg')
        test_png = self.create_test_image('test2.png')
        
        # Mock successful SetFile command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Mock EXIF date extraction
        with patch('photo_date_updater.get_exif_date') as mock_get_exif:
            test_date = datetime(2023, 5, 15, 14, 30, 25)
            mock_get_exif.return_value = test_date

            with self.assertLogs(level='INFO') as log:
                process_directory(self.temp_dir)

            # Verify that SetFile was called for each image
            self.assertEqual(mock_run.call_count, 2)

            # Verify the correct date format was used
            for call in mock_run.call_args_list:
                args = call[0][0]
                self.assertEqual(args[0], 'SetFile')
                self.assertEqual(args[1], '-d')
                # Check date format: MM/DD/YYYY HH:MM:SS
                date_str = args[2]
                self.assertRegex(date_str, r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 