import duckdb
import os
import json
import re
import pandas as pd
from google import genai
from google.genai import types
from .config import Settings
from .logger import log_event
from .prompts import DETECTIVE_SYS_PROMPT, get_user_context_prompt

# --- Config ---
MODEL_NAME = Settings.GEMINI_MODEL


class DetectiveAgent:
    def __init__(self, api_key=None):
        # ... rest of init ...
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or Settings.GEMINI_MINER_KEY

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ Detective Warning: No API Key found.")

        self.chat_session = None
        self.system_prompt = DETECTIVE_SYS_PROMPT

    # --- DB Helper (Blue-Green Aware) ---
    def _get_db_path(self):
        return str(Settings.get_active_db_path())

    def _run_query(self, query, params=None, fetch_df=True):
        """Execute query safely against ACTIVE DB."""
        try:
            db_path = self._get_db_path()
            with duckdb.connect(db_path, read_only=True) as conn:
                if fetch_df:
                    return conn.execute(query, params).df()
                else:
                    return conn.execute(query, params).fetchall()
        except Exception as e:
            print(f"DB Error in Detective: {e}")
            return pd.DataFrame() if fetch_df else []

    def _get_vocabulary(self):
        """Get vocab for system prompt"""
        try:
            db_path = self._get_db_path()
            with duckdb.connect(db_path, read_only=True) as conn:
                check = conn.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_name = 'aspect_mapping'"
                ).fetchone()[0]
                if check == 0:
                    return []

                res = conn.execute(
                    "SELECT DISTINCT standard_aspect FROM aspect_mapping WHERE standard_aspect IS NOT NULL"
                ).fetchall()
                return [r[0] for r in res]
        except Exception:
            return []

    def _normalize_asin(self, asin: str) -> str:
        """Always returns the Parent ASIN for a given Child or Parent."""
        if not asin:
            return ""
        query = "SELECT parent_asin FROM products WHERE asin = ? OR parent_asin = ? LIMIT 1"
        res = self._run_query(query, [asin, asin])
        if not res.empty:
            return res.iloc[0]["parent_asin"]
        return asin

    # --- TOOLS DEFINITION ---

    def get_product_dna(self, asin: str) -> str:
        """Fetch base metadata and official market stats for a product."""
        parent_asin = self._normalize_asin(asin)

        try:
            # 1. Fetch metadata from product_parents (Source of Truth for categorization)
            query_parent = """
                SELECT category, niche, title, brand, image_url 
                FROM product_parents WHERE parent_asin = ?
            """
            parent_df = self._run_query(query_parent, [parent_asin])

            # 2. Fetch technical specs from products
            query_tech = """
                SELECT material, target_audience, size_capacity, product_line, variation_count, 
                       real_average_rating, real_total_ratings, rating_breakdown
                FROM products WHERE asin = ?
            """
            tech_df = self._run_query(query_tech, [parent_asin])

            # 3. Fetch pre-calculated metrics
            query_stats = "SELECT metrics_json FROM product_stats WHERE asin = ?"
            stats_res = self._run_query(query_stats, [parent_asin], fetch_df=False)

            result = {
                "asin": asin,
                "parent_asin": parent_asin,
                "metadata": {},
                "market_stats": {},
                "top_aspects": {"strengths": [], "weaknesses": []},
            }

            if not parent_df.empty:
                result["metadata"].update(parent_df.iloc[0].to_dict())

            if not tech_df.empty:
                tech_data = tech_df.iloc[0].to_dict()
                # Clean up technical data
                result["metadata"].update(
                    {
                        k: v
                        for k, v in tech_data.items()
                        if k not in ["real_average_rating", "real_total_ratings", "rating_breakdown"]
                    }
                )
                result["market_stats"] = {
                    "avg_rating": tech_data.get("real_average_rating"),
                    "total_reviews": tech_data.get("real_total_ratings"),
                }

            if stats_res:
                stats = json.loads(stats_res[0][0])
                sw = stats.get("sentiment_weighted", [])
                result["top_aspects"]["strengths"] = [a["aspect"] for a in sw if a.get("net_impact", 0) > 0][:5]
                result["top_aspects"]["weaknesses"] = [a["aspect"] for a in sw if a.get("net_impact", 0) < 0][-5:]

                # --- NEW: Preference for Pre-calculated stats over raw product metadata ---
                kpis = stats.get("kpis", {})
                if kpis:
                    result["market_stats"] = {
                        "avg_rating": kpis.get("avg_rating"),
                        "total_reviews": kpis.get("total_reviews"),
                    }

            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e), "asin": asin})

    def search_review_evidence(self, asin: str, aspect: str = None, sentiment: str = None, keyword: str = None) -> str:
        parent_asin = self._normalize_asin(asin)
        clauses = ["rt.parent_asin = ?"]
        params = [parent_asin]

        # Standardized Aspect Filter (Flexible Search)
        if aspect:
            # We match against standard_aspect OR raw_aspect (case-insensitive)
            clauses.append(
                "(lower(trim(am.standard_aspect)) = lower(trim(?)) OR lower(trim(rt.aspect)) = lower(trim(?)))"
            )
            params.append(aspect)
            params.append(aspect)

        if sentiment:
            clauses.append("rt.sentiment = ?")
            params.append(sentiment)

        if keyword:
            k_list = [k.strip() for k in keyword.split(",")]
            or_clauses = []
            for k in k_list:
                or_clauses.append("(rt.quote ILIKE ? OR r.text ILIKE ?)")
                params.append(f"%{k}%")
                params.append(f"%{k}%")
            clauses.append("(" + " OR ".join(or_clauses) + ")")

        where_stmt = " AND ".join(clauses)

        query = f"""
            SELECT 
                COALESCE(am.standard_aspect, rt.aspect) as aspect,
                rt.sentiment, 
                rt.quote,
                r.variation_text,
                CAST(r.review_date AS VARCHAR) as review_date
            FROM review_tags rt
            JOIN reviews r ON rt.review_id = r.review_id
            LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
            WHERE {where_stmt}
            ORDER BY r.review_date DESC
            LIMIT 30
        """
        try:
            res = self._run_query(query, params)
            if res.empty:
                return f"NOTICE: No specific evidence found for ASIN {asin} with criteria: aspect={aspect}, sentiment={sentiment}, keyword={keyword}."
            return res.to_json(orient="records")
        except Exception as e:
            return f"Query Error: {e}"

    def find_better_alternatives(self, current_asin: str, aspect_criteria: str = "Quality") -> str:
        parent_asin = self._normalize_asin(current_asin)
        try:
            niche_query = """
                SELECT 
                    pp.niche,
                    pp.category
                FROM product_parents pp 
                WHERE pp.parent_asin = ?
                LIMIT 1
            """
            niche_df = self._run_query(niche_query, [parent_asin])

            if niche_df.empty or not niche_df.iloc[0]["category"]:
                return "Cannot find alternatives: The current product has no defined Category."

            niche = niche_df.iloc[0]["niche"]
            category = niche_df.iloc[0]["category"]

            aspect_filter = ""
            if aspect_criteria and aspect_criteria != "Overall":
                aspect_filter = f"AND (am.category = '{aspect_criteria}' OR am.standard_aspect = '{aspect_criteria}')"

            # Mandatory Category Match (BỨC TƯỜNG THÉP)
            where_clauses = ["pp.category = ?"]
            params = [category]

            # Optional Niche matching (Priority within category)
            niche_filter = ""
            if niche and niche not in ["None", "Non-defined", "null"]:
                niche_filter = f"OR pp.niche ILIKE '%{niche}%'"

            query = f"""
                SELECT 
                    p.parent_asin,
                    p.title,
                    COUNT(*) as total_mentions,
                    ROUND(SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as positive_score
                FROM products p
                JOIN product_parents pp ON p.parent_asin = pp.parent_asin
                JOIN review_tags rt ON p.parent_asin = rt.parent_asin
                LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                WHERE pp.category = ?
                AND p.parent_asin != ?
                {aspect_filter}
                GROUP BY 1, 2
                HAVING count(*) > 10
                ORDER BY 
                    (CASE WHEN pp.niche ILIKE ? THEN 10 ELSE 0 END) DESC,
                    positive_score DESC
                LIMIT 3
            """
            # Using primary niche for ILIKE matching
            primary_niche = f"%{niche.split(',')[0].strip()}%" if niche else "%"
            res = self._run_query(query, [category, current_asin, primary_niche])
            if res.empty:
                return f"No better alternatives found specifically for '{aspect_criteria}' in {category} arena."
            return res.to_json(orient="records")
        except Exception as e:
            return f"Market Scout Error: {e}"

    def get_product_swot(self, asin: str) -> str:
        parent_asin = self._normalize_asin(asin)
        try:
            query = """
                SELECT 
                    COALESCE(am.standard_aspect, rt.aspect) as aspect,
                    COUNT(*) as mentions,
                    SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) as pos_count,
                    SUM(CASE WHEN rt.sentiment = 'Negative' THEN 1 ELSE 0 END) as neg_count,
                    ROUND(SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pos_ratio
                FROM review_tags rt
                LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
                WHERE rt.parent_asin = ?
                GROUP BY 1
                HAVING mentions >= 3
                ORDER BY mentions DESC
            """
            df = self._run_query(query, [parent_asin])

            if df.empty:
                return f"No sentiment data found for ASIN {parent_asin}."

            swot = {"strengths": [], "weaknesses": [], "controversial": [], "summary": {}}

            # --- FIX: Use REAL METADATA from product_stats if available ---
            stats_res = self._run_query(
                "SELECT metrics_json FROM product_stats WHERE asin = ?", [parent_asin], fetch_df=False
            )

            if stats_res:
                stats = json.loads(stats_res[0][0])
                swot["summary"] = {
                    "avg_rating": round(stats.get("kpis", {}).get("avg_rating", 0), 2),
                    "total_reviews": int(stats.get("kpis", {}).get("total_reviews", 0)),
                }
            else:
                # Fallback to products table
                meta_stats = self._run_query(
                    """
                    SELECT real_average_rating, real_total_ratings 
                    FROM products WHERE asin = ? 
                """,
                    [parent_asin],
                ).iloc[0]
                swot["summary"] = {
                    "avg_rating": round(float(meta_stats["real_average_rating"] or 0), 2),
                    "total_reviews": int(meta_stats["real_total_ratings"] or 0),
                }

            for _, row in df.iterrows():
                item = {"aspect": row["aspect"], "mentions": int(row["mentions"]), "pos_ratio": float(row["pos_ratio"])}
                if row["pos_ratio"] >= 75:
                    swot["strengths"].append(item)
                elif row["pos_ratio"] <= 40:
                    q_query = f"SELECT quote FROM review_tags WHERE parent_asin=? AND (aspect=? OR aspect ILIKE ?) AND sentiment='Negative' LIMIT 1"
                    aspect_pattern = f"%{row['aspect']}%"
                    # Need specific query execution for fetchone, reusing _run_query logic minimally or just execute
                    # For simplicity, using df and iloc
                    sample_df = self._run_query(q_query, [asin, row["aspect"], aspect_pattern])
                    item["sample_complaint"] = sample_df.iloc[0]["quote"] if not sample_df.empty else None
                    swot["weaknesses"].append(item)
                elif 40 < row["pos_ratio"] < 75:
                    swot["controversial"].append(item)

            swot["strengths"] = swot["strengths"][:5]
            swot["weaknesses"] = swot["weaknesses"][:5]
            swot["controversial"] = swot["controversial"][:3]
            return json.dumps(swot, default=str)
        except Exception as e:
            return f"SWOT Error: {e}"

    def compare_head_to_head(self, asin_a: str, asin_b: str) -> str:
        parent_a = self._normalize_asin(asin_a)
        parent_b = self._normalize_asin(asin_b)

        query = f"""
            WITH stats AS (
                SELECT 
                    rt.parent_asin,
                    COALESCE(am.standard_aspect, rt.aspect) as aspect,
                    COUNT(*) as total,
                    ROUND(SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pos_pct
                FROM review_tags rt
                LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
                WHERE rt.parent_asin IN ('{parent_a}', '{parent_b}')
                GROUP BY 1, 2
                HAVING total >= 2
            )
            SELECT aspect,
                MAX(CASE WHEN parent_asin = '{parent_a}' THEN pos_pct END) as score_a,
                MAX(CASE WHEN parent_asin = '{parent_b}' THEN pos_pct END) as score_b,
                MAX(CASE WHEN parent_asin = '{parent_a}' THEN total END) as mentions_a,
                MAX(CASE WHEN parent_asin = '{parent_b}' THEN total END) as mentions_b
            FROM stats
            GROUP BY 1
            HAVING score_a IS NOT NULL AND score_b IS NOT NULL
            ORDER BY (mentions_a + mentions_b) DESC
            LIMIT 10
        """
        try:
            df = self._run_query(query)
            if df.empty:
                return f"Not enough shared data points to compare {asin_a} vs {asin_b}."
            return df.to_json(orient="records")
        except Exception as e:
            return f"Comparison Error: {e}"

    def analyze_customer_context(self, asin: str) -> str:
        parent_asin = self._normalize_asin(asin)
        targets = {
            "End-User: Kids/Teens": [
                "daughter",
                "son",
                "kid",
                "child",
                "teen",
                "girl",
                "boy",
                "granddaughter",
                "grandson",
            ],
            "End-User: Adults/Self": ["master bedroom", "myself", "husband", "wife", "we"],
            "End-User: Guest": ["guest room", "visitor", "airbnb", "spare room"],
            "End-User: College Student": ["dorm", "college", "campus", "student"],
        }
        occasions = {
            "Gift": ["gift", "birthday", "christmas", "present", "xmas"],
            "Renovation": ["remodel", "new house", "moving", "makeover"],
            "Replacement": ["replace", "old comforter", "worn out"],
        }
        results = {"target_audience": {}, "usage_occasion": {}}

        try:
            for group, keywords in targets.items():
                kw_str = " OR ".join([f"text ILIKE '%{k}%'" for k in keywords])
                df = self._run_query(
                    f"SELECT COUNT(*) as c FROM reviews WHERE parent_asin = ? AND ({kw_str})", [parent_asin]
                )
                count = df.iloc[0]["c"] if not df.empty else 0
                if count > 0:
                    results["target_audience"][group] = int(count)

            for group, keywords in occasions.items():
                kw_str = " OR ".join([f"text ILIKE '%{k}%'" for k in keywords])
                df = self._run_query(
                    f"SELECT COUNT(*) as c FROM reviews WHERE parent_asin = ? AND ({kw_str})", [parent_asin]
                )
                count = df.iloc[0]["c"] if not df.empty else 0
                if count > 0:
                    results["usage_occasion"][group] = int(count)

            return json.dumps(results)
        except Exception as e:
            return f"Context Analysis Error: {e}"

    def generate_listing_content(self, asin: str, tone: str = "Persuasive") -> str:
        """Generates SEO Title and 5 Bullet Points based on Pain Points & Strengths."""
        parent_asin = self._normalize_asin(asin)
        try:
            # 1. Get DNA
            dna_query = "SELECT title, material, main_niche, target_audience FROM products WHERE asin = ? LIMIT 1"
            dna_df = self._run_query(dna_query, [parent_asin])
            dna_str = dna_df.iloc[0].to_json() if not dna_df.empty else "N/A"

            # 2. Get Top Pain Points (to solve)
            pain_query = """
                SELECT COALESCE(am.standard_aspect, rt.aspect) as aspect, COUNT(*) as cnt 
                FROM review_tags rt 
                LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect)) 
                WHERE rt.parent_asin = ? AND rt.sentiment = 'Negative' 
                GROUP BY 1 ORDER BY 2 DESC LIMIT 5
            """
            pain_df = self._run_query(pain_query, [parent_asin])
            pain_str = ", ".join(pain_df["aspect"].tolist()) if not pain_df.empty else "None"

            # 3. Get Top Strengths (to highlight)
            pos_query = """
                SELECT COALESCE(am.standard_aspect, rt.aspect) as aspect, COUNT(*) as cnt 
                FROM review_tags rt 
                LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect)) 
                WHERE rt.parent_asin = ? AND rt.sentiment = 'Positive' 
                GROUP BY 1 ORDER BY 2 DESC LIMIT 5
            """
            pos_df = self._run_query(pos_query, [parent_asin])
            pos_str = ", ".join(pos_df["aspect"].tolist()) if not pos_df.empty else "None"

            return json.dumps(
                {
                    "action": "generate_listing",
                    "dna": dna_str,
                    "solve_pain_points": pain_str,
                    "highlight_strengths": pos_str,
                    "tone": tone,
                }
            )
        except Exception as e:
            return f"Error generating content data: {e}"

    def analyze_competitors(self, asin: str) -> str:
        """Finds real competitors in DB using Smart Fallback (Strict Category Arena) and compares them."""
        parent_asin = self._normalize_asin(asin)
        try:
            # 1. Get DNA of Current Product (Preferring product_parents for Category/Niche)
            dna_query = """
                SELECT 
                    pp.parent_asin, 
                    pp.category, 
                    pp.niche,
                    p.product_line, p.material, p.target_audience 
                FROM product_parents pp
                LEFT JOIN products p ON pp.parent_asin = p.parent_asin
                WHERE pp.parent_asin = ?
                LIMIT 1
            """
            dna_df = self._run_query(dna_query, [parent_asin])

            if dna_df.empty:
                return "Product DNA not found. Cannot identify competitors."

            dna = dna_df.iloc[0]
            current_parent = dna["parent_asin"]
            category = dna["category"]
            niche = dna["niche"]
            line = dna["product_line"]
            mat = dna["material"]

            # 2. Build Query with Strict Category Match
            params = [current_parent, category]

            # Use primary niche for ILIKE matching
            primary_niche = niche.split(",")[0].strip() if niche else ""

            comp_query = f"""
                SELECT 
                    pp.parent_asin, 
                    COALESCE(pp.title, ANY_VALUE(p.title)) as title, 
                    COALESCE(pp.brand, ANY_VALUE(p.brand)) as brand, 
                    MAX(p.real_average_rating) as rating, 
                    MAX(p.real_total_ratings) as reviews
                FROM products p
                JOIN product_parents pp ON p.parent_asin = pp.parent_asin
                WHERE pp.parent_asin != ? 
                AND pp.category = ? -- BỨC TƯỜNG THÉP
                GROUP BY pp.parent_asin, pp.title, pp.brand
                HAVING reviews > 5
                ORDER BY 
                    (CASE WHEN pp.niche ILIKE '%{primary_niche}%' THEN 10 ELSE 0 END) DESC,
                    rating DESC, reviews DESC
                LIMIT 3
            """

            comps_df = self._run_query(comp_query, params)

            if comps_df.empty:
                return f"No direct competitors found in DB for {category} arena (Checked Niche: {niche})."

            # 3. Get Current ASIN Weaknesses
            my_weak_query = """
                SELECT COALESCE(am.standard_aspect, rt.aspect) as aspect
                FROM review_tags rt LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                WHERE rt.parent_asin = ? AND rt.sentiment = 'Negative'
                GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 3
            """
            my_weak_df = self._run_query(my_weak_query, [current_parent])
            my_weaknesses = my_weak_df["aspect"].tolist() if not my_weak_df.empty else []

            # 4. Analyze Each Competitor
            results = []
            for _, row in comps_df.iterrows():
                comp_asin = row["parent_asin"]
                strengths = []

                if my_weaknesses:
                    for weak_point in my_weaknesses:
                        s_query = """
                            SELECT COUNT(*) FROM review_tags rt 
                            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                            WHERE rt.parent_asin = ? 
                            AND (am.standard_aspect = ? OR rt.aspect = ?) 
                            AND rt.sentiment = 'Positive'
                        """
                        try:
                            res = self._run_query(s_query, [comp_asin, weak_point, weak_point], fetch_df=False)
                            count = res[0][0] if res else 0
                        except:
                            count = 0

                        if count > 0:
                            strengths.append(f"Better at '{weak_point}' ({count} positive mentions)")

                results.append(
                    {
                        "competitor_brand": row["brand"],
                        "competitor_title": row["title"][:50] + "...",
                        "rating": round(row["rating"], 2),
                        "review_count": row["reviews"],
                        "advantage_over_us": strengths if strengths else "No clear advantage in our weak areas.",
                    }
                )

            return json.dumps(
                {
                    "analysis_logic": f"Compared against competitors in Niche '{niche}' or Line '{line}'.",
                    "our_weaknesses": my_weaknesses,
                    "competitors": results,
                }
            )

        except Exception as e:
            return f"Competitor Analysis Error: {e}"

    def answer(self, user_query: str, default_asin: str = None, user_id: str = "guest"):
        if not self.client:
            return "Gemini API Key is missing."

        # Tools mapping
        tools_map = {
            "get_product_dna": self.get_product_dna,
            "search_review_evidence": self.search_review_evidence,
            "find_better_alternatives": self.find_better_alternatives,
            "get_product_swot": self.get_product_swot,
            "compare_head_to_head": self.compare_head_to_head,
            "analyze_customer_context": self.analyze_customer_context,
            "generate_listing_content": self.generate_listing_content,
            "analyze_competitors": self.analyze_competitors,
        }

        # Tool declarations
        tool_declarations = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="get_product_dna",
                        description="Get technical specs and variation stats.",
                        parameters=types.Schema(
                            type="OBJECT", properties={"asin": types.Schema(type="STRING")}, required=["asin"]
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="get_product_swot",
                        description="Get SWOT analysis.",
                        parameters=types.Schema(
                            type="OBJECT", properties={"asin": types.Schema(type="STRING")}, required=["asin"]
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="search_review_evidence",
                        description="Search quotes.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "asin": types.Schema(type="STRING"),
                                "aspect": types.Schema(type="STRING"),
                                "sentiment": types.Schema(type="STRING"),
                                "keyword": types.Schema(type="STRING"),
                            },
                            required=["asin"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="find_better_alternatives",
                        description="Find alternatives.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "current_asin": types.Schema(type="STRING"),
                                "aspect_criteria": types.Schema(type="STRING"),
                            },
                            required=["current_asin"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="compare_head_to_head",
                        description="Compare two products.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={"asin_a": types.Schema(type="STRING"), "asin_b": types.Schema(type="STRING")},
                            required=["asin_a", "asin_b"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="analyze_customer_context",
                        description="Analyze context.",
                        parameters=types.Schema(
                            type="OBJECT", properties={"asin": types.Schema(type="STRING")}, required=["asin"]
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="generate_listing_content",
                        description="Generate Amazon Title and Bullet Points.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={"asin": types.Schema(type="STRING"), "tone": types.Schema(type="STRING")},
                            required=["asin"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="analyze_competitors",
                        description="Find real competitors in DB and compare strengths/weaknesses.",
                        parameters=types.Schema(
                            type="OBJECT", properties={"asin": types.Schema(type="STRING")}, required=["asin"]
                        ),
                    ),
                ]
            )
        ]

        # Init session
        if not self.chat_session:
            vocab = self._get_vocabulary()
            vocab_str = ", ".join(vocab)

            # Build Full System Instruction
            system_instructions = f"""
            {self.system_prompt}
            
            ### KNOWLEDGE BASE (Standard Aspects):
            [{vocab_str}]
            
            ### SESSION CONTEXT:
            - Default ASIN: {default_asin}.
            
            ### ADDITIONAL CRITICAL RULES:
            1. **ZERO TRUST POLICY:** Do NOT use your internal training data to guess Competitors, Prices, or specific Review Quotes.
            2. **COMPETITORS:** When asked about competitors or comparisons, you **MUST** use the `analyze_competitors` tool. 
               - If the tool returns specific brands, ONLY discuss those.
               - DO NOT mention general brands like Disney, Target, or Walmart unless the tool explicitly lists them.
            3. **EVIDENCE:** Always back up your claims with data provided by the tools (counts, percentages, quotes).
            4. **NO LOOPING:** If a tool returns "No evidence found" or similar empty results, DO NOT call it again with the same parameters. Admit you cannot find the info and provide a best-effort answer or suggestions.
            """

            self.chat_session = self.client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(tools=tool_declarations, system_instruction=system_instructions),
            )

        final_response_text = ""
        previous_tool_calls = []  # Track tool calls to prevent loops

        try:
            response = self.chat_session.send_message(user_query)
            max_turns = 10
            for _ in range(max_turns):
                if response.function_calls:
                    parts = []
                    current_calls = []

                    for fc in response.function_calls:
                        fname = fc.name
                        fargs = dict(fc.args)  # Convert to dict

                        # --- ROBUSTNESS: Auto-inject Default ASIN if missing ---
                        if default_asin:
                            if "asin" not in fargs and "asin" in tools_map[fname].__code__.co_varnames:
                                fargs["asin"] = default_asin
                            if "current_asin" not in fargs and "current_asin" in tools_map[fname].__code__.co_varnames:
                                fargs["current_asin"] = default_asin
                            if "asin_a" not in fargs and "asin_a" in tools_map[fname].__code__.co_varnames:
                                fargs["asin_a"] = default_asin

                        # --- LOOP DETECTION ---
                        call_signature = f"{fname}:{json.dumps(fargs, sort_keys=True)}"
                        if call_signature in previous_tool_calls:
                            result = "SYSTEM ERROR: You already called this tool with these exact arguments. DO NOT DO IT AGAIN. Stop and answer with what you have."
                        else:
                            previous_tool_calls.append(call_signature)
                            if fname in tools_map:
                                try:
                                    result = tools_map[fname](**fargs)
                                except Exception as tool_err:
                                    result = f"Tool Execution Error: {tool_err}"
                            else:
                                result = "Error: Tool not found"

                        parts.append(
                            types.Part(
                                function_response=types.FunctionResponse(name=fname, response={"result": result})
                            )
                        )

                    response = self.chat_session.send_message(parts)
                else:
                    final_response_text = response.text
                    break

            if not final_response_text:
                final_response_text = "Agent stopped to prevent infinite loop. (Max turns reached)"

        except Exception as e:
            self.chat_session = None
            final_response_text = f"Detective Error: {e}"

        # --- LOGGING ---
        log_event(
            "chat_history",
            {"user_id": user_id, "asin": default_asin, "query": user_query, "response": final_response_text},
        )

        return final_response_text


if __name__ == "__main__":
    agent = DetectiveAgent()
