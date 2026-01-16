import duckdb
import os
import json
import re
import pandas as pd
from google import genai
from google.genai import types
from .config import Settings

# --- Config ---
MODEL_NAME = Settings.GEMINI_MODEL 

class DetectiveAgent:
    def __init__(self, api_key=None):
        # We don't cache DB_PATH here because it might swap
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or Settings.GEMINI_MINER_KEY
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ Detective Warning: No API Key found.")

        self.chat_session = None

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
                check = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'aspect_mapping'").fetchone()[0]
                if check == 0: return []
                
                res = conn.execute("SELECT DISTINCT standard_aspect FROM aspect_mapping WHERE standard_aspect IS NOT NULL").fetchall()
                return [r[0] for r in res]
        except Exception:
            return []

    # --- TOOLS DEFINITION ---
    
    def get_product_dna(self, asin: str) -> str:
        # 1. Base Metadata
        query_meta = """
            SELECT title, material, main_niche, target_audience, size_capacity, brand 
            FROM products 
            WHERE asin = ? OR parent_asin = ?
            LIMIT 1
        """
        # 2. Variation Stats
        query_vars = """
            SELECT 
                COUNT(DISTINCT child_asin) as total_variations,
                LIST(DISTINCT variation_text) FILTER (variation_text IS NOT NULL) as var_list
            FROM reviews 
            WHERE parent_asin = ?
        """
        try:
            df_meta = self._run_query(query_meta, [asin, asin])
            df_vars = self._run_query(query_vars, [asin])
            
            result = {}
            if not df_meta.empty:
                result.update(df_meta.iloc[0].to_dict())
            else:
                result["notice"] = f"No static metadata found for ASIN {asin}."

            if not df_vars.empty:
                row = df_vars.iloc[0]
                total = row['total_variations']
                var_raw_list = row['var_list'] if row['var_list'] is not None else []
                
                colors = set()
                sizes = set()
                for v in var_raw_list: 
                    parts = v.split(',')
                    for p in parts:
                        if "Color:" in p: colors.add(p.split(":")[-1].strip())
                        if "Size:" in p: sizes.add(p.split(":")[-1].strip())
                
                result["variation_stats"] = {
                    "total_count": int(total),
                    "detected_colors": list(colors)[:20],
                    "detected_sizes": list(sizes)[:10]
                }
            return json.dumps(result, default=str)
        except Exception as e:
            return f"Error fetching DNA: {e}"

    def search_review_evidence(self, asin: str, aspect: str = None, sentiment: str = None, keyword: str = None) -> str:
        clauses = ["rt.parent_asin = ?"]
        params = [asin]

        if sentiment:
            clauses.append("rt.sentiment = ?")
            params.append(sentiment)
        if aspect:
            clauses.append("am.standard_aspect ILIKE ?")
            params.append(f"%{aspect}%")
        if keyword:
            k_list = [k.strip() for k in keyword.split(',')]
            or_clauses = []
            for k in k_list:
                or_clauses.append("(rt.quote ILIKE ? OR r.variation_text ILIKE ?)")
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
            LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
            WHERE {where_stmt}
            ORDER BY r.review_date DESC
            LIMIT 30
        """
        try:
            res = self._run_query(query, params)
            if res.empty:
                return f"NOTICE: No evidence found for ASIN {asin}."
            return res.to_json(orient='records')
        except Exception as e:
            return f"Query Error: {e}"

    def find_better_alternatives(self, current_asin: str, aspect_criteria: str = "Quality") -> str:
        try:
            niche_query = "SELECT main_niche FROM products WHERE asin = ? OR parent_asin = ? LIMIT 1"
            niche_df = self._run_query(niche_query, [current_asin, current_asin])
            
            if niche_df.empty or not niche_df.iloc[0]['main_niche']:
                return "Cannot find alternatives: The current product has no defined Niche/Category."
            
            niche = niche_df.iloc[0]['main_niche']
            aspect_filter = ""
            if aspect_criteria and aspect_criteria != "Overall":
                aspect_filter = f"AND (am.category = '{aspect_criteria}' OR am.standard_aspect = '{aspect_criteria}')"
            
            query = f"""
                SELECT 
                    p.parent_asin,
                    p.title,
                    COUNT(*) as total_mentions,
                    ROUND(SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as positive_score
                FROM products p
                JOIN review_tags rt ON p.parent_asin = rt.parent_asin
                LEFT JOIN aspect_mapping am ON rt.aspect = am.raw_aspect
                WHERE p.main_niche = ?
                AND p.parent_asin != ?
                {aspect_filter}
                GROUP BY 1, 2
                HAVING count(*) > 10
                ORDER BY positive_score DESC
                LIMIT 3
            """
            res = self._run_query(query, [niche, current_asin])
            if res.empty:
                return f"No better alternatives found specifically for '{aspect_criteria}' in niche '{niche}'."
            return res.to_json(orient='records')
        except Exception as e:
            return f"Market Scout Error: {e}"

    def get_product_swot(self, asin: str) -> str:
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
            df = self._run_query(query, [asin])
            
            if df.empty:
                return f"No sentiment data found for ASIN {asin}."

            swot = {"strengths": [], "weaknesses": [], "controversial": [], "summary": {}}
            
            global_stats = self._run_query("SELECT AVG(rating_score) as avg_rating, COUNT(*) as total_reviews FROM reviews WHERE parent_asin = ?", [asin]).iloc[0]
            swot["summary"] = {
                "avg_rating": round(float(global_stats['avg_rating']), 2),
                "total_reviews": int(global_stats['total_reviews'])
            }

            for _, row in df.iterrows():
                item = {
                    "aspect": row['aspect'],
                    "mentions": int(row['mentions']),
                    "pos_ratio": float(row['pos_ratio'])
                }
                if row['pos_ratio'] >= 75:
                    swot["strengths"].append(item)
                elif row['pos_ratio'] <= 40:
                    q_query = f"SELECT quote FROM review_tags WHERE parent_asin=? AND (aspect=? OR aspect ILIKE ?) AND sentiment='Negative' LIMIT 1"
                    aspect_pattern = f"%{row['aspect']}%"
                    # Need specific query execution for fetchone, reusing _run_query logic minimally or just execute
                    # For simplicity, using df and iloc
                    sample_df = self._run_query(q_query, [asin, row['aspect'], aspect_pattern])
                    item["sample_complaint"] = sample_df.iloc[0]['quote'] if not sample_df.empty else None
                    swot["weaknesses"].append(item)
                elif 40 < row['pos_ratio'] < 75:
                    swot["controversial"].append(item)

            swot["strengths"] = swot["strengths"][:5]
            swot["weaknesses"] = swot["weaknesses"][:5]
            swot["controversial"] = swot["controversial"][:3]
            return json.dumps(swot, default=str)
        except Exception as e:
            return f"SWOT Error: {e}"

    def compare_head_to_head(self, asin_a: str, asin_b: str) -> str:
        query = f"""
            WITH stats AS (
                SELECT 
                    rt.parent_asin,
                    COALESCE(am.standard_aspect, rt.aspect) as aspect,
                    COUNT(*) as total,
                    ROUND(SUM(CASE WHEN rt.sentiment = 'Positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pos_pct
                FROM review_tags rt
                LEFT JOIN aspect_mapping am ON lower(trim(rt.aspect)) = lower(trim(am.raw_aspect))
                WHERE rt.parent_asin IN ('{asin_a}', '{asin_b}')
                GROUP BY 1, 2
                HAVING total >= 2
            )
            SELECT aspect,
                MAX(CASE WHEN parent_asin = '{asin_a}' THEN pos_pct END) as score_a,
                MAX(CASE WHEN parent_asin = '{asin_b}' THEN pos_pct END) as score_b,
                MAX(CASE WHEN parent_asin = '{asin_a}' THEN total END) as mentions_a,
                MAX(CASE WHEN parent_asin = '{asin_b}' THEN total END) as mentions_b
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
            return df.to_json(orient='records')
        except Exception as e:
            return f"Comparison Error: {e}"

    def analyze_customer_context(self, asin: str) -> str:
        targets = {
            "Kids/Teens": ["daughter", "son", "kid", "child", "teen", "girl", "boy", "granddaughter", "grandson"],
            "Adults/Self": ["master bedroom", "myself", "husband", "wife", "we"],
            "Guest": ["guest room", "visitor", "airbnb", "spare room"],
            "College": ["dorm", "college", "campus", "student"]
        }
        occasions = {
            "Gift": ["gift", "birthday", "christmas", "present", "xmas"],
            "Renovation": ["remodel", "new house", "moving", "makeover"],
            "Replacement": ["replace", "old comforter", "worn out"]
        }
        results = {"target_audience": {}, "usage_occasion": {}}
        
        try:
            # We can run these counts using fetchall via _run_query helper modification or loop
            # Using loop with dataframe count for simplicity and consistency
            for group, keywords in targets.items():
                kw_str = " OR ".join([f"text ILIKE '%{k}%'" for k in keywords])
                df = self._run_query(f"SELECT COUNT(*) as c FROM reviews WHERE parent_asin = ? AND ({kw_str})", [asin])
                count = df.iloc[0]['c'] if not df.empty else 0
                if count > 0: results["target_audience"][group] = int(count)

            for group, keywords in occasions.items():
                kw_str = " OR ".join([f"text ILIKE '%{k}%'" for k in keywords])
                df = self._run_query(f"SELECT COUNT(*) as c FROM reviews WHERE parent_asin = ? AND ({kw_str})", [asin])
                count = df.iloc[0]['c'] if not df.empty else 0
                if count > 0: results["usage_occasion"][group] = int(count)

            return json.dumps(results)
        except Exception as e:
            return f"Context Analysis Error: {e}"

    def answer(self, user_query: str, default_asin: str = None):
        if not self.client:
            return "Gemini API Key is missing."

        # Tools mapping
        tools_map = {
            "get_product_dna": self.get_product_dna,
            "search_review_evidence": self.search_review_evidence,
            "find_better_alternatives": self.find_better_alternatives,
            "get_product_swot": self.get_product_swot,
            "compare_head_to_head": self.compare_head_to_head,
            "analyze_customer_context": self.analyze_customer_context
        }
        
        # Tool declarations (Keeping schema same as before)
        tool_declarations = [types.Tool(function_declarations=[
            types.FunctionDeclaration(name="get_product_dna", description="Get technical specs and variation stats.", parameters=types.Schema(type="OBJECT", properties={"asin": types.Schema(type="STRING")}, required=["asin"])),
            types.FunctionDeclaration(name="get_product_swot", description="Get SWOT analysis.", parameters=types.Schema(type="OBJECT", properties={"asin": types.Schema(type="STRING")}, required=["asin"])),
            types.FunctionDeclaration(name="search_review_evidence", description="Search quotes.", parameters=types.Schema(type="OBJECT", properties={"asin": types.Schema(type="STRING"), "aspect": types.Schema(type="STRING"), "sentiment": types.Schema(type="STRING"), "keyword": types.Schema(type="STRING")}, required=["asin"])),
            types.FunctionDeclaration(name="find_better_alternatives", description="Find alternatives.", parameters=types.Schema(type="OBJECT", properties={"current_asin": types.Schema(type="STRING"), "aspect_criteria": types.Schema(type="STRING")}, required=["current_asin"])),
            types.FunctionDeclaration(name="compare_head_to_head", description="Compare two products.", parameters=types.Schema(type="OBJECT", properties={"asin_a": types.Schema(type="STRING"), "asin_b": types.Schema(type="STRING")}, required=["asin_a", "asin_b"])),
            types.FunctionDeclaration(name="analyze_customer_context", description="Analyze context.", parameters=types.Schema(type="OBJECT", properties={"asin": types.Schema(type="STRING")}, required=["asin"]))
        ])]

        # Init session
        if not self.chat_session:
            vocab = self._get_vocabulary()
            vocab_str = ", ".join(vocab)
            
            system_instructions = f"""
            You are 'The Detective', an elite Amazon Market Analyst.
            KNOWLEDGE BASE (Standard Aspects): [{vocab_str}]
            RULES: Default ASIN: {default_asin}.
            """
            
            self.chat_session = self.client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(tools=tool_declarations, system_instruction=system_instructions)
            )

        try:
            response = self.chat_session.send_message(user_query)
            max_turns = 10
            for _ in range(max_turns):
                if response.function_calls:
                    parts = []
                    for fc in response.function_calls:
                        fname = fc.name
                        fargs = fc.args
                        if fname in tools_map:
                            result = tools_map[fname](**fargs)
                        else:
                            result = "Error: Tool not found"
                        parts.append(types.Part(function_response=types.FunctionResponse(name=fname, response={"result": result})))
                    response = self.chat_session.send_message(parts)
                else:
                    return response.text
            return "Agent got stuck in a loop."
        except Exception as e:
            self.chat_session = None
            return f"Detective Error: {e}"

if __name__ == "__main__":
    agent = DetectiveAgent()