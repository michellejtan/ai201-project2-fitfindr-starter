"""
Test the Gradio UI integration by calling handle_query directly.
"""
import sys
sys.path.insert(0, '/home/michelle1/ai201-project2-fitfindr-starter')

from app import handle_query

def test_ui_happy_path():
    """Test a complete happy path query through the UI handler."""
    print("\n" + "=" * 80)
    print("UI INTEGRATION TEST 1: Happy Path Query")
    print("=" * 80)

    listing_text, outfit_text, fit_card_text = handle_query(
        user_query="looking for a vintage graphic tee under $30, size M",
        wardrobe_choice="Example wardrobe"
    )

    print("\n🛍️ Listing Output:")
    print("-" * 40)
    print(listing_text)
    print("-" * 40)

    print("\n👗 Outfit Suggestion:")
    print("-" * 40)
    print(outfit_text)
    print("-" * 40)

    print("\n✨ Fit Card:")
    print("-" * 40)
    print(fit_card_text)
    print("-" * 40)

    # Verify outputs are populated
    assert listing_text and not listing_text.startswith("Error"), "Listing should be populated"
    assert outfit_text, "Outfit suggestion should be populated"
    assert fit_card_text, "Fit card should be populated"
    assert "Price:" in listing_text, "Listing should show price"
    assert "Platform:" in listing_text, "Listing should show platform"

    print("\n✅ Happy path UI test PASSED")


def test_ui_no_results():
    """Test the no-results error path through the UI handler."""
    print("\n" + "=" * 80)
    print("UI INTEGRATION TEST 2: No-Results Error Path")
    print("=" * 80)

    listing_text, outfit_text, fit_card_text = handle_query(
        user_query="designer ballgown size XXS under $5",
        wardrobe_choice="Example wardrobe"
    )

    print("\n🛍️ Listing Output (should be error):")
    print("-" * 40)
    print(listing_text)
    print("-" * 40)

    print("\n👗 Outfit Suggestion (should be empty):")
    print("-" * 40)
    print(f"'{outfit_text}'")
    print("-" * 40)

    print("\n✨ Fit Card (should be empty):")
    print("-" * 40)
    print(f"'{fit_card_text}'")
    print("-" * 40)

    # Verify error path
    assert listing_text.startswith("Error:"), "Should return error in listing panel"
    assert outfit_text == "", "Outfit should be empty on error"
    assert fit_card_text == "", "Fit card should be empty on error"

    print("\n✅ No-results error path test PASSED")


def test_ui_empty_query():
    """Test the empty query guard."""
    print("\n" + "=" * 80)
    print("UI INTEGRATION TEST 3: Empty Query Guard")
    print("=" * 80)

    listing_text, outfit_text, fit_card_text = handle_query(
        user_query="",
        wardrobe_choice="Example wardrobe"
    )

    print("\n🛍️ Listing Output (should be error):")
    print("-" * 40)
    print(listing_text)
    print("-" * 40)

    assert listing_text == "Please enter a search query.", "Should reject empty query"
    assert outfit_text == "", "Outfit should be empty on invalid input"
    assert fit_card_text == "", "Fit card should be empty on invalid input"

    print("\n✅ Empty query guard test PASSED")


def test_ui_empty_wardrobe():
    """Test with empty wardrobe."""
    print("\n" + "=" * 80)
    print("UI INTEGRATION TEST 4: Empty Wardrobe Path")
    print("=" * 80)

    listing_text, outfit_text, fit_card_text = handle_query(
        user_query="vintage tee under $40",
        wardrobe_choice="Empty wardrobe (new user)"
    )

    print("\n🛍️ Listing Output:")
    print("-" * 40)
    print(listing_text)
    print("-" * 40)

    print("\n👗 Outfit Suggestion (should work with empty wardrobe):")
    print("-" * 40)
    print(outfit_text)
    print("-" * 40)

    print("\n✨ Fit Card:")
    print("-" * 40)
    print(fit_card_text)
    print("-" * 40)

    # Verify fallback behavior for empty wardrobe
    assert listing_text and not listing_text.startswith("Error"), "Should find items"
    assert outfit_text, "Should generate outfit suggestion even with empty wardrobe"
    assert fit_card_text, "Should generate fit card"

    print("\n✅ Empty wardrobe path test PASSED")


if __name__ == "__main__":
    test_ui_happy_path()
    test_ui_no_results()
    test_ui_empty_query()
    test_ui_empty_wardrobe()
    print("\n" + "=" * 80)
    print("ALL UI INTEGRATION TESTS PASSED ✅")
    print("=" * 80)
