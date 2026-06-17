# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

# FitFindr

FitFindr is an AI-powered thrift assistant that takes a natural language query, finds secondhand listings, and generates a personalized outfit suggestion plus a shareable social caption — all in one pipeline.

```
python app.py
```

Then open the URL shown in your terminal (usually http://localhost:7860).

---

## How to Run

```bash
pip install -r requirements.txt
```

Create a `.env` file with your Groq API key (free at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

```bash
python app.py
```

---

## Tool Inventory

### Tool 1: `search_listings`

**Purpose:** Searches the mock thrift dataset for items matching a user's description, size, and price ceiling. Returns results ranked by keyword relevance so the most on-target listing surfaces first.

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `description` | `str` | Natural-language keywords (e.g. `"vintage graphic tee"`) |
| `size` | `str \| None` | Clothing size to filter by (e.g. `"M"`, `"S/M"`). `None` skips size filtering. |
| `max_price` | `float \| None` | Maximum price (inclusive). `None` skips price filtering. |

**Output:** `list[dict]` — each dict is a listing record containing `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`. Sorted by relevance, highest first. Returns `[]` when nothing matches.

**No LLM is used here.** The scoring is pure Python: count how many words from `description` appear in the listing's `title`, `description`, and `style_tags` fields (case-insensitive), drop any listing with a score of 0, and sort descending.

---

### Tool 2: `suggest_outfit`

**Purpose:** Given a thrift listing and the user's wardrobe, asks an LLM to suggest 1–2 complete outfits. If the wardrobe is empty, it falls back to general styling advice rather than failing.

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `new_item` | `dict` | A single listing dict from `search_listings` |
| `wardrobe` | `dict` | A wardrobe object with an `items` list of clothing records |

**Output:** `str` — A paragraph (or two) describing complete outfit combinations. When the wardrobe is non-empty, the LLM references specific wardrobe items by name. When the wardrobe is empty, it offers general advice about what types of pieces pair well with the thrift find.

**LLM call:** `llama-3.3-70b-versatile` via Groq, temperature 0.7.

---

### Tool 3: `create_fit_card`

**Purpose:** Turns the outfit suggestion into a 2–4 sentence social media caption styled like a real OOTD post. Each call uses a high temperature (0.9) so captions sound fresh for different inputs.

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `outfit` | `str` | The outfit suggestion text from `suggest_outfit` |
| `new_item` | `dict` | The listing dict used as the anchor piece |

**Output:** `str` — An Instagram/TikTok-style caption that mentions the item name, price, and platform once each and captures the outfit vibe in specific terms. Never returns `None` or an empty string.

**LLM call:** `llama-3.3-70b-versatile` via Groq, temperature 0.9.

---

## Planning Loop

The agent in `run_agent()` follows a **fixed, conditional pipeline** — not a loop that re-plans. The key insight is that each step either succeeds and hands data forward, or fails and stops execution immediately with a helpful message. No tool is called speculatively or without inputs from a prior step.

### What the agent decides at each step:

**Step 1 — Parse the query (no LLM)**
The agent extracts three parameters from the raw query using regex: `description`, `size`, and `max_price`. This is intentionally deterministic — regex is cheap, instant, and produces the same parse every time, which matters for reproducibility. An LLM parse would be slower, cost tokens, and could vary between calls. Extracted values are stored in `session["parsed"]`.

**Step 2 — Search for listings (with retry fallback)**
The agent calls `search_listings` with the extracted parameters. After this call, the agent checks: _did we get any results?_

- **If no results and size was specified:** the agent retries with `size=None`, dropping the size filter. If results are found, it stores a `retry_note` in the session and continues. Size is dropped first because it is the most restrictive filter in the dataset.
- **If still no results and max_price was specified:** the agent retries again with both `size=None` and `max_price=None`. If results are found, it stores a `retry_note` and continues.
- **If all retries fail:** the agent sets `session["error"]` naming which filters were tried and returns immediately. Tools 2 and 3 are never called.
- **If results exist** (from the initial search or any retry): the agent selects `results[0]` as the best match. Picking the top-scored item is a deliberate design choice — the scoring is already ranked, so index 0 is the most relevant result.

The `retry_note` is shown to the user in panel 1 (prepended to the listing text) so they always know when filters were loosened.

**Step 3 — Generate an outfit**
`suggest_outfit` is only called once the agent has a real `selected_item`. The agent passes both the item and the user's wardrobe. Internally, the tool itself makes a branch decision: empty wardrobe → general styling; non-empty wardrobe → outfit using named wardrobe pieces. Any exception here is caught and stored in `session["error"]`; the agent returns early rather than calling `create_fit_card` with no outfit.

**Step 4 — Create the fit card**
`create_fit_card` is only called when there is a valid outfit string. If the outfit string is somehow empty, the tool returns a fallback caption (never `None`). Exceptions are caught and stored in `session["error"]`.

**Step 5 — Return**
The agent returns the session dict. The caller checks `session["error"]` first; if set, only the first UI panel shows a message. If not set, all three panels populate.

### When the agent is "done"
The agent terminates after `create_fit_card` completes (or after any error). There is no re-planning, no retries, and no loops — the three tools form a strict dependency chain and each one runs at most once per user query.

---

## State Management

All state for one interaction lives in a single `session` dict initialized by `_new_session()`:

```python
{
    "query":             str,    # original user query, unchanged
    "parsed":            dict,   # {description, size, max_price} from regex
    "search_results":    list,   # full list returned by search_listings
    "selected_item":     dict,   # results[0], passed into tools 2 & 3
    "wardrobe":          dict,   # passed through from the UI unchanged
    "outfit_suggestion": str,    # output of suggest_outfit
    "fit_card":          str,    # output of create_fit_card
    "error":             str,    # set on any early-exit; None on success
    "retry_note":        str,    # set if a retry loosened constraints; None otherwise
}
```

**Why a single dict?** It makes state explicit and inspectable. Any point in the pipeline can read what happened before it, and the caller (Gradio) can check `session["error"]` before touching the output fields. There are no global variables and no side channels between tools.

**Data flow:**

```
user query (str)
    → regex parser
        → session["parsed"]
            → search_listings(description, size, max_price)
                → session["search_results"], session["selected_item"]
                    → suggest_outfit(selected_item, wardrobe)
                        → session["outfit_suggestion"]
                            → create_fit_card(outfit_suggestion, selected_item)
                                → session["fit_card"]
```

Each tool reads only from the session fields it needs and writes only one new field. No tool has access to the session dict itself — state passing is explicit via function arguments.

---

## Error Handling

| Tool / Step | Failure condition | What the agent does |
|-------------|-------------------|---------------------|
| `handle_query` | Empty or whitespace-only query string | Returns `("Please enter a search query.", "", "")` immediately — `run_agent` is never called |
| `search_listings` | Returns `[]` and size was specified | **Retry 1:** calls `search_listings(description, None, max_price)` without size filter. If results found, sets `session["retry_note"]` and continues. |
| `search_listings` | Still `[]` and max_price was specified | **Retry 2:** calls `search_listings(description, None, None)` without size or price filter. If results found, sets `session["retry_note"]` and continues. |
| `search_listings` | Still `[]` after all retries | Sets `session["error"]` naming which filters were tried. Returns session early — tools 2 and 3 are skipped entirely. |
| `suggest_outfit` | Raises an exception (e.g. API timeout) | Sets `session["error"]` with the exception message, returns session early. `create_fit_card` is not called. |
| `suggest_outfit` | `wardrobe["items"]` is empty | Handled internally: the tool switches to a general-styling prompt instead of raising or returning empty. The pipeline continues normally. |
| `create_fit_card` | `outfit` is empty or whitespace-only | Handled internally: returns a fallback caption built from `new_item` fields alone — never returns `None`. |
| `create_fit_card` | Raises an exception | Sets `session["error"]` with the exception message, returns session. |

### Concrete example from testing

**Query:** `"designer ballgown size XXS under $5"`

The listings dataset has no ballgowns priced under $5. `search_listings` returns `[]`. The agent immediately sets:

```python
session["error"] = (
    "No matching items found for your query. "
    "Try broadening your search — use fewer keywords, remove the size filter, "
    "or raise your price ceiling."
)
```

and returns. `suggest_outfit` and `create_fit_card` are never called. The Gradio UI shows the error message in panel 1 (with specific guidance on what to adjust) and leaves panels 2 and 3 empty.

**Query that triggers a retry:** `"vintage graphic tee size XXS under $30"`

`search_listings` finds no listings in size XXS under $30. The agent retries without the size filter: `search_listings("vintage graphic tee size XXS under $30", None, 30)` and finds results. `session["retry_note"]` is set to `"No results for size XXS — showing results without size filter."` The UI panel 1 shows the note above the listing so the user knows the filter was relaxed.

**Query with empty wardrobe:** `"vintage graphic tee under $30"` with `Empty wardrobe (new user)` selected.

`search_listings` finds results. `suggest_outfit` is called with `wardrobe = {"items": []}`. The tool detects the empty wardrobe and calls the LLM with a general-styling prompt instead of a wardrobe-matching prompt. Output: a paragraph about what kinds of bottoms and shoes pair well with graphic tees. `create_fit_card` runs normally and returns a caption. All three panels populate.

---

## Stretch Feature: Retry Logic with Fallback

When `search_listings` returns no results, the agent automatically retries with progressively looser constraints rather than immediately failing. This keeps the agent useful for queries that are slightly too specific.

**Retry sequence:**

1. **Drop size filter** — if the user specified a size and got no results, retry without it. Size is dropped first because it is the most restrictive filter in the 40-item dataset.
2. **Drop price filter** — if still no results and the user specified a price ceiling, retry with no filters at all (description-only search).
3. **Fail gracefully** — if all retries fail, return an error message that names exactly which filters were tried, so the user knows to change their description.

**Transparency:** Every retry that finds results sets `session["retry_note"]` with a plain-English explanation (e.g. `"No results for size XXS — showing results without size filter."`). This note is prepended to the listing panel in the UI so the user always knows when their search was automatically widened.

**What doesn't change:** The original parsed values (`session["parsed"]["size"]`, `session["parsed"]["max_price"]`) are never overwritten — they preserve the user's intent. Only the local variables used for the retry calls are loosened.

---

## Spec Reflection

**What matched the spec well:**
- The fixed pipeline structure (search → outfit → caption) mapped cleanly to the session dict approach. State passing via explicit function arguments rather than implicit shared state made each tool easy to test in isolation.
- The early-exit on empty search results is exactly what the spec called for and made the no-results path trivially easy to test.

**What I changed from my original plan:**
- The planning.md described stripping size and price tokens from the raw query to create a cleaner `description`. In practice, leaving the full query as the description worked better for scoring — common words like "vintage" that appear in both the query and listings contributed to the relevance score. Stripping produced shorter, sometimes over-filtered descriptions.
- The initial plan used `llama3-8b-8192` for the LLM calls. I switched to `llama-3.3-70b-versatile` after noticing the smaller model produced noticeably blander outfit suggestions that didn't reference wardrobe item names consistently.

**What I'd do differently:**
- Add a minimum-score threshold to `search_listings` (e.g. require score ≥ 2) to avoid surfacing weak keyword matches as the top result. Currently a query like `"blue jeans size M"` could surface a listing that only matched the word "blue."
- Surface the full `search_results` list in the UI so users can browse alternatives, not just the top pick.

---

## AI Usage

### Instance 1: Implementing `suggest_outfit`

**What I gave the AI:**
- The Tool 2 spec section from `planning.md` (inputs, return type, failure modes)
- The wardrobe schema field names (`name`, `category`, `colors`, `style_tags`)
- The `_get_groq_client()` helper already in `tools.py`
- The agent architecture diagram showing the empty-wardrobe branch

**What it produced:**
A `suggest_outfit()` implementation with two branches (empty vs. non-empty wardrobe), each building a different prompt string and calling the Groq API. The logic matched the spec closely.

**What I changed:**
The generated code assumed every wardrobe item had `colors` and `style_tags` keys and directly joined them without defensive checks. In the actual wardrobe data, some items use `None` for these fields. I added `or []` fallbacks to `.get('colors', [])` and `.get('style_tags', [])` to prevent `TypeError: argument of type 'NoneType' is not iterable`. I also changed the model from `llama3-8b-8192` to `llama-3.3-70b-versatile` after testing showed more specific outfit references.

---

### Instance 2: Implementing `run_agent` (the planning loop)

**What I gave the AI:**
- The full Planning Loop section of `planning.md` (Steps 1–7)
- The State Management section with the session dict structure
- The `_new_session()` function body already in `agent.py`
- The query parsing pseudocode from Step 1b

**What it produced:**
A `run_agent()` implementation that followed the 7-step structure almost exactly: regex parse → search → early exit on empty → select top result → suggest outfit → create fit card → return session. The regex patterns for size and price extraction matched what was described in planning.md.

**What I changed:**
The generated regex for price extraction (`r"(?:under|below|<)?\s*\$?(\d+)"`) was overly broad — it matched any number in the query, including size numbers. For the query `"track jacket size 10 under $40"`, it extracted `10` instead of `40` because `10` appeared first. I added word-boundary anchors and made the price-indicator words (`under`, `below`) required when no `$` sign is present, tightening the match to actual price expressions.
