"""
tests/test_tools.py

Unit tests for FitFindr tools:
- search_listings
- suggest_outfit
- create_fit_card

Each test verifies either:
1. correct output behavior
2. filtering logic
3. failure mode handling
"""

from tools import search_listings, suggest_outfit, create_fit_card

# ─────────────────────────────────────────────
# SEARCH_LISTINGS TESTS
# ─────────────────────────────────────────────
def test_search_returns_results():
    """
    Ensures search_listings returns a non-empty list for a valid query.
    """
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    """
    Ensures search_listings returns an empty list when no items match filters.
    This tests the 'no results' failure mode.
    """
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []    # empty list, no exception
    assert isinstance(results, list)


def test_search_price_filter():
    """
    Ensures all returned items respect the max_price constraint.
    """
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter():
    """
    Ensures size filtering works correctly when size is provided.
    """
    results = search_listings("shirt", size="M", max_price=None)
    assert all("m" in item["size"].lower() for item in results)

def test_search_combined_filters():
    """
    Ensures that combined filters (size and price) work together correctly.
    """
    results = search_listings("sweater", size="L", max_price=20)
    assert all("l" in item["size"].lower() and item["price"] <= 20 for item in results)

def test_search_result_structure():
    """
    NEW: Ensures search results follow expected schema.
    Prevents silent breakage if listing format changes.
    """
    results = search_listings("tee", size=None, max_price=None)

    assert len(results) > 0
    item = results[0]

    required_keys = {"id", "title", "price", "style_tags", "size"}

    assert all(key in item for key in required_keys)


# ─────────────────────────────────────────────
# SUGGEST_OUTFIT TESTS
# ─────────────────────────────────────────────
def test_suggest_outfit_non_empty_wardrobe():
    item = {
        "title": "Vintage Nike Tee",
        "description": "graphic tee",
        "style_tags": ["vintage"],
        "colors": ["black"]
    }

    wardrobe = {
        "items": [
            {"name": "Baggy Jeans", "category": "pants"},
            {"name": "Chunky Sneakers", "category": "shoes"}
        ]
    }

    result = suggest_outfit(item, wardrobe)

    assert isinstance(result, str)
    assert len(result) > 20  # basic sanity check

    # Should reference either item or wardrobe pieces
    text = result.lower()
    assert (
        "tee" in text
        or "jeans" in text
        or "sneakers" in text
        or "nike" in text
    )

def test_suggest_outfit_empty_wardrobe():
    item = {
        "title": "Vintage Nike Tee",
        "description": "graphic tee",
        "style_tags": ["vintage"],
        "colors": ["black"]
    }

    wardrobe = {"items": []}

    result = suggest_outfit(item, wardrobe)

    assert isinstance(result, str)
    assert len(result) > 20  # basic sanity check
    assert "tee" in result.lower()

def test_suggest_outfit_robust_to_bad_input():
    """
    NEW: Ensures tool does not crash on malformed inputs.
    Important for grading robustness.
    """
    item = {"title": None, "style_tags": None, "colors": None}
    wardrobe = {"items": []}

    result = suggest_outfit(item, wardrobe)

    assert isinstance(result, str)
    assert len(result) > 0


# ─────────────────────────────────────────────
# CREATE_FIT_CARD TESTS
# ─────────────────────────────────────────────
def test_create_fit_card_valid_input():
    """
    Ensures create_fit_card generates a valid caption for normal input.
    """
    item = {
        "title": "Vintage Nike Tee",
        "price": 25,
        "platform": "Depop"
    }

    outfit = "Baggy jeans, chunky sneakers"

    result = create_fit_card(outfit, item)

    assert isinstance(result, str)
    assert len(result) > 0


def test_create_fit_card_empty_outfit():
    """
    Ensures create_fit_card handles empty outfit input safely.
    This tests the fallback caption behavior.
    """
    item = {
        "title": "Vintage Nike Tee",
        "price": 25,
        "platform": "Depop"
    }

    result = create_fit_card("", item)

    assert isinstance(result, str)
    assert len(result) > 0
    assert (
        "tee" in result.lower()
        or "vintage" in result.lower()
        or "nike" in result.lower()
    )

def test_create_fit_card_mentions_metadata():
    """
    NEW: Ensures required metadata is present in output.
    Matches assignment requirement: item name, price, platform must appear.
    """
    item = {
        "title": "Vintage Nike Tee",
        "price": 25,
        "platform": "Depop"
    }

    result = create_fit_card("baggy jeans outfit", item)
    text = result.lower()

    assert "nike" in text or "tee" in text
    assert "25" in text or "$25" in text
    assert "depop" in text

def test_create_fit_card_variation():
    """
    Ensures LLM output is not deterministic (temperature randomness check).
    """
    item = {
        "title": "Vintage Nike Tee",
        "price": 25,
        "platform": "Depop"
    }

    outfit = "Baggy jeans and sneakers"

    outputs = [create_fit_card(outfit, item) for _ in range(3)]

    assert len(set(outputs)) > 1
