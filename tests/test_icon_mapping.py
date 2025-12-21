"""
Property-based tests for Subject Icon Mapping Consistency

Feature: study-page-improvements, Property 1: Subject Icon Mapping Consistency
Validates: Requirements 1.1
"""
import pytest
from hypothesis import given, strategies as st, settings
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Subject, ICONOIR_SUBJECT_ICONS


# Get all default subject names
DEFAULT_SUBJECT_NAMES = [subj['name'] for subj in Subject.DEFAULT_SUBJECTS]


@settings(max_examples=100)
@given(st.sampled_from(DEFAULT_SUBJECT_NAMES))
def test_property_1_subject_icon_mapping_consistency(subject_name):
    """
    Property 1: Subject Icon Mapping Consistency
    
    *For any* default subject in the system, the subject's Iconoir icon name 
    should match the predefined mapping (e.g., Mathematics → calculator, Science → flask).
    
    **Validates: Requirements 1.1**
    """
    # Find the subject in DEFAULT_SUBJECTS
    subject_data = next(
        (s for s in Subject.DEFAULT_SUBJECTS if s['name'] == subject_name), 
        None
    )
    
    assert subject_data is not None, f"Subject {subject_name} not found in DEFAULT_SUBJECTS"
    
    # Get the iconoir icon from the subject data
    iconoir_from_default = subject_data.get('iconoir')
    
    # Get the expected iconoir icon from the mapping
    expected_iconoir = ICONOIR_SUBJECT_ICONS.get(subject_name)
    
    # Verify the mapping is consistent
    assert iconoir_from_default == expected_iconoir, (
        f"Icon mapping mismatch for {subject_name}: "
        f"DEFAULT_SUBJECTS has '{iconoir_from_default}', "
        f"ICONOIR_SUBJECT_ICONS has '{expected_iconoir}'"
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
