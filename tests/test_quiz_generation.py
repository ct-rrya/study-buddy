"""
Property-based tests for Quiz Generation Matching Configuration

Feature: study-page-improvements, Property 7: Quiz Generation Matches Configuration
Validates: Requirements 4.4
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.bot import StudyBot


# Valid quiz configuration values
VALID_QUESTION_COUNTS = [5, 10, 15, 20]
VALID_QUESTION_TYPES = ['multiple_choice', 'identification', 'true_false', 'mixed']


# Sample study content for testing - sufficient content for quiz generation
SAMPLE_STUDY_CONTENT = """
Introduction to Computer Science

Chapter 1: Data Structures

A data structure is a way of organizing and storing data so that it can be accessed and modified efficiently.

Arrays: An array is a collection of elements stored at contiguous memory locations. Arrays allow random access to elements using indices. The time complexity for accessing an element is O(1).

Linked Lists: A linked list is a linear data structure where elements are stored in nodes. Each node contains data and a reference to the next node. Linked lists allow efficient insertion and deletion.

Stacks: A stack is a Last-In-First-Out (LIFO) data structure. Elements are added and removed from the same end called the top. Common operations are push (add) and pop (remove).

Queues: A queue is a First-In-First-Out (FIFO) data structure. Elements are added at the rear and removed from the front. Common operations are enqueue (add) and dequeue (remove).

Trees: A tree is a hierarchical data structure with a root node and child nodes. Binary trees have at most two children per node. Binary Search Trees maintain sorted order.

Hash Tables: A hash table uses a hash function to map keys to indices. This allows O(1) average time complexity for search, insert, and delete operations.

Graphs: A graph consists of vertices (nodes) and edges connecting them. Graphs can be directed or undirected, weighted or unweighted.

Chapter 2: Algorithms

An algorithm is a step-by-step procedure for solving a problem or accomplishing a task.

Sorting Algorithms:
- Bubble Sort: Repeatedly swaps adjacent elements if they are in wrong order. Time complexity O(n²).
- Quick Sort: Uses divide and conquer with a pivot element. Average time complexity O(n log n).
- Merge Sort: Divides array into halves, sorts, and merges. Time complexity O(n log n).

Searching Algorithms:
- Linear Search: Checks each element sequentially. Time complexity O(n).
- Binary Search: Works on sorted arrays, divides search space in half. Time complexity O(log n).

Chapter 3: Programming Concepts

Variables store data values. Data types include integers, floats, strings, and booleans.

Functions are reusable blocks of code that perform specific tasks. They can accept parameters and return values.

Object-Oriented Programming (OOP) uses classes and objects. Key concepts include encapsulation, inheritance, and polymorphism.

Recursion is when a function calls itself. Every recursive function needs a base case to prevent infinite loops.
"""


class MockStudyBot(StudyBot):
    """
    Mock StudyBot that simulates quiz generation without calling the actual API.
    This allows us to test the configuration handling logic.
    """
    
    def _chat(self, user_message, task_context=""):
        """Mock the chat method to return predictable quiz responses"""
        # Parse the requested number of questions from the prompt
        import re
        match = re.search(r'Create exactly (\d+)', user_message)
        num_questions = int(match.group(1)) if match else 5
        
        # Determine question type from prompt
        if 'Multiple Choice ONLY' in user_message:
            question_type = 'multiple_choice'
        elif 'Identification ONLY' in user_message:
            question_type = 'identification'
        elif 'True/False ONLY' in user_message:
            question_type = 'true_false'
        else:
            question_type = 'mixed'
        
        # Generate mock questions based on type
        questions = []
        for i in range(1, num_questions + 1):
            if question_type == 'multiple_choice':
                questions.append(f"Q{i}: What is a data structure? (A) A way to organize data (B) A programming language (C) A computer (D) A network")
                questions.append(f"A{i}: A")
            elif question_type == 'identification':
                questions.append(f"Q{i}: Identify: A Last-In-First-Out data structure")
                questions.append(f"A{i}: Stack")
            elif question_type == 'true_false':
                questions.append(f"Q{i}: True or False: Arrays allow random access to elements")
                questions.append(f"A{i}: True")
            else:  # mixed
                if i % 4 == 1:
                    questions.append(f"Q{i}: What is a data structure? (A) A way to organize data (B) A programming language (C) A computer (D) A network")
                    questions.append(f"A{i}: A")
                elif i % 4 == 2:
                    questions.append(f"Q{i}: Identify: A Last-In-First-Out data structure")
                    questions.append(f"A{i}: Stack")
                elif i % 4 == 3:
                    questions.append(f"Q{i}: True or False: Arrays allow random access to elements")
                    questions.append(f"A{i}: True")
                else:
                    questions.append(f"Q{i}: The _____ data structure uses FIFO ordering")
                    questions.append(f"A{i}: Queue")
        
        return "QUIZ_START\n" + "\n".join(questions) + "\nQUIZ_END"


# Strategy for valid question counts
valid_count_strategy = st.sampled_from(VALID_QUESTION_COUNTS)

# Strategy for valid question types
valid_type_strategy = st.sampled_from(VALID_QUESTION_TYPES)


@settings(max_examples=100)
@given(count=valid_count_strategy, question_type=valid_type_strategy)
def test_property_7_quiz_generation_matches_config(count, question_type):
    """
    Property 7: Quiz Generation Matches Configuration
    
    *For any* valid quiz configuration with sufficient study material,
    the generated quiz should have exactly the requested number of questions
    and all questions should match the requested type (or be mixed types if 'mixed' is selected).
    
    **Validates: Requirements 4.4**
    """
    bot = MockStudyBot(SAMPLE_STUDY_CONTENT)
    result = bot.generate_quiz(num_questions=count, question_type=question_type)
    
    # Verify quiz was generated successfully
    assert result['type'] == 'quiz', f"Expected quiz type, got {result['type']}"
    
    # Verify question count matches requested
    assert result['total'] == count, (
        f"Expected {count} questions, got {result['total']}"
    )
    assert len(result['questions']) == count, (
        f"Expected {count} questions in list, got {len(result['questions'])}"
    )
    
    # Verify requested_count is set correctly
    assert result['requested_count'] == count, (
        f"Expected requested_count={count}, got {result.get('requested_count')}"
    )
    
    # Verify question_type is set correctly
    assert result['question_type'] == question_type, (
        f"Expected question_type={question_type}, got {result.get('question_type')}"
    )
    
    # Verify question types match configuration
    if question_type != 'mixed':
        for q in result['questions']:
            detected_type = q.get('type', '')
            # For specific types, verify all questions match
            if question_type == 'multiple_choice':
                assert detected_type == 'multiple_choice', (
                    f"Expected multiple_choice question, got {detected_type}: {q['question']}"
                )
            elif question_type == 'identification':
                assert detected_type == 'identification', (
                    f"Expected identification question, got {detected_type}: {q['question']}"
                )
            elif question_type == 'true_false':
                assert detected_type == 'true_false', (
                    f"Expected true_false question, got {detected_type}: {q['question']}"
                )


@settings(max_examples=100)
@given(count=valid_count_strategy)
def test_property_7_mixed_type_allows_variety(count):
    """
    Property 7: Quiz Generation Matches Configuration (Mixed Type)
    
    *For any* valid quiz configuration with 'mixed' type,
    the generated quiz should allow various question types.
    
    **Validates: Requirements 4.4**
    """
    bot = MockStudyBot(SAMPLE_STUDY_CONTENT)
    result = bot.generate_quiz(num_questions=count, question_type='mixed')
    
    # Verify quiz was generated
    assert result['type'] == 'quiz'
    assert result['total'] == count
    
    # For mixed type, we just verify questions were generated
    # (they can be any valid type)
    for q in result['questions']:
        assert 'question' in q
        assert 'answer' in q
        assert 'type' in q


def test_insufficient_content_handling():
    """
    Test that insufficient content is handled gracefully.
    
    **Validates: Requirements 4.6**
    """
    # Content less than 100 characters
    short_content = "Short content"
    bot = StudyBot(short_content)
    result = bot.generate_quiz(num_questions=10, question_type='mixed')
    
    # Should return an error type
    assert result['type'] == 'error'
    assert 'Not enough content' in result['message']


def test_invalid_count_defaults_to_5():
    """
    Test that invalid question count defaults to 5.
    
    **Validates: Requirements 4.4**
    """
    bot = MockStudyBot(SAMPLE_STUDY_CONTENT)
    
    # Test with invalid count
    result = bot.generate_quiz(num_questions=7, question_type='mixed')
    
    # Should default to 5
    assert result['total'] == 5
    assert result['requested_count'] == 5


def test_invalid_type_defaults_to_mixed():
    """
    Test that invalid question type defaults to mixed.
    
    **Validates: Requirements 4.4**
    """
    bot = MockStudyBot(SAMPLE_STUDY_CONTENT)
    
    # Test with invalid type
    result = bot.generate_quiz(num_questions=5, question_type='invalid_type')
    
    # Should default to mixed
    assert result['question_type'] == 'mixed'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
