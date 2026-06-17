"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
        "retry_note": None,          # set if search was retried with looser constraints
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop
    session = _new_session(query, wardrobe)     # Step 1: initialize session


    # ─────────────────────────────
    # Step 2: parse query (regex-based, deterministic)
    # ─────────────────────────────
    import re
    text = query.lower()

    # price extraction (robust for "under $30", "$30", etc.)
    price_match = re.search(r"(?:under|below|<)?\s*\$?(\d+)", text)
    max_price = int(price_match.group(1)) if price_match else None

    # size extraction (includes common variants)
    size_match = re.search(
        r"\b(xs|s|m|l|xl|xxl|s/m|m/l|l/xl|one size)\b",
        text
    )
    size = size_match.group(1).upper() if size_match else None

    # description = cleaned query (simple + stable for grading)
    description = query

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    # ─────────────────────────────
    # Step 3: search listings (with retry fallback)
    # ─────────────────────────────
    results = search_listings(description, size, max_price)
    session["search_results"] = results

    # Retry 1: drop size filter if it was set and produced no results
    if not results and size is not None:
        results = search_listings(description, None, max_price)
        if results:
            session["search_results"] = results
            session["retry_note"] = (
                f"No results for size {size} — showing results without size filter."
            )
            size = None

    # Retry 2: drop price filter too if still no results
    if not results and max_price is not None:
        results = search_listings(description, None, None)
        if results:
            session["search_results"] = results
            session["retry_note"] = (
                f"No exact matches — removed size and price filters to find results."
            )
            size = None
            max_price = None

    # All retries exhausted → stop pipeline
    if not results:
        tried_filters = []
        if session["parsed"]["size"]:
            tried_filters.append(f"size {session['parsed']['size']}")
        if session["parsed"]["max_price"]:
            tried_filters.append(f"under ${session['parsed']['max_price']}")
        filter_str = " and ".join(tried_filters)
        session["error"] = (
            f"No results found{' for ' + filter_str if filter_str else ''} — "
            "even after removing size and price filters. "
            "Try a different description."
        )
        return session

    # ─────────────────────────────
    # Step 4: select top result (deterministic)
    # ─────────────────────────────
    selected_item = results[0]
    session["selected_item"] = selected_item

    # ─────────────────────────────
    # Step 5: suggest outfit
    # ─────────────────────────────
    try:
        outfit = suggest_outfit(selected_item, wardrobe)
        session["outfit_suggestion"] = outfit
    except Exception as e:
        session["error"] = f"Outfit generation failed: {str(e)}"
        return session

    # ─────────────────────────────
    # Step 6: create fit card
    # ─────────────────────────────
    try:
        fit_card = create_fit_card(outfit, selected_item)
        session["fit_card"] = fit_card
    except Exception as e:
        session["error"] = f"Fit card generation failed: {str(e)}"
        return session

    # ─────────────────────────────
    # Step 7: return final session
    # ────────────────────────────
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
