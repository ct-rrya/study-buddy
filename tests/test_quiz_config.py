"""
Property-based tests for Quiz Configuration Validation

Feature: study-page-improvements, Property 6: Quiz Configuration Validation
Validates: Requirements 4.2, 4.3
"""
import pytest
from hypothesis import given, strategies as st, settings
from typing import Optional


# Valid quiz configuration values
VALID_QUESTION_COUNTS = [5, 10, 15, 20]
VALID_QUESTION_TYPES = ['multiple_choice', 'identification', 'true_false', 'mixed']


class QuizConfigValidator:
    """
    Validates quiz configuration parameters.
    This mirrors the validation logic that should be applied on both
    frontend and backend.
    """
    
    @staticmethod
    def validate_count(count: int) -> bool:
        """Validate question count is one of the allowed values"""
        return count in VALID_QUESTION_COUNTS
    
    @staticmethod
    def validate_type(question_type: str) -> bool:
        """Validate question type is one of the allowed values"""
        return question_type in VALID_QUESTION_TYPES
    
    @staticmethod
    def validate_config(count: int, question_type: str) -> tuple[bool, Optional[str]]:
        """
        Validate a complete quiz configuration.
        Returns (is_valid, error_message)
        """
        if not QuizConfigValidator.validate_count(count):
            return False, f"Invalid question count: {count}. Must be one of {VALID_QUESTION_COUNTS}"
        
        if not QuizConfigValidator.validate_type(question_type):
            return False, f"Invalid question type: {question_type}. Must be one of {VALID_QUESTION_TYPES}"
        
        return True, None


# Strategy for valid question counts
valid_count_strategy = st.sampled_from(VALID_QUESTION_COUNTS)

# Strategy for valid question types
valid_type_strategy = st.sampled_from(VALID_QUESTION_TYPES)

# Strategy for invalid question counts
invalid_count_strategy = st.integers().filter(lambda x: x not in VALID_QUESTION_COUNTS)

# Strategy for invalid question types
invalid_type_strategy = st.text(min_size=1, max_size=50).filter(
    lambda x: x not in VALID_QUESTION_TYPES
)


@settings(max_examples=100)
@given(count=valid_count_strategy, question_type=valid_type_strategy)
def test_property_6_valid_config_accepted(count, question_type):
    """
    Property 6: Quiz Configuration Validation (Valid Configs)
    
    *For any* quiz configuration where count is in [5, 10, 15, 20] and
    type is in ['multiple_choice', 'identification', 'true_false', 'mixed'],
    the configuration should be accepted as valid.
    
    **Validates: Requirements 4.2, 4.3**
    """
    is_valid, error = QuizConfigValidator.validate_config(count, question_type)
    
    assert is_valid, (
        f"Valid config (count={count}, type={question_type}) "
        f"was rejected with error: {error}"
    )
    assert error is None


@settings(max_examples=100)
@given(count=invalid_count_strategy, question_type=valid_type_strategy)
def test_property_6_invalid_count_rejected(count, question_type):
    """
    Property 6: Quiz Configuration Validation (Invalid Count)
    
    *For any* quiz configuration where count is NOT in [5, 10, 15, 20],
    the configuration should be rejected.
    
    **Validates: Requirements 4.2**
    """
    is_valid, error = QuizConfigValidator.validate_config(count, question_type)
    
    assert not is_valid, (
        f"Invalid count {count} should have been rejected"
    )
    assert error is not None
    assert str(count) in error


@settings(max_examples=100)
@given(count=valid_count_strategy, question_type=invalid_type_strategy)
def test_property_6_invalid_type_rejected(count, question_type):
    """
    Property 6: Quiz Configuration Validation (Invalid Type)
    
    *For any* quiz configuration where type is NOT in 
    ['multiple_choice', 'identification', 'true_false', 'mixed'],
    the configuration should be rejected.
    
    **Validates: Requirements 4.3**
    """
    is_valid, error = QuizConfigValidator.validate_config(count, question_type)
    
    assert not is_valid, (
        f"Invalid type '{question_type}' should have been rejected"
    )
    assert error is not None
    assert question_type in error


@settings(max_examples=100)
@given(count=invalid_count_strategy, question_type=invalid_type_strategy)
def test_property_6_both_invalid_rejected(count, question_type):
    """
    Property 6: Quiz Configuration Validation (Both Invalid)
    
    *For any* quiz configuration where both count and type are invalid,
    the configuration should be rejected.
    
    **Validates: Requirements 4.2, 4.3**
    """
    is_valid, error = QuizConfigValidator.validate_config(count, question_type)
    
    assert not is_valid, (
        f"Config with invalid count {count} and type '{question_type}' "
        f"should have been rejected"
    )
    assert error is not None


def test_all_valid_counts_accepted():
    """
    Verify all valid question counts are accepted.
    
    **Validates: Requirements 4.2**
    """
    for count in VALID_QUESTION_COUNTS:
        assert QuizConfigValidator.validate_count(count), (
            f"Valid count {count} should be accepted"
        )


def test_all_valid_types_accepted():
    """
    Verify all valid question types are accepted.
    
    **Validates: Requirements 4.3**
    """
    for qtype in VALID_QUESTION_TYPES:
        assert QuizConfigValidator.validate_type(qtype), (
            f"Valid type '{qtype}' should be accepted"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
