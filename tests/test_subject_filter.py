"""
Property-based tests for Subject Filter Correctness

Feature: study-page-improvements, Property 5: Subject Filter Correctness
Validates: Requirements 3.2, 3.3
"""
import pytest
from hypothesis import given, strategies as st, settings
from dataclasses import dataclass
from typing import List, Set, Optional


@dataclass
class StudyFile:
    """Represents a study file with an optional subject"""
    file_id: int
    subject_id: Optional[int] = None


class SubjectFilterState:
    """
    Simulates the subject filter logic from the frontend.
    This mirrors the filterState JavaScript object behavior.
    """
    
    def __init__(self):
        self.selected_filters: List[str] = ['all']
    
    def toggle(self, filter_id: str) -> None:
        """Toggle a filter selection"""
        if filter_id == 'all':
            # Reset to show all
            self.selected_filters = ['all']
        else:
            # Remove 'all' if selecting specific filter
            if 'all' in self.selected_filters:
                self.selected_filters.remove('all')
            
            # Toggle the specific filter
            if filter_id in self.selected_filters:
                self.selected_filters.remove(filter_id)
                # If no filters left, reset to 'all'
                if len(self.selected_filters) == 0:
                    self.selected_filters = ['all']
            else:
                self.selected_filters.append(filter_id)
    
    def apply(self, files: List[StudyFile]) -> List[StudyFile]:
        """Apply filters and return visible files"""
        if 'all' in self.selected_filters:
            return files
        
        visible_files = []
        for file in files:
            subject_id_str = str(file.subject_id) if file.subject_id else ''
            if subject_id_str in self.selected_filters:
                visible_files.append(file)
        
        return visible_files
    
    def reset(self) -> None:
        """Reset filters to show all"""
        self.selected_filters = ['all']


# Strategy to generate study files with subjects
@st.composite
def study_files_strategy(draw):
    """Generate a list of study files with random subject assignments"""
    num_files = draw(st.integers(min_value=0, max_value=20))
    num_subjects = draw(st.integers(min_value=1, max_value=12))
    
    files = []
    for i in range(num_files):
        # Some files may have no subject (None)
        has_subject = draw(st.booleans())
        subject_id = draw(st.integers(min_value=1, max_value=num_subjects)) if has_subject else None
        files.append(StudyFile(file_id=i + 1, subject_id=subject_id))
    
    return files, num_subjects


@settings(max_examples=100)
@given(
    data=study_files_strategy(),
    filter_id=st.integers(min_value=1, max_value=12)
)
def test_property_5_single_filter_correctness(data, filter_id):
    """
    Property 5: Subject Filter Correctness (Single Filter)
    
    *For any* single selected subject filter and any file list, the filtered 
    results should contain only files where the file's subject matches the 
    selected filter.
    
    **Validates: Requirements 3.2**
    """
    files, num_subjects = data
    filter_state = SubjectFilterState()
    
    # Apply single filter
    filter_state.toggle(str(filter_id))
    
    # Get filtered results
    visible_files = filter_state.apply(files)
    
    # Verify all visible files match the filter
    for file in visible_files:
        assert file.subject_id == filter_id, (
            f"File {file.file_id} with subject {file.subject_id} "
            f"should not be visible when filtering by subject {filter_id}"
        )
    
    # Verify no matching files are hidden
    for file in files:
        if file.subject_id == filter_id:
            assert file in visible_files, (
                f"File {file.file_id} with subject {filter_id} "
                f"should be visible when filtering by subject {filter_id}"
            )


@settings(max_examples=100)
@given(
    data=study_files_strategy(),
    filter_ids=st.lists(st.integers(min_value=1, max_value=12), min_size=1, max_size=5, unique=True)
)
def test_property_5_multi_filter_correctness(data, filter_ids):
    """
    Property 5: Subject Filter Correctness (Multiple Filters)
    
    *For any* set of selected subject filters and any file list, the filtered 
    results should contain only files where the file's subject matches at 
    least one selected filter.
    
    **Validates: Requirements 3.3**
    """
    files, num_subjects = data
    filter_state = SubjectFilterState()
    
    # Apply multiple filters
    for filter_id in filter_ids:
        filter_state.toggle(str(filter_id))
    
    # Get filtered results
    visible_files = filter_state.apply(files)
    
    # Convert filter_ids to set for easier lookup
    filter_set = set(filter_ids)
    
    # Verify all visible files match at least one filter
    for file in visible_files:
        assert file.subject_id in filter_set, (
            f"File {file.file_id} with subject {file.subject_id} "
            f"should not be visible when filtering by subjects {filter_ids}"
        )
    
    # Verify no matching files are hidden
    for file in files:
        if file.subject_id in filter_set:
            assert file in visible_files, (
                f"File {file.file_id} with subject {file.subject_id} "
                f"should be visible when filtering by subjects {filter_ids}"
            )


@settings(max_examples=100)
@given(data=study_files_strategy())
def test_property_5_all_filter_shows_all(data):
    """
    Property 5: Subject Filter Correctness (All Filter)
    
    *For any* file list, when "All" is selected, all files should be visible.
    
    **Validates: Requirements 3.2, 3.3**
    """
    files, _ = data
    filter_state = SubjectFilterState()
    
    # 'all' is selected by default
    assert 'all' in filter_state.selected_filters
    
    # Get filtered results
    visible_files = filter_state.apply(files)
    
    # All files should be visible
    assert len(visible_files) == len(files), (
        f"Expected all {len(files)} files to be visible, "
        f"but only {len(visible_files)} are visible"
    )
    
    for file in files:
        assert file in visible_files, (
            f"File {file.file_id} should be visible when 'All' filter is selected"
        )


@settings(max_examples=100)
@given(
    data=study_files_strategy(),
    filter_id=st.integers(min_value=1, max_value=12)
)
def test_property_5_all_reset_behavior(data, filter_id):
    """
    Property 5: Subject Filter Correctness (All Reset)
    
    *For any* filter state, clicking "All" should reset to show all files.
    
    **Validates: Requirements 3.2, 3.3**
    """
    files, _ = data
    filter_state = SubjectFilterState()
    
    # Apply a specific filter first
    filter_state.toggle(str(filter_id))
    assert 'all' not in filter_state.selected_filters
    
    # Click "All" to reset
    filter_state.toggle('all')
    
    # Should be reset to 'all'
    assert filter_state.selected_filters == ['all'], (
        f"Expected ['all'], got {filter_state.selected_filters}"
    )
    
    # All files should be visible
    visible_files = filter_state.apply(files)
    assert len(visible_files) == len(files)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
