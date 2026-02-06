# Code Deep Dive: AI Core (`miner.py` & `detective.py`)

**Role:** The Intelligence Layer.
**Responsibility:** Transforms unstructured text (Reviews, Chat) into structured data and actionable insights using Large Language Models (Gemini).

---

## 1. `AIMiner` (`scout_app/core/miner.py`)
**Role:** The Heavy Lifter. Batches thousands of reviews and extracts structured Aspect/Sentiment tags.

### Key Logic & Atomic Functions

#### `get_unmined_reviews(limit, status)`
- **Logic:**
    1.  **Trash Filter (Atomic):** Automatically finds reviews with `length <= 10` chars. Instead of wasting AI tokens, it *auto-injects* a generic "Satisfaction" tag based on rating (4-5 -> Pos, 1-2 -> Neg).
    2.  **Selection:** Fetches reviews with `mining_status='PENDING'`.

#### `run_live(limit)`
- **Role:** Immediate execution (Worker Thread).
- **Atomic Logic:** "Contextual Locking Strategy"
    1.  **Locking:** Immediately updates status to `'QUEUED'` to prevent other workers from picking up the same batch.
    2.  **Prompting:** Builds a prompt containing ~50 reviews at once (Context Window Optimization).
    3.  **Parsing:** `_save_tags_to_db` uses Regex/JSON repair logic to handle LLM hallucinations or malformed JSON.
    4.  **Completion:** Updates status to `'COMPLETED'`.
    5.  **Trigger:** Calls `StatsEngine.calculate_and_save` for affected ASINs immediately after mining.

#### `prepare_batch_file(limit)`
- **Role:** Cost Optimization.
- **Logic:** Instead of calling the API directly, it writes a JSONL file formatted for Gemini Batch API (50% cheaper).

### Dependency Graph
- **Upstream:** `worker_api.py` (/trigger/miner).
- **Downstream:** `DuckDB` (Read reviews, Write review_tags), `Gemini API`, `StatsEngine`.

---

## 2. `DetectiveAgent` (`scout_app/core/detective.py`)
**Role:** The Interactive Analyst. Handles user queries via a Chat Interface.

### Atomic Logic: "The Tool Dispatcher"

#### `answer(user_query, default_asin)`
- **Logic:**
    1.  **System Prompt Injection:** Injects "Standard Aspects" from DB (`_get_vocabulary`) into the System Prompt so the AI knows the domain language.
    2.  **Loop Prevention (Atomic):** Maintains a `previous_tool_calls` list. If the AI calls the same tool with the exact same arguments twice, it intercepts the call and returns a "SYSTEM ERROR" message to force the AI to stop looping.
    3.  **Argument Injection:** If the AI forgets to pass the `asin` (common with "Tell me about *this* product"), the code automatically injects `default_asin` from the session context.
    4.  **Tool Execution:** Maps function names (e.g., `get_product_dna`) to actual Python methods.

#### `analyze_competitors(asin)`
- **Role:** Specific Tool Logic.
- **Logic:**
    1.  **DNA Fetch:** Gets Category/Niche of the current product.
    2.  **Strict Match:** Queries DB for other products in the *exact same Category*.
    3.  **Weakness Mapping:** Identifies current product's top Negative aspects.
    4.  **Advantage Search:** Checks if competitors have Positive sentiment for those specific aspects.

---

## 3. `TagNormalizer` (`scout_app/core/normalizer.py`)
**Role:** The Janitor. Standardizes raw AI output into a canonical dictionary.

### Key Logic & Atomic Functions

#### `get_unmapped_aspects()`
- **Logic:** Performs a `LEFT JOIN` between `review_tags` and `aspect_mapping`. Identifies "Dirty" aspects that haven't been assigned a standard category/name yet.

#### `run_live()`
- **Atomic Logic:** "RAG Shield Context"
    1.  **Shielding:** Fetches all existing `standard_aspect` terms and injects them into the prompt.
    2.  **Instruction:** Forces AI to map new raw terms to *existing* standard terms if possible, preventing dictionary bloat.
    3.  **Transformation:** Summarizes long sentences (e.g., "the fabric feels like silk") into Noun Phrases (e.g., "Texture Quality").

#### `save_mappings(mappings)`
- **Logic:** Performs `INSERT OR REPLACE` into `aspect_mapping`.
- **Side Effect (Smart Recalc):** Immediately identifies which ASINs are impacted by the new mappings and triggers `StatsEngine` to update their cached metrics.

## 4. `Prompts` (`scout_app/core/prompts.py`)
**Role:** The AI Persona Definition.

### Atomic Logic: "Strict Engineering"
- **Anti-Hallucination:** Explicitly forbids the AI from using internal knowledge to guess prices or competitors. "If the tool returns no data, say 'No Data'".
- **Tone Enforcement:** Bans adjectives ("soft", "amazing") in favor of raw technical data ("polyester", "4.5 stars").
- **Structure enforcement:** Mandates Markdown Tables for all analysis outputs.

#### `generate_listing_content(asin, tone)`
- **Role:** SEO Gen.
- **Logic:** Fetches Top 5 Strengths (Positive Tags) and Top 5 Pain Points (Negative Tags) to construct a "Problem-Solution" narrative for the listing.

### Dependency Graph
- **Upstream:** `scout_app/ui/tabs/strategy.py` (Streamlit Chat UI).
- **Downstream:** `DuckDB` (Read-Only queries), `Gemini API`.
