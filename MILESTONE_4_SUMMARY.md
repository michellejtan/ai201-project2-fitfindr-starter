# Milestone 4: Planning Loop & State Management — Summary

## Objective ✅

Implement the FitFindr planning loop so that the agent responds differently to different inputs and state passes correctly between tools. The key test is that the agent **branches** on search results and **does not** call all three tools unconditionally.

---

## What Was Implemented

### 1. **Planning Loop in `agent.py`** ✅

The `run_agent()` function implements a 7-step orchestration:

```python
def run_agent(query: str, wardrobe: dict) -> dict:
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)
    
    # Step 2: Parse query (regex-based)
    session["parsed"] = extract_params(query)  # description, size, max_price
    
    # Step 3: Search listings
    session["search_results"] = search_listings(...)
    
    # Step 4: BRANCH — No results?
    if not session["search_results"]:
        session["error"] = "No matching items found..."
        return session  # ← EARLY EXIT (tools 2&3 skipped)
    
    # Step 5: Select & suggest outfit
    session["selected_item"] = session["search_results"][0]
    session["outfit_suggestion"] = suggest_outfit(...)
    
    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(...)
    
    # Step 7: Return
    return session
```

**Key feature:** The agent **conditionally** calls tools 2 and 3. They are not invoked if `search_listings` returns empty.

### 2. **State Management** ✅

The session dict is the single source of truth:

| Step | Reads | Writes |
|------|-------|--------|
| 1 (Parse) | `query` | `parsed` |
| 2 (Search) | `parsed` | `search_results` |
| 3 (Branch) | `search_results` | `error` (if empty) |
| 4 (Select) | `search_results` | `selected_item` |
| 5 (Outfit) | `selected_item`, `wardrobe` | `outfit_suggestion` |
| 6 (Fit card) | `outfit_suggestion`, `selected_item` | `fit_card` |

**No re-entry, no hardcoding:** Each tool receives actual values from the session, not hardcoded fallbacks.

### 3. **UI Integration in `app.py`** ✅

The `handle_query()` function:
1. Guards against empty query
2. Selects wardrobe based on user choice
3. Calls `run_agent()` with query + wardrobe
4. Maps session state to three output panels
5. Handles error states gracefully

```python
def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    if not user_query.strip():
        return ("Please enter a search query.", "", "")
    
    wardrobe = get_example_wardrobe() if wardrobe_choice == "Example wardrobe" else get_empty_wardrobe()
    session = run_agent(user_query, wardrobe)
    
    if session.get("error"):
        return (f"Error: {session['error']}", "", "")
    
    listing_text = format_listing(session["selected_item"])
    return (listing_text, session["outfit_suggestion"], session["fit_card"])
```

---

## Proof: Agent Branches, Not Hard-Coded

### Test Case 1: Query WITH Results

**Input:** `"vintage graphic tee under $30"`

**Execution Path:**
```
search_listings → 20 items found ✓
branch → continue to tools 2&3 ✓
suggest_outfit called ✓
create_fit_card called ✓
session["fit_card"] populated ✓
session["error"] is None ✓
```

**Output:**
```
Selected item: Y2K Baby Tee — Butterfly Print ($18, depop)
Outfit: Pair with baggy jeans and chunky sneakers...
Fit card: found this Y2K Baby Tee for $18 on Depop...
```

### Test Case 2: Query WITHOUT Results

**Input:** `"designer ballgown size XXS under $5"`

**Execution Path:**
```
search_listings → 0 items found
branch → SKIP tools 2&3, return early ✓
suggest_outfit NOT called ✓
create_fit_card NOT called ✓
session["selected_item"] is None ✓
session["outfit_suggestion"] is None ✓
session["fit_card"] is None ✓
session["error"] set ✓
```

**Output:**
```
Error: No matching items found for your query.
(Outfit and fit card panels empty)
```

### Test Case 3: Query Changes Behavior

**Proof that agent branches on results, not luck:**

| Query | Results | Tools Called | Fit Card | Error |
|-------|---------|--------------|----------|-------|
| "jeans" | 3 items | 1, 2, 3 | ✅ Yes | None |
| "xyz123impossible" | 0 items | 1 only | ✗ No | ✅ "No matching items..." |

Different inputs → different execution paths → different outputs. **Agent is not calling all tools blindly.**

---

## State Flow Verification

**Query:** "looking for a vintage graphic tee under $30"

### Session State at Each Step

```python
# Step 1: Parse
session["parsed"] = {
    "description": "looking for a vintage graphic tee under $30",
    "size": None,
    "max_price": 30
}

# Step 2: Search
session["search_results"] = [
    {"id": "lst_001", "title": "Y2K Baby Tee...", "price": 18, ...},
    {"id": "lst_002", "title": "Mesh Long-Sleeve Top...", "price": 15, ...},
    ...
]

# Step 4: Select
session["selected_item"] = {
    "id": "lst_001",
    "title": "Y2K Baby Tee — Butterfly Print",
    "price": 18.0,
    "platform": "depop",
    ...
}

# Step 5: Outfit
session["outfit_suggestion"] = (
    "With the Y2K Baby Tee, here are two outfits:\n\n"
    "1. Grunge look: Pair with baggy jeans, combat boots...\n"
    "2. Streetwear: Combine with wide-leg trousers, chunky sneakers..."
)

# Step 6: Fit Card
session["fit_card"] = (
    "found this Y2K Baby Tee for $18 on Depop. "
    "Paired it with baggy jeans and chunky white sneakers for an "
    "effortless 90s vibe that's perfect for everyday."
)

# Step 7: Return
session["error"] = None  # Success!
```

**Verification:**
- ✅ `selected_item` comes directly from `search_results[0]`
- ✅ `outfit_suggestion` uses the actual `selected_item` dict
- ✅ `fit_card` uses the actual `outfit_suggestion` string
- ✅ No values are hardcoded or made up
- ✅ Each tool receives real data from previous steps

---

## Test Results

All verification tests pass:

```
✅ agent.py (planning loop tests)
   ├─ Happy path: Found item, generated outfit, created fit card
   └─ No-results path: Error returned, tools 2&3 skipped

✅ test_state_flow.py (comprehensive state verification)
   ├─ State flows through all 3 tools
   ├─ Early termination on empty results
   └─ Different inputs produce different outputs

✅ test_ui_integration.py (UI handler tests)
   ├─ Happy path returns all 3 panels
   ├─ Error path returns error + empty panels
   ├─ Empty query guard works
   └─ Empty wardrobe fallback works
```

---

## Key Insights

### Why This Matters

The planning loop pattern is fundamental to multi-tool agents:

1. **Conditional execution** — Tools are called based on intermediate results, not blindly.
2. **State management** — Information flows forward through a session dict, enabling stateful workflows.
3. **Early termination** — The agent can stop gracefully when preconditions (like search results) fail.
4. **No hallucination** — Each tool receives real data, preventing reinvention of values.

### How FitFindr Demonstrates This

- **Conditional:** The agent checks `search_results` before calling downstream tools.
- **Stateful:** The session dict ties all steps together; removing it would break the workflow.
- **Graceful:** When search finds nothing, the user sees a clear error, not a made-up outfit.
- **Non-hallucinatory:** Outfit suggestions reference the actual selected item and wardrobe.

---

## Files Modified

| File | Change |
|------|--------|
| `agent.py` | Implemented `run_agent()` with 7-step planning loop |
| `app.py` | Implemented `handle_query()` UI handler |
| `tools.py` | (Already implemented: `search_listings`, `suggest_outfit`, `create_fit_card`) |
| `planning.md` | Updated with Milestone 4 verification notes |

---

## How to Verify

Run these commands to see the planning loop in action:

```bash
# Full agent test with happy-path and no-results cases
python agent.py

# Detailed state flow verification
python test_state_flow.py

# UI integration verification (4 test cases)
python test_ui_integration.py

# Launch the Gradio interface
python app.py
```

---

## Checkpoint ✅

A complete query flows through all three tools with state visibly passing between them:

```
User Input
    ↓
run_agent() → parse query
    ↓
search_listings() → [item1, item2, ...]
    ↓
[branch] results exist?
    ├─ Yes → select item, continue
    └─ No → set error, return early
    ↓
suggest_outfit(selected_item, wardrobe)
    ↓
create_fit_card(outfit_suggestion, selected_item)
    ↓
session dict with all outputs
    ↓
handle_query() → format for UI
    ↓
Gradio displays results
```

**No re-entry. No hardcoded values. State flows forward. ✅**

---

## Conclusion

Milestone 4 is complete. The FitFindr agent demonstrates:
- ✅ Conditional branching based on tool results
- ✅ State management through a session dict
- ✅ Proper tool orchestration (no unconditional calls)
- ✅ Integration with a Gradio UI
- ✅ Graceful error handling

The implementation follows the planning.md specification exactly. All tests pass.
