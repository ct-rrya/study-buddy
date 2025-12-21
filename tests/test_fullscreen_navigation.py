"""
Property-based tests for Fullscreen Navigation Correctness

Feature: study-page-improvements, Property 9: Fullscreen Navigation Correctness
Validates: Requirements 5.3
"""
import pytest
from hypothesis import given, strategies as st, settings
from dataclasses import dataclass
from typing import List


@dataclass
class Flashcard:
    """Represents a flashcard"""
    index: int
    front: str
    back: str
    flipped: bool = False
    active: bool = False


class FullscreenFlashcardNavigator:
    """
    Simulates the fullscreen flashcard navigation logic from the frontend.
    This mirrors the fullscreenNav JavaScript function behavior.
    """
    
    def __init__(self, cards: List[Flashcard]):
        self.cards = cards
        self.current_index = 0
        self.total = len(cards)
        
        # Set first card as active
        if self.cards:
            self.cards[0].active = True
    
    def navigate(self, direction: int) -> bool:
        """
        Navigate between cards.
        direction: -1 for previous, 1 for next
        Returns True if navigation occurred, False if at boundary
        """
        if not self.cards:
            return False
        
        new_index = self.current_index + direction
        
        # Respect card boundaries
        if new_index < 0 or new_index >= self.total:
            return False
        
        # Deactivate current card
        self.cards[self.current_index].active = False
        
        # Activate new card and reset flip state
        self.cards[new_index].active = True
        self.cards[new_index].flipped = False
        
        self.current_index = new_index
        return True
    
    def get_current_card(self) -> Flashcard:
        """Get the currently active card"""
        return self.cards[self.current_index]
    
    def get_display_position(self) -> int:
        """Get the 1-based display position (for UI)"""
        return self.current_index + 1


# Strategy to generate a list of flashcards
@st.composite
def flashcards_strategy(draw):
    """Generate a list of flashcards"""
    num_cards = draw(st.integers(min_value=1, max_value=20))
    cards = [
        Flashcard(
            index=i,
            front=f"Question {i+1}",
            back=f"Answer {i+1}"
        )
        for i in range(num_cards)
    ]
    return cards


@settings(max_examples=100)
@given(
    cards=flashcards_strategy(),
    starting_position=st.integers(min_value=0, max_value=19)
)
def test_property_9_right_arrow_advances_card(cards, starting_position):
    """
    Property 9: Fullscreen Navigation Correctness (Right Arrow)
    
    *For any* flashcard set in fullscreen mode, pressing the right arrow key 
    should advance to the next card (if not at the last card).
    
    **Validates: Requirements 5.3**
    """
    # Ensure starting position is within bounds
    if starting_position >= len(cards):
        starting_position = starting_position % len(cards)
    
    navigator = FullscreenFlashcardNavigator(cards)
    
    # Move to starting position
    for _ in range(starting_position):
        navigator.navigate(1)
    
    initial_index = navigator.current_index
    
    # Press right arrow (direction = 1)
    navigated = navigator.navigate(1)
    
    if initial_index < len(cards) - 1:
        # Not at last card - should advance
        assert navigated == True, "Navigation should succeed when not at last card"
        assert navigator.current_index == initial_index + 1, (
            f"Expected index {initial_index + 1}, got {navigator.current_index}"
        )
        assert navigator.cards[navigator.current_index].active == True, (
            "New card should be active"
        )
        assert navigator.cards[initial_index].active == False, (
            "Previous card should be inactive"
        )
    else:
        # At last card - should not advance
        assert navigated == False, "Navigation should fail at last card"
        assert navigator.current_index == initial_index, (
            "Index should remain unchanged at boundary"
        )


@settings(max_examples=100)
@given(
    cards=flashcards_strategy(),
    starting_position=st.integers(min_value=0, max_value=19)
)
def test_property_9_left_arrow_goes_previous(cards, starting_position):
    """
    Property 9: Fullscreen Navigation Correctness (Left Arrow)
    
    *For any* flashcard set in fullscreen mode, pressing the left arrow key 
    should go to the previous card (if not at the first card).
    
    **Validates: Requirements 5.3**
    """
    # Ensure starting position is within bounds
    if starting_position >= len(cards):
        starting_position = starting_position % len(cards)
    
    navigator = FullscreenFlashcardNavigator(cards)
    
    # Move to starting position
    for _ in range(starting_position):
        navigator.navigate(1)
    
    initial_index = navigator.current_index
    
    # Press left arrow (direction = -1)
    navigated = navigator.navigate(-1)
    
    if initial_index > 0:
        # Not at first card - should go back
        assert navigated == True, "Navigation should succeed when not at first card"
        assert navigator.current_index == initial_index - 1, (
            f"Expected index {initial_index - 1}, got {navigator.current_index}"
        )
        assert navigator.cards[navigator.current_index].active == True, (
            "New card should be active"
        )
        assert navigator.cards[initial_index].active == False, (
            "Previous card should be inactive"
        )
    else:
        # At first card - should not go back
        assert navigated == False, "Navigation should fail at first card"
        assert navigator.current_index == initial_index, (
            "Index should remain unchanged at boundary"
        )


@settings(max_examples=100)
@given(
    cards=flashcards_strategy(),
    navigation_sequence=st.lists(
        st.sampled_from([-1, 1]),
        min_size=1,
        max_size=50
    )
)
def test_property_9_navigation_respects_boundaries(cards, navigation_sequence):
    """
    Property 9: Fullscreen Navigation Correctness (Boundary Invariant)
    
    *For any* sequence of navigation actions, the current index should 
    always remain within valid bounds [0, total-1].
    
    **Validates: Requirements 5.3**
    """
    navigator = FullscreenFlashcardNavigator(cards)
    
    for direction in navigation_sequence:
        navigator.navigate(direction)
        
        # Invariant: index always within bounds
        assert 0 <= navigator.current_index < len(cards), (
            f"Index {navigator.current_index} out of bounds [0, {len(cards)-1}]"
        )
        
        # Invariant: exactly one card is active
        active_count = sum(1 for card in navigator.cards if card.active)
        assert active_count == 1, (
            f"Expected exactly 1 active card, found {active_count}"
        )
        
        # Invariant: the active card matches current_index
        assert navigator.cards[navigator.current_index].active == True, (
            f"Card at current_index {navigator.current_index} should be active"
        )


@settings(max_examples=100)
@given(
    cards=flashcards_strategy(),
    navigation_sequence=st.lists(
        st.sampled_from([-1, 1]),
        min_size=1,
        max_size=30
    )
)
def test_property_9_display_position_matches_index(cards, navigation_sequence):
    """
    Property 9: Fullscreen Navigation Correctness (Display Position)
    
    *For any* navigation sequence, the display position should always be
    current_index + 1 (1-based for UI display).
    
    **Validates: Requirements 5.3**
    """
    navigator = FullscreenFlashcardNavigator(cards)
    
    for direction in navigation_sequence:
        navigator.navigate(direction)
        
        # Display position should be 1-based
        expected_display = navigator.current_index + 1
        actual_display = navigator.get_display_position()
        
        assert actual_display == expected_display, (
            f"Display position {actual_display} should be {expected_display}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
