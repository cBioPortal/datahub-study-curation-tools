#!/usr/bin/env python3
"""
Unit tests for TimelineValidator duplicate SAMPLE_ID detection.

Tests verify that:
- Duplicate SAMPLE_IDs within the same track are detected and logged as errors
- SAMPLE_IDs can be reused across different tracks
- Unique SAMPLE_IDs pass validation
- Error messages include SAMPLE_ID value and track name
"""

import unittest
import sys
import os
from unittest.mock import MagicMock

# Mock MySQLdb before importing validateData
sys.modules['MySQLdb'] = MagicMock()

try:
    # When run as part of package
    from .validateData import TimelineValidator
except (ImportError, ValueError):
    # When run standalone
    sys.path.insert(0, os.path.dirname(__file__))
    from validateData import TimelineValidator


class MockLoggerAdapter:
    """Mock logger to capture validation errors."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.infos = []
    
    def error(self, msg, *args, **kwargs):
        """Capture error messages."""
        extra = kwargs.get('extra', {})
        self.errors.append({
            'message': msg,
            'extra': extra
        })
    
    def warning(self, msg, *args, **kwargs):
        """Capture warning messages."""
        self.warnings.append({'message': msg, 'extra': kwargs.get('extra', {})})
    
    def debug(self, msg, *args, **kwargs):
        """No-op for debug."""
        pass
    
    def info(self, msg, *args, **kwargs):
        """Capture info messages."""
        self.infos.append({'message': msg})
    
    @property
    def logger(self):
        """Provide logger attribute for compatibility."""
        return self


class TestTimelineValidatorDuplicateSampleID(unittest.TestCase):
    """Test TimelineValidator duplicate SAMPLE_ID detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create validator instance
        meta_dict = {'data_filename': 'test.txt'}
        self.validator = TimelineValidator(
            study_dir='.',
            meta_dict=meta_dict,
            portal_instance=None,
            logger=None,
            relaxed_mode=False,
            strict_maf_checks=False
        )
        
        # Override logger to capture messages
        self.mock_logger = MockLoggerAdapter()
        self.validator.logger = self.mock_logger
        
        # Set up header
        self.header = ['PATIENT_ID', 'START_DATE', 'STOP_DATE', 'EVENT_TYPE', 'SAMPLE_ID']
        self.validator.cols = self.header
        self.validator.numCols = len(self.header)
    
    def _check_line(self, line_num, patient_id, start_date, stop_date, event_type, sample_id):
        """Helper to check a timeline line."""
        self.validator.line_number = line_num
        line_data = [patient_id, start_date, stop_date, event_type, sample_id]
        self.validator.checkLine(line_data)
    
    def test_duplicate_sample_id_in_sample_acquisition_track(self):
        """Test that duplicate SAMPLE_IDs in SAMPLE_ACQUISITION track are detected."""
        # First occurrence
        self._check_line(2, 'patient1', '0', '100', 'SAMPLE_ACQUISITION', 'sample_A')
        self.assertEqual(len(self.mock_logger.errors), 0, "First occurrence should not error")
        
        # Duplicate in same track
        self._check_line(3, 'patient1', '100', '200', 'SAMPLE_ACQUISITION', 'sample_A')
        self.assertEqual(len(self.mock_logger.errors), 1, "Duplicate should be detected")
        
        error = self.mock_logger.errors[0]
        self.assertIn('Duplicate SAMPLE_ID', error['message'])
        self.assertEqual(error['extra']['line_number'], 3)
        self.assertEqual(error['extra']['column_number'], 5)  # SAMPLE_ID is 5th column
        self.assertIn('sample_A', error['extra']['cause'])
        self.assertIn('SAMPLE_ACQUISITION', error['extra']['cause'])
    
    def test_duplicate_sample_id_in_sequencing_track(self):
        """Test that duplicate SAMPLE_IDs in SEQUENCING track are detected."""
        # First occurrence
        self._check_line(2, 'patient1', '0', '100', 'SEQUENCING', 'sample_X')
        self.assertEqual(len(self.mock_logger.errors), 0)
        
        # Duplicate in same track
        self._check_line(3, 'patient1', '100', '200', 'SEQUENCING', 'sample_X')
        self.assertEqual(len(self.mock_logger.errors), 1)
        
        error = self.mock_logger.errors[0]
        self.assertIn('Duplicate SAMPLE_ID', error['message'])
        self.assertIn('sample_X', error['extra']['cause'])
        self.assertIn('SEQUENCING', error['extra']['cause'])
    
    def test_same_sample_id_in_different_tracks_allowed(self):
        """Test that same SAMPLE_ID can be used in different tracks."""
        # SAMPLE_ACQUISITION track
        self._check_line(2, 'patient1', '0', '100', 'SAMPLE_ACQUISITION', 'sample_A')
        self.assertEqual(len(self.mock_logger.errors), 0)
        
        # SEQUENCING track with same SAMPLE_ID
        self._check_line(3, 'patient1', '100', '200', 'SEQUENCING', 'sample_A')
        self.assertEqual(len(self.mock_logger.errors), 0, 
                        "Same SAMPLE_ID in different tracks should be allowed")
    
    def test_unique_sample_ids_pass_validation(self):
        """Test that unique SAMPLE_IDs pass validation."""
        self._check_line(2, 'patient1', '0', '100', 'SAMPLE_ACQUISITION', 'sample_A')
        self._check_line(3, 'patient1', '100', '200', 'SAMPLE_ACQUISITION', 'sample_B')
        self._check_line(4, 'patient1', '200', '300', 'SAMPLE_ACQUISITION', 'sample_C')
        self._check_line(5, 'patient1', '300', '400', 'SEQUENCING', 'sample_X')
        self._check_line(6, 'patient1', '400', '500', 'SEQUENCING', 'sample_Y')
        
        duplicate_errors = [e for e in self.mock_logger.errors 
                           if 'Duplicate SAMPLE_ID' in e['message']]
        self.assertEqual(len(duplicate_errors), 0, 
                        "Unique SAMPLE_IDs should not generate errors")
    
    def test_empty_sample_id_not_tracked(self):
        """Test that empty SAMPLE_ID values are not tracked."""
        # First with empty SAMPLE_ID
        self._check_line(2, 'patient1', '0', '100', 'SAMPLE_ACQUISITION', '')
        self.assertEqual(len(self.mock_logger.errors), 0)
        
        # Another with empty SAMPLE_ID in same track - should not error
        self._check_line(3, 'patient1', '100', '200', 'SAMPLE_ACQUISITION', '')
        self.assertEqual(len(self.mock_logger.errors), 0,
                        "Empty SAMPLE_IDs should not be tracked for duplicates")
    
    def test_complex_scenario_with_multiple_tracks(self):
        """Test complex scenario with multiple tracks and duplicate detection."""
        lines = [
            # SAMPLE_ACQUISITION track
            (2, 'patient1', '0', '100', 'SAMPLE_ACQUISITION', 'sample_A'),
            (3, 'patient1', '100', '200', 'SAMPLE_ACQUISITION', 'sample_B'),
            (4, 'patient1', '200', '300', 'SAMPLE_ACQUISITION', 'sample_A'),  # Dup in SAMPLE_ACQUISITION
            # SEQUENCING track
            (5, 'patient1', '300', '400', 'SEQUENCING', 'sample_A'),  # OK: different track
            (6, 'patient1', '400', '500', 'SEQUENCING', 'sample_C'),
            (7, 'patient1', '500', '600', 'SEQUENCING', 'sample_A'),  # Dup in SEQUENCING
        ]
        
        for line_num, patient_id, start_date, stop_date, event_type, sample_id in lines:
            self._check_line(line_num, patient_id, start_date, stop_date, event_type, sample_id)
        
        duplicate_errors = [e for e in self.mock_logger.errors 
                           if 'Duplicate SAMPLE_ID' in e['message']]
        self.assertEqual(len(duplicate_errors), 2, "Should detect 2 duplicates")
        
        # First duplicate at line 4
        self.assertEqual(duplicate_errors[0]['extra']['line_number'], 4)
        self.assertIn('SAMPLE_ACQUISITION', duplicate_errors[0]['extra']['cause'])
        
        # Second duplicate at line 7
        self.assertEqual(duplicate_errors[1]['extra']['line_number'], 7)
        self.assertIn('SEQUENCING', duplicate_errors[1]['extra']['cause'])
    
    def test_no_sample_id_column(self):
        """Test validation works when SAMPLE_ID column is not present."""
        # Change header to exclude SAMPLE_ID
        self.validator.cols = ['PATIENT_ID', 'START_DATE', 'STOP_DATE', 'EVENT_TYPE']
        self.validator.numCols = 4
        
        # Should not raise an error even with duplicate values in 4th column
        line_data = ['patient1', '0', '100', 'TRACK_A']
        self.validator.line_number = 2
        self.validator.checkLine(line_data)
        
        line_data = ['patient1', '100', '200', 'TRACK_A']
        self.validator.line_number = 3
        self.validator.checkLine(line_data)
        
        duplicate_errors = [e for e in self.mock_logger.errors 
                           if 'Duplicate SAMPLE_ID' in e['message']]
        self.assertEqual(len(duplicate_errors), 0, 
                        "Should not check for duplicates without SAMPLE_ID column")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

