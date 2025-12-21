"""
Property-based tests for Subject Card Selection Toggle

Feature: study-page-improvements, Property 3: Subject Card Selection Toggle
Validates: Requirements 2.3
"""
import pytest
from hypothesis import given, strategies as st, settings
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SubjectCard:
    """Represents a subject card in the UI"""
    subject_id: int
    selected: bool = False


class SubjectCardSelector:
    """
    Simulates the subject card selection logic from the frontend.
    This mirrors the toggleSubjectCard JavaScript function behavior.
    """
    
    def __init__(self, cards: List[SubjectCard]):
        self.cards = cards
        self.selected_subject_id: Optional[int] = None
    
    def toggle_card(self, card_index: int) -> None:
        """Toggle selection state of a card (single selection mode)"""
        if card_index < 0 or card_index >= len(self.cards):
            return
        
        target_card = self.cards[card_index]
        was_selected = target_card.selected
        
        # Deselect all cards first
        for card in self.cards:
            card.selected = False
        
        if not was_selected:
            # Select this card
            target_card.selected = True
            self.selected_subject_id = target_card.subject_id
        else:
            # Deselect (no subject selected)
            self.selected_subject_id = None
    
    def get_selected_card(self) -> Optional[SubjectCard]:
        """Get the currently selected card, if any"""
        for card in self.cards:
            if card.selected:
                return card
        return None


# Strategy to generate a list of subject cards
@st.composite
def subject_cards_strategy(draw):
    """Generate a list of subject cards with unique IDs"""
    num_cards = draw(st.integers(min_value=1, max_value=12))
    cards = [SubjectCard(subject_id=i) for i in range(1, num_cards + 1)]
    return cards


@settings(max_examples=100)
@given(
    cards=subject_cards_strategy(),
    click_index=st.integers(min_value=0, max_value=11)
)
def test_property_3_subject_card_selection_toggle(cards, click_index):
    """
    Property 3: Subject Card Selection Toggle
    
    *For any* subject card, clicking it should toggle its selection state 
    from selected to unselected or vice versa.
    
    **Validates: Requirements 2.3**
    """
    # Ensure click_index is within bounds
    if click_index >= len(cards):
        click_index = click_index % len(cards)
    
    selector = SubjectCardSelector(cards)
    target_card = selector.cards[click_index]
    
    # Record initial state
    initial_selected = target_card.selected
    
    # Click the card
    selector.toggle_card(click_index)
    
    # Verify toggle behavior
    if not initial_selected:
        # Card was not selected, should now be selected
        assert target_card.selected == True, (
            f"Card {click_index} should be selected after clicking when unselected"
        )
        assert selector.selected_subject_id == target_card.subject_id, (
            f"Hidden input should have subject ID {target_card.subject_id}"
        )
    else:
        # Card was selected, should now be unselected
        assert target_card.selected == False, (
            f"Card {click_index} should be unselected after clicking when selected"
        )
        assert selector.selected_subject_id is None, (
            "Hidden input should be empty when card is deselected"
        )


@settings(max_examples=100)
@given(
    cards=subject_cards_strategy(),
    click_sequence=st.lists(st.integers(min_value=0, max_value=11), min_size=1, max_size=10)
)
def test_property_3_single_selection_invariant(cards, click_sequence):
    """
    Property 3 (extended): Single Selection Invariant
    
    *For any* sequence of clicks, at most one card should be selected at any time.
    
    **Validates: Requirements 2.3**
    """
    selector = SubjectCardSelector(cards)
    
    for click_index in click_sequence:
        # Ensure click_index is within bounds
        if click_index >= len(cards):
            click_index = click_index % len(cards)
        
        selector.toggle_card(click_index)
        
        # Count selected cards
        selected_count = sum(1 for card in selector.cards if card.selected)
        
        # Invariant: at most one card selected
        assert selected_count <= 1, (
            f"Expected at most 1 selected card, found {selected_count}"
        )
        
        # If a card is selected, it should match the hidden input value
        selected_card = selector.get_selected_card()
        if selected_card:
            assert selector.selected_subject_id == selected_card.subject_id, (
                f"Hidden input ({selector.selected_subject_id}) should match "
                f"selected card ID ({selected_card.subject_id})"
            )
        else:
            assert selector.selected_subject_id is None, (
                "Hidden input should be None when no card is selected"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
