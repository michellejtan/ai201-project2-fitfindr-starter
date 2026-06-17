# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches through the thrift listings dataset and returns items that match a user’s description, size, and budget constraints. It filters and ranks results so the most relevant items appear first.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str):  A natural language description of the desired item (e.g., "vintage graphic tee")
- `size` (str): Clothing size filter (string match; may include formats like "S", "M", "W30 L30", "S/M", "One Size")
- `max_price` (float | None): Optional maximum price. If `None`, no price filtering is applied, listings are filtered only by description and size.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of listing dictionaries. Each listing contains:
- id (str)
- title (str)
- description (str)
- category (str)
- style_tags (list[str])
- size (str)
- condition (str)
- price (float)
- colors (list[str])
- brand (str | None)
- platform (str)

If matches exist, results are sorted by relevance (best match first).


**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If no listings match, the tool returns an empty list `[]`. 
The agent must inform the user and suggest loosening constraints (price, size, or description). Return a message: "I couldn’t find any matching listings. Try adjusting your description, size, or price range and I’ll search again."
The workflow stops immediately (do not call further tools).


---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates outfit combinations using a selected thrift item and the user’s existing wardrobe. It produces styling suggestions that integrate the new item into complete looks.


**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A single listing object returned from `search_listings`
- `wardrobe` (dict): A structured list of the user’s existing clothing items


**What it returns:**
<!-- Describe the return value -->
A structured outfit suggestion that describes how to style the selected `new_item` using pieces from the user's wardrobe. The output includes a natural-language outfit description (e.g., top + bottom + shoes + accessories combinations when possible) and may reference specific wardrobe item names or categories.

Example output:
"Pair the vintage graphic tee with baggy dark-wash jeans and chunky white sneakers. Layer with the oversized grey crewneck for a relaxed streetwear look."

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty (`wardrobe["items"] == []`), the tool returns a fallback outfit suggestion using only the `new_item`, focusing on general styling advice without wardrobe matching.

If no coherent outfit can be generated (e.g., missing or malformed inputs), the tool returns a simple fallback message like:
"Style this item as a standalone statement piece or pair it with basic essentials like jeans and sneakers."

The agent must still continue execution to `create_fit_card` as long as a valid `new_item` exists.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates a short, social-media-style “fit card” caption based on a completed outfit and the selected thrift item. The goal is to turn the outfit into a shareable, aesthetic description similar to an Instagram caption or outfit post.


**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str or dict): A natural-language outfit description produced by `suggest_outfit`
- `new_item` (dict): The selected listing object from `search_listings` used as the base piece of the outfit


**What it returns:**
<!-- Describe the return value -->
A single short text caption styled like a social media post. It should be concise, aesthetic, and slightly informal, describing the outfit and vibe.
Example:
"found this faded band tee for $24 and built the whole look around it—baggy jeans, chunky sneakers, and effortless grunge energy."



**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If the `outfit` input is missing or incomplete, the tool generates a fallback caption using only the `new_item`, focusing on the vibe of the selected piece.
Example fallback:
"picked up this vintage piece and styled it with everyday basics—clean, simple, and effortlessly wearable."

The tool should never return `None`; it must always produce a usable caption string for the agent to pass back to the user.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
No additional tools are required for this implementation. The agent uses only:
- search_listings
- suggest_outfit
- create_fit_card

---

## Stretch Feature: Retry Logic with Fallback

### What it does
When `search_listings` returns no results, the agent automatically retries with progressively looser constraints instead of immediately failing. It informs the user exactly what filter was removed, so they understand why the results changed.

### Retry sequence (implemented in `run_agent()` in `agent.py`)

**Retry 1 — drop size filter:**
```python
if not results and size is not None:
    results = search_listings(description, None, max_price)
    if results:
        session["retry_note"] = f"No results for size {size} — showing results without size filter."
        size = None
```

**Retry 2 — drop price filter too:**
```python
if not results and max_price is not None:
    results = search_listings(description, None, None)
    if results:
        session["retry_note"] = "No exact matches — removed size and price filters to find results."
        size = None
        max_price = None
```

**All retries exhausted:**
```python
if not results:
    session["error"] = f"No results found for {filter_str} — even after removing size and price filters. Try a different description."
    return session
```

### State additions
A new `retry_note` field is added to the session dict:
```python
"retry_note": None  # set to a string if any retry was triggered; None otherwise
```

If `retry_note` is set, `handle_query()` in `app.py` prepends it to the listing panel output so the user sees which filter was removed.

### Design decisions
- Size is dropped before price because size is more restrictive in the dataset — many users want a specific price range but are flexible on size.
- The original parsed values (`session["parsed"]["size"]`, `session["parsed"]["max_price"]`) are never modified — they preserve the user's original intent for display in the UI.
- Only the local variables `size` and `max_price` are updated during retries so downstream tools use the relaxed values.
- The retry is transparent: the note always tells the user what changed, not just that results were found.

### Error handling for this feature
| Condition | Agent response |
|-----------|---------------|
| Retry 1 finds results | Sets `retry_note`, continues pipeline normally |
| Retry 2 finds results | Sets `retry_note`, continues pipeline normally |
| All retries fail | Sets `session["error"]` naming which filters were tried, returns early |

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The agent follows a fixed decision-making loop that processes the user request step-by-step and updates internal state after each tool call. It does not call all tools blindly; instead, each step depends on the output of the previous one.

### Step 1 — Parse user input
Extract:
- `description` (required, string — keywords describing the item)
- `size` (optional string — `None` if the user doesn't specify one, skipping size filtering)
- `max_price` (optional float — `None` if the user doesn't specify a price, skipping price filtering)

---

### Step 1b — Query parsing detail

Query parsing uses regex before calling any LLM. This keeps it fast, free, and deterministic.

**Size extraction** — scan for common clothing size tokens (case-insensitive):
- Letter sizes: `\b(XXS|XS|S|M|L|XL|XXL|XXXL|S\/M|M\/L|L\/XL)\b`
- Numeric sizes: `\bsize\s+(\d{1,2}(?:\.\d)?)\b` (e.g. "size 8", "size 10.5")
- Waist/length: `\bW(\d{2})\s*L(\d{2})\b`
- "One Size": `\bone\s*size\b`

If no size token is found, `size` is left as `None` (no size filter applied).

**Price extraction** — scan for price patterns:
- `under\s+\$?(\d+(?:\.\d{2})?)` → e.g. "under $30"
- `\$(\d+(?:\.\d{2})?)\s*(?:or less|max|maximum)?`
- `less than\s+\$?(\d+(?:\.\d{2})?)`
- `budget\s+(?:of\s+)?\$?(\d+(?:\.\d{2})?)`

If no price pattern is found, `max_price` is left as `None` (no price filter applied).

**Description extraction** — after stripping the size and price tokens from the raw query string, the remaining text is used as the description. Common stop-words ("I'm looking for", "find me", "I want") are stripped. If the result is blank, the full original query is used as a fallback.

```python
# Pseudocode
size = extract_size(query)        # regex, returns str or None
max_price = extract_price(query)  # regex, returns float or None
description = strip_tokens(query, size, max_price)  # remaining text
session["parsed"] = {"description": description, "size": size, "max_price": max_price}
```

---

### Step 2 — Search listings
Call:
```python
results = search_listings(description, size, max_price)
```

### Step 3 — Handle search results (with retry fallback)
BEFORE STRETCH GOAL:
IF results is `empty`:

return error message to user
STOP execution immediately
AFTER IMPLEMENT STRETCH GOAL:
IF results is `empty` AND size was specified:
- Retry: call `search_listings(description, None, max_price)` (drop size filter)
- If results found: store `retry_note` in session, set `size = None`, continue

IF still empty AND max_price was specified:
- Retry: call `search_listings(description, None, None)` (drop price filter too)
- If results found: store `retry_note` in session, continue

IF still empty after all retries:
- Set `session["error"]` naming which filters were tried
- STOP execution immediately

ELSE (results exist, either from initial search or a retry):

set `selected_item = results[0]`
Always store:
- search_results = results
- retry_note = message describing what was loosened (or None if no retry needed)

### Step 4 — Generate outfit

Call:
```python
outfit = suggest_outfit(selected_item, wardrobe)
```
The result is stored in outfit.

### Step 5 — Generate fit card

Call:
```python
fit_card = create_fit_card(outfit, selected_item)
```
The result is stored as `fit_card` and represents the final generated caption.

### Step 6 — Return response (Termination condition)
The loop ends after `create_fit_card` executes successfully. At this point, all required outputs exist:
- selected_item
- outfit
- fit_card

The agent ensures all outputs are derived from state and no tool is called after termination.
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent maintains session-level state so information can persist across multiple tool calls during a single interaction.
### State structure

```python
state = {
    "selected_item": None,
    "outfit": None,
    "fit_card": None,
    "wardrobe": {"items": []},
    "last_search_results": [],
    "last_query": None,
    "retry_note": None,   # set if search was retried with looser constraints
}
```

## How state is updated

### After `search_listings`
- Store full results in `last_search_results`
- Set `selected_item = results[0]` (if results exist)

### After `suggest_outfit`
- Store output in `outfit`

### After `create_fit_card`
- Store output in `fit_card`

---

## How state is used

- `selected_item` is passed into:
  - `suggest_outfit`
  - `create_fit_card`

- `wardrobe` is passed into:
  - `suggest_outfit`

- `outfit` is passed into:
  - `create_fit_card`


---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

Each tool includes explicit failure handling to prevent silent failures and ensure the agent always responds meaningfully to the user.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results — size filter too restrictive | Retry without size filter; set `retry_note` in session to inform user |
| search_listings | No results — price filter too restrictive | Retry without size and price filters; set `retry_note` in session |
| search_listings | No results after all retries | Return error message naming which filters were tried; stop workflow immediately |
| suggest_outfit | Wardrobe is empty (`wardrobe["items"] == []`)| Generate a fallback outfit using only the selected item without wardrobe matching |
| create_fit_card | Outfit input is missing or incomplete | Generate a fallback caption using only the selected item |

### General rules

- The agent must never crash or return `None`
- The agent must always return a user-facing message, even in failure cases
- If `search_listings` fails after all retries, no further tools are executed
- All fallback behavior must still produce a usable output for the user
- Retry attempts are transparent — the user always sees which filter was relaxed
---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

FitFindr has four layers: a Gradio UI (`app.py`), a planning loop (`agent.py`), three tools (`tools.py`), and a session state dict that threads data between them.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  User (Gradio UI — app.py)                                                  │
│  Inputs: user_query (str), wardrobe (dict)                                  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ user_query == ""
                               ├──────────────────► [ERROR] Return error to UI
                               │
                               │ valid query + wardrobe dict
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Planning Loop — run_agent() in agent.py                                    │
│  Session state: { query, parsed, search_results, selected_item,             │
│                   wardrobe, outfit_suggestion, fit_card, error,             │
│                   retry_note }                                              │
│                                                                             │
│  Step 1 — Regex parse query                                                 │
│      description (str), size (str|None), max_price (float|None)             │
│      Session: parsed = { description, size, max_price }                     │
│               │                                                             │
│  Step 2 ──────┘                                                             │
│      │                                                                      │
│      ▼                                                                      │
│  search_listings(description, size, max_price)        ┌─────────────────┐  │
│      │                                                │  Session State  │  │
│      │ results == [] AND size set                     │                 │  │
│      ├──► Retry 1: search_listings(desc, None, price) │  search_results │  │
│      │       │ results found → set retry_note         │  selected_item  │  │
│      │       │ results == [] AND max_price set        │  outfit_suggest │  │
│      │       └──► Retry 2: search_listings(desc,None,None)  fit_card   │  │
│      │               │ results found → set retry_note │  error          │  │
│      │               │ results == [] (all retries done)│  retry_note    │  │
│      │               └──► [ERROR] "No results after   │                 │  │
│      │                    retries" ─► return early ◄──┤                 │  │
│      │                                                │                 │  │
│      │ results = [item, ...]                          │                 │  │
│      ▼                                                │                 │  │
│  Session: selected_item = results[0]  ────────────────►                 │  │
│      │                                                └─────────────────┘  │
│      ▼                                                                      │
│  suggest_outfit(selected_item, wardrobe)                                    │
│      │                                                                      │
│      │ wardrobe["items"] == []                                              │
│      ├──► LLM: item-only general styling advice                             │
│      │                                                                      │
│      │ wardrobe["items"] is non-empty                                       │
│      ├──► LLM: outfit pairing new item with named wardrobe pieces           │
│      │                                                                      │
│      ▼                                                                      │
│  Session: outfit_suggestion = "..." ──────────────────► Session State       │
│      │                                                                      │
│      ▼                                                                      │
│  create_fit_card(outfit_suggestion, selected_item)                          │
│      │                                                                      │
│      │ outfit_suggestion is empty/whitespace                                │
│      ├──► fallback caption (item-only, never returns None)                  │
│      │                                                                      │
│      │ outfit_suggestion is valid                                           │
│      ├──► LLM: Instagram-style caption (temp=0.9)                          │
│      │                                                                      │
│      ▼                                                                      │
│  Session: fit_card = "..." ───────────────────────────► Session State       │
│                                                                             │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ return session dict
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  User (Gradio UI — app.py)                                                  │
│  Panel 1: selected listing (title, price, platform, condition)              │
│  Panel 2: outfit_suggestion                                                 │
│  Panel 3: fit_card caption                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key data flows:**

| From | To | Data |
|------|----|------|
| `handle_query` | `run_agent` | raw query string + wardrobe dict |
| Regex parser | `search_listings` | description (str), size (str\|None), max_price (float\|None) |
| `search_listings` | `suggest_outfit` | `selected_item` dict (results[0]) |
| `run_agent` | `suggest_outfit` | `wardrobe` dict (passed through session) |
| `suggest_outfit` | `create_fit_card` | outfit suggestion string |
| `create_fit_card` | `handle_query` | fit card caption string (via session) |

**Error paths:**

| Where | Condition | Outcome |
|-------|-----------|---------|
| `handle_query` | empty query string | return error in panel 1, skip agent |
| `search_listings` | returns `[]`, size was set | Retry without size filter; set `retry_note` if found |
| `search_listings` | still `[]`, max_price was set | Retry without size or price filter; set `retry_note` if found |
| `search_listings` | still `[]` after all retries | set `session["error"]`, return session immediately — tools 2 & 3 never called |
| `suggest_outfit` | `wardrobe["items"] == []` | LLM generates item-only advice — continues to `create_fit_card` |
| `create_fit_card` | empty outfit string | returns fallback caption — never returns `None` |
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

### Tool 1: `search_listings`

**AI tool:** Claude (in this editor)

**What I'll give it:**
- The Tool 1 spec from this file (inputs, return value, failure mode)
- The `load_listings()` docstring from `utils/data_loader.py` showing the field names
- Instruction: "Implement `search_listings` in tools.py using only the Python standard library (no LLM call). Score each listing by counting how many words from `description` appear in the listing's `title`, `description`, and `style_tags` fields (case-insensitive). Filter out listings with score 0, sort descending by score, and return the list."

**What I expect it to produce:**
A working `search_listings()` that filters by price and size, scores by keyword overlap, and returns a sorted list of dicts.

**How I'll verify it:**
Run these 3 queries manually before moving on:
1. `search_listings("vintage graphic tee", "M", 30)` → expect ≥1 result, all priced ≤ $30
2. `search_listings("90s track jacket", "M", None)` → expect results including lst_004
3. `search_listings("designer ballgown", "XXS", 5)` → expect `[]` (empty)

---

### Tool 2: `suggest_outfit`

**AI tool:** Claude (in this editor)

**What I'll give it:**
- The Tool 2 spec from this file (inputs, return value, failure mode)
- The `wardrobe_schema.json` example showing exact field names (`name`, `category`, `colors`, `style_tags`, `notes`)
- The `_get_groq_client()` helper already in tools.py
- Instruction: "Implement `suggest_outfit` using the Groq client. If `wardrobe['items']` is empty, ask the LLM for general styling advice only using the new_item's title, style_tags, and colors. If the wardrobe is non-empty, format each wardrobe item as `{name} ({category}, {colors}, style: {style_tags})` and ask the LLM to suggest 1–2 complete outfits that pair the new_item with specific named pieces. Use model `llama3-8b-8192`, temperature 0.7."

**What I expect it to produce:**
A `suggest_outfit()` that returns a non-empty string in both the empty-wardrobe and full-wardrobe cases.

**How I'll verify it:**
1. Call with a sample listing dict + example wardrobe → output should mention at least one wardrobe item by name
2. Call with same listing + empty wardrobe (`{"items": []}`) → output should still be a useful styling paragraph, not empty

---

### Tool 3: `create_fit_card`

**AI tool:** Claude (in this editor)

**What I'll give it:**
- The Tool 3 spec from this file (inputs, return value, failure mode, caption style guidelines)
- The `_get_groq_client()` helper
- Instruction: "Implement `create_fit_card` using the Groq client. Guard: if `outfit` is empty or whitespace-only, return a fallback string that still describes the item. Otherwise, prompt the LLM with the item's title, price, platform, and the outfit string, asking for a 2–4 sentence Instagram-style caption that mentions the item name, price, and platform once each and captures the outfit vibe. Use model `llama3-8b-8192`, temperature 0.9 (higher for variety)."

**What I expect it to produce:**
A `create_fit_card()` that always returns a non-empty string and sounds casual/authentic.

**How I'll verify it:**
1. Call twice with the same inputs — captions should differ (confirming high temperature is working)
2. Call with `outfit=""` → expect a fallback caption string, not an empty string or exception
3. Check that the item name, price (`$XX`), and platform appear in the output

---

**Milestone 4 — Planning loop and state management:**
**AI tool:** Claude (in this editor)

**What I'll give it:**
- The `agent.py` skeleton (the `_new_session` dict and the `run_agent` TODO comments)
- The Planning Loop section of this file (Steps 1–7)
- The State Management section of this file
- The query parsing pseudocode from Step 1b above
- Instruction: "Implement `run_agent()` in agent.py. Use the regex parsing approach described in planning.md to extract description, size, and max_price from the query string. Call the three tools in order, store results in the session dict at each step, and return the session early (with `session['error']` set) if `search_listings` returns an empty list."

**What I expect it to produce:**
A working `run_agent()` that passes the happy-path and no-results tests in `agent.py`'s `__main__` block.

**How I'll verify it:**
Run `python agent.py` directly. It exercises two paths:
1. Happy path: should print a `selected_item` title, a non-empty outfit, and a fit card
2. No-results path: should print a helpful error message and no outfit/fit-card output

Once both pass, I'll wire up `handle_query()` in `app.py` using the same session dict fields and run `python app.py` to do a final UI smoke test.

**Status:** ✅ COMPLETE — VERIFIED

**Implementation details:**
- `run_agent()` in `agent.py` is fully implemented with all 7 steps from the planning loop
- Query parsing uses regex to extract description, size, and max_price (deterministic, no LLM)
- The agent branches correctly: returns early with error if `search_listings` returns empty list
- State flows correctly through the session dict:
  - `search_listings` result → `selected_item`
  - `selected_item` + `wardrobe` → `outfit_suggestion` 
  - `outfit_suggestion` + `selected_item` → `fit_card`
- `handle_query()` in `app.py` properly maps session dict to UI panels and handles error states
- All three tools are only called when needed (no unconditional execution)

**Verification (All tests passing):**
✅ `python agent.py` — Happy-path and no-results branch tests pass
✅ `python test_state_flow.py` — Comprehensive state flow verification (3 tests)
✅ `python test_ui_integration.py` — UI integration tests (4 tests)
✅ Agent branches conditionally: tools 2&3 skipped when search_listings returns empty
✅ Different inputs produce different outputs (not hard-coded)
✅ State flows: search_results → selected_item → outfit_suggestion → fit_card
✅ No re-entry, no hardcoded values, proper error handling
✅ See VERIFICATION_REPORT.md for detailed test results

---

## A Complete Interaction (Step by Step)

FitFindr takes a user’s natural language request for secondhand clothing and first uses `search_listings` to retrieve matching items from a mock dataset based on description, size, and price constraint. If a valid listing is found, it passes the selected item along with the user’s wardrobe to `suggest_outfit`, and then sends the resulting outfit into `create_fit_card` to generate a shareable caption. If `search_listings` returns no results, the agent stops immediately and returns a message asking the user to adjust their search instead of continuing the workflow.

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
search_listings
The agent first parses the user request to extract the item type, size, and price constraint. It then calls `search_listings` using the extracted values.
Tool call:
```python
search_listings(
    description="vintage graphic tee",
    size="M",
    max_price=30
)
```
The tool returns a list of matching listings. The agent selects the first (most relevant) result and stores it as selected_item.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
suggest_outfit
The agent receives the results from `search_listings` and checks whether the list is empty. Since at least one listing is returned, it selects the first (most relevant) item and stores it as `selected_item`.

It then retrieves the user’s wardrobe (using the example wardrobe from `get_example_wardrobe()`) and calls `suggest_outfit` with both inputs.

Tool call:
```python
suggest_outfit(
    new_item=selected_item,
    wardrobe=wardrobe
)
```
The tool returns an outfit suggestion describing how to style the selected thrift item with pieces from the user’s wardrobe. The agent stores this output as `outfit`.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The agent generates a shareable caption:
```python
create_fit_card(outfit, selected_item)
```

Returns:
A short social-media-style “fit card” caption describing the look

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user receives a combined response containing:
- The selected listing (title, price, platform, and key details)
- A styling suggestion using their wardrobe
- A generated “fit card” caption suitable for sharing on social media