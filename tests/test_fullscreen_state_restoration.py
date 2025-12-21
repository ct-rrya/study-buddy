"""
Property-based tests for Fullscreen State Restoration

Feature: study-page-improvements, Property 10: Fullscreen State Restoration
Validates: Requirements 5.6
"""
import pytest
from hypothesis import given, strategies as st, settings
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Flashcard:
    """Represents a flashcard"""
    index: int
    front: str
    back: str
    flipped: bool = False
    active: bool = False
    marked_knew: bool = False
    marked_learning: bool = False


@dataclass
class FullscreenState:
    """Tracks fullscreen state for restoration"""
    original_card_index: int = 0
    is_active: bool = False
    knew_count: int = 0
    learning_count: int = 0


class FlashcardContainer:
    """Simulates the original flashcard container in the chat"""
    
    def __init__(self, cards: List[Flashcard]):
        self.cards = [
            Flashcard(
                index=c.index,
                front=c.front,
                back=c.back,
                flipped=c.flipped,
                active=c.active,
                marked_knew=c.marked_knew,
                marked_learning=c.marked_learning
            )
            for c in cards
        ]
        self.current_index = 0
        self.knew_count = 0
        self.learning_count = 0
        
        if self.cards:
            self.cards[0].active = True


class FullscreenFlashcardMode:
    """
    Simulates the fullscreen flashcard mode logic from the frontend.
    This mirrors the enterFullscreen/exitFullscreen JavaScript functions.
    """
    
    def __init__(self):
        self.state = FullscreenState()
        self.fullscreen_cards: List[Flashcard] = []
        self.current_index = 0
        self.total = 0
    
    def enter_fullscreen(self, container: FlashcardContainer) -> None:
        """Enter fullscreen mode, cloning cards from container"""
        # Store original state for restoration
        self.state.original_card_index = container.current_index
        self.state.is_active = True
        self.state.knew_count = container.knew_count
        self.state.learning_count = container.learning_count
        
        # Clone cards to fullscreen
        self.fullscreen_cards = [
            Flashcard(
                index=c.index,
                front=c.front,
                back=c.back,
                flipped=c.flipped,
                active=c.active,
                marked_knew=c.marked_knew,
                marked_learning=c.marked_learning
            )
            for c in container.cards
        ]
        
        self.current_index = container.current_index
        self.total = len(self.fullscreen_cards)
    
    def navigate(self, direction: int) -> bool:
        """Navigate between cards in fullscreen"""
        if not self.fullscreen_cards:
            return False
        
        new_index = self.current_index + direction
        
        if new_index < 0 or new_index >= self.total:
            return False
        
        self.fullscreen_cards[self.current_index].active = False
        self.fullscreen_cards[new_index].active = True
        self.fullscreen_cards[new_index].flipped = False
        self.current_index = new_index
        return True
    
    def mark_response(self, knew: bool) -> None:
        """Mark current card as knew or learning"""
        if not self.fullscreen_cards:
            return
        
        card = self.fullscreen_cards[self.current_index]
        if knew:
            card.marked_knew = True
            self.state.knew_count += 1
        else:
            card.marked_learning = True
            self.state.learning_count += 1
    
    def exit_fullscreen(self, container: FlashcardContainer) -> None:
        """Exit fullscreen and restore state to container"""
        if not self.state.is_active:
            return
        
        # Sync current position back to container
        for card in container.cards:
            card.active = False
        
        if self.current_index < len(container.cards):
            container.cards[self.current_index].active = True
        container.current_index = self.current_index
        
        # Sync marked states from fullscreen to original
        for i, fs_card in enumerate(self.fullscreen_cards):
            if i < len(container.cards):
                if fs_card.marked_knew:
                    container.cards[i].marked_knew = True
                if fs_card.marked_learning:
                    container.cards[i].marked_learning = True
        
        # Sync counts
        container.knew_count = self.state.knew_count
        container.learning_count = self.state.learning_count
        
        self.state.is_active = False


# Strategy to generate a list of flashcards
@st.composite
def flashcards_strategy(draw):
    """Generate a list of flashcards"""
    num_cards = draw(st.integers(min_value=1, max_value=15))
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
    navigation_sequence=st.lists(
        st.sampled_from([-1, 1]),
        min_size=0,
        max_size=20
    )
)
def test_property_10_position_restored_on_exit(cards, navigation_sequence):
    """
    Property 10: Fullscreen State Restoration (Position)
    
    *For any* flashcard position when entering fullscreen mode, exiting 
    fullscreen should restore the view to the current card position 
    (which may have changed during fullscreen navigation).
    
    **Validates: Requirements 5.6**
    """
    container = FlashcardContainer(cards)
    fullscreen = FullscreenFlashcardMode()
    
    # Enter fullscreen
    fullscreen.enter_fullscreen(container)
    
    # Navigate in fullscreen
    for direction in navigation_sequence:
        fullscreen.navigate(direction)
    
    # Record position before exit
    fullscreen_position = fullscreen.current_index
    
    # Exit fullscreen
    fullscreen.exit_fullscreen(container)
    
    # Verify position is synced back
    assert container.current_index == fullscreen_position, (
        f"Container position {container.current_index} should match "
        f"fullscreen position {fullscreen_position}"
    )
    
    # Verify the correct card is active
    assert container.cards[container.current_index].active == True, (
        f"Card at position {container.current_index} should be active"
    )
    
    # Verify only one card is active
    active_count = sum(1 for c in container.cards if c.active)
    assert active_count == 1, (
        f"Expected exactly 1 active card, found {active_count}"
    )


@settings(max_examples=100)
@given(
    cards=flashcards_strategy(),
    responses=st.lists(
        st.booleans(),
        min_size=0,
        max_size=10
    )
)
def test_property_10_marked_states_synced_on_exit(cards, responses):
    """
    Property 10: Fullscreen State Restoration (Marked States)
    
    *For any* cards marked as knew/learning in fullscreen mode, those 
    marked states should be synced back to the original container on exit.
    
    **Validates: Requirements 5.6**
    """
    container = FlashcardContainer(cards)
    fullscreen = FullscreenFlashcardMode()
    
    # Enter fullscreen
    fullscreen.enter_fullscreen(container)
    
    # Mark some cards with responses
    marked_indices = []
    for i, knew in enumerate(responses):
        if fullscreen.current_index < len(cards):
            marked_indices.append((fullscreen.current_index, knew))
            fullscreen.mark_response(knew)
            # Move to next card if possible
            fullscreen.navigate(1)
    
    # Exit fullscreen
    fullscreen.exit_fullscreen(container)
    
    # Verify marked states are synced
    for index, knew in marked_indices:
        if knew:
            assert container.cards[index].marked_knew == True, (
                f"Card {index} should be marked as knew"
            )
        else:
            assert container.cards[index].marked_learning == True, (
                f"Card {index} should be marked as learning"
            )


@settings(max_examples=100)
@given(
    cards=flashcards_strategy(),
    responses=st.lists(
        st.booleans(),
        min_size=0,
        max_size=10
    )
)
def test_property_10_counts_synced_on_exit(cards, responses):
    """
    Property 10: Fullscreen State Restoration (Counts)
    
    *For any* responses given in fullscreen mode, the knew_count and 
    learning_count should be synced back to the original container on exit.
    
    **Validates: Requirements 5.6**
    """
    container = FlashcardContainer(cards)
    fullscreen = FullscreenFlashcardMode()
    
    # Enter fullscreen
    fullscreen.enter_fullscreen(container)
    
    # Count expected responses
    expected_knew = 0
    expected_learning = 0
    
    for knew in responses:
        if fullscreen.current_index < len(cards):
            fullscreen.mark_response(knew)
            if knew:
                expected_knew += 1
            else:
                expected_learning += 1
            fullscreen.navigate(1)
    
    # Exit fullscreen
    fullscreen.exit_fullscreen(container)
    
    # Verify counts are synced
    assert container.knew_count == expected_knew, (
        f"knew_count {container.knew_count} should be {expected_knew}"
    )
    assert container.learning_count == expected_learning, (
        f"learning_count {container.learning_count} should be {expected_learning}"
    )


@settings(max_examples=100)
@given(
    cards=flashcards_strategy(),
    starting_position=st.integers(min_value=0, max_value=14)
)
def test_property_10_enter_exit_without_changes(cards, starting_position):
    """
    Property 10: Fullscreen State Restoration (No Changes)
    
    *For any* flashcard set, entering and immediately exiting fullscreen 
    without any navigation should preserve the original state.
    
    **Validates: Requirements 5.6**
    """
    # Ensure starting position is within bounds
    if starting_position >= len(cards):
        starting_position = starting_position % len(cards)
    
    container = FlashcardContainer(cards)
    
    # Move to starting position
    for card in container.cards:
        card.active = False
    container.cards[starting_position].active = True
    container.current_index = starting_position
    
    fullscreen = FullscreenFlashcardMode()
    
    # Enter and immediately exit
    fullscreen.enter_fullscreen(container)
    fullscreen.exit_fullscreen(container)
    
    # Verify state is preserved
    assert container.current_index == starting_position, (
        f"Position should be preserved at {starting_position}"
    )
    assert container.cards[starting_position].active == True, (
        f"Card at {starting_position} should still be active"
    )
    assert container.knew_count == 0, "knew_count should be 0"
    assert container.learning_count == 0, "learning_count should be 0"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
