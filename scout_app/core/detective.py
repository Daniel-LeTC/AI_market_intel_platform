import duckdb
import os
import json
from google import genai
from google.genai import types
from .config import Settings

# --- Config ---
# Use Settings for centralized config
DB_PATH = str(Settings.DB_PATH)
MODEL_NAME = Settings.GEMINI_MODEL # This now points to Gemini 3 Flash Preview

class DetectiveAgent:
    def __init__(self, api_key=None):
        self.db_path = DB_PATH
        # Priority: Passed Key > Env GEMINI_API_KEY (Project Key) > Miner Key (Fallback)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or Settings.GEMINI_MINER_KEY
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️ Detective Warning: No API Key found.")

        self.chat_session = None # Persist chat session

    def _get_conn(self):
        """Lazy connection to avoid locking issues"""
        return duckdb.connect(self.db_path, read_only=True)

    def _get_vocabulary(self):
        """Lay danh sach cac tag da duoc chuan hoa de lam Knowledge Base cho AI"""
        conn = self._get_conn()
        try:
            # Check if table exists first to avoid error
            check = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'aspect_mapping'").fetchone()[0]
            if check == 0: return []
            
            res = conn.execute("SELECT DISTINCT standard_aspect FROM aspect_mapping WHERE standard_aspect IS NOT NULL").fetchall()
            return [r[0] for r in res]
        except: return []
        finally: conn.close()

    # --- TOOLS DEFINITION ---
    
    def get_product_dna(self, asin: str) -> str:
        """
        Fetch technical specs, metadata, AND variation stats for a specific ASIN.
        Use this to understand what the product is (material, brand, target) and its variations.
        """
        conn = self._get_conn()
        
        # 1. Base Metadata
        query_meta = f"""
            SELECT title, material, main_niche, target_audience, size_capacity, brand 
            FROM products 
            WHERE asin = '{asin}' OR parent_asin = '{asin}'
            LIMIT 1
        """
        
        # 2. Variation Stats (From Reviews)
        query_vars = f"""
            SELECT 
                COUNT(DISTINCT child_asin) as total_variations,
                LIST(DISTINCT variation_text) FILTER (variation_text IS NOT NULL) as var_list
            FROM reviews 
            WHERE parent_asin = '{asin}'
        """
        
        try:
            # Execute both
            df_meta = conn.execute(query_meta).df()
            df_vars = conn.execute(query_vars).df()
            
            result = {}
            
            if not df_meta.empty:
                result.update(df_meta.iloc[0].to_dict())
            else:
                result["notice"] = f"No static metadata found for ASIN {asin}."

            if not df_vars.empty:
                row = df_vars.iloc[0]
                total = row['total_variations']
                var_raw_list = row['var_list'] if row['var_list'] is not None else []
                
                # Simple extraction of Colors/Sizes from variation text if possible
                # Expected text format: "Color: Black, Size: Queen"
                colors = set()
                sizes = set()
                
                for v in var_raw_list: # Check top 50 to avoid huge loops
                    parts = v.split(',')
                    for p in parts:
                        if "Color:" in p: colors.add(p.split(":")[-1].strip())
                        if "Size:" in p: sizes.add(p.split(":")[-1].strip())
                
                result["variation_stats"] = {
                    "total_count": int(total),
                    "detected_colors": list(colors)[:20], # Limit to avoid token overflow
                    "detected_sizes": list(sizes)[:10]
                }
            
            return json.dumps(result, default=str)

        except Exception as e:
            return f"Error fetching DNA: {e}"
        finally:
            conn.close()

    def search_review_evidence(self, asin: str, aspect: str = None, sentiment: str = None, keyword: str = None) -> str:
        """
        Search for specific review quotes.
        - keyword: Can be a single word or multiple synonyms separated by comma (e.g. 'torn, tear, hole')
        """
        conn = self._get_conn()
        clauses = ["rt.parent_asin = ?"]
        params = [asin]

        if sentiment:
            clauses.append("rt.sentiment = ?")
            params.append(sentiment)
        
        if aspect:
            clauses.append("am.standard_aspect ILIKE ?")
            params.append(f"%{aspect}%")
            
        if keyword:
            # Split keywords and create OR clause
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
            res = conn.execute(query, params).df()
            if res.empty:
                return f"NOTICE: No evidence found for ASIN {asin} (Aspect: {aspect}, Sentiment: {sentiment}, Keyword: {keyword})."
            return res.to_json(orient='records')
        except Exception as e:
            return f"Database Query Error: {e}"
        finally:
            conn.close()

    def find_better_alternatives(self, current_asin: str, aspect_criteria: str = "Quality") -> str:
        """
        Scout the market database to find BETTER products in the same niche.
        It ranks products based on Positive Sentiment Rate for the requested aspect (default: Quality).
        """
        conn = self._get_conn()
        try:
            # 1. Identify Niche
            niche_query = f"SELECT main_niche FROM products WHERE asin = '{current_asin}' OR parent_asin = '{current_asin}' LIMIT 1"
            niche_df = conn.execute(niche_query).df()
            
            if niche_df.empty or not niche_df.iloc[0]['main_niche']:
                return "Cannot find alternatives: The current product has no defined Niche/Category in DB."
            
            niche = niche_df.iloc[0]['main_niche']

            # 2. Rank Competitors in that Niche
            # Formula: Score = (Positive Tags / Total Tags) for that Aspect
            # We map raw aspects to check 'Quality', 'Material' etc.
            
            aspect_filter = ""
            if aspect_criteria and aspect_criteria != "Overall":
                # Ensure we are filtering by mapped category or standard aspect
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
                HAVING count(*) > 10  -- Min thresholds to avoid junk
                ORDER BY positive_score DESC
                LIMIT 3
            """
            
            res = conn.execute(query, [niche, current_asin]).df()
            
            if res.empty:
                return f"No better alternatives found specifically for '{aspect_criteria}' in niche '{niche}'. Try searching for 'Overall'."
            
            return res.to_json(orient='records')

        except Exception as e:
            return f"Market Scout Error: {e}"
        finally:
            conn.close()

    def get_product_swot(self, asin: str) -> str:
        """
        High-level SWOT analysis of a product. 
        Returns Strengths, Weaknesses, and Controversial aspects based on aggregated sentiment.
        Use this for general questions like 'How is this product?' or 'Pros and cons'.
        """
        conn = self._get_conn()
        try:
            # 1. Aggregated Aspect Stats
            query = f"""
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
            df = conn.execute(query, [asin]).df()
            
            if df.empty:
                return f"No sentiment data found to perform SWOT for ASIN {asin}."

            swot = {
                "strengths": [],
                "weaknesses": [],
                "controversial": [],
                "summary": {}
            }

            # 2. Global Stats
            global_stats = conn.execute(f"SELECT AVG(rating_score) as avg_rating, COUNT(*) as total_reviews FROM reviews WHERE parent_asin = '{asin}'").df().iloc[0]
            swot["summary"] = {
                "avg_rating": round(float(global_stats['avg_rating']), 2),
                "total_reviews": int(global_stats['total_reviews'])
            }

            # 3. Categorization Logic
            for _, row in df.iterrows():
                item = {
                    "aspect": row['aspect'],
                    "mentions": int(row['mentions']),
                    "pos_ratio": float(row['pos_ratio'])
                }
                
                if row['pos_ratio'] >= 75:
                    swot["strengths"].append(item)
                elif row['pos_ratio'] <= 40:
                    # Get one sample negative quote for weakness
                    q_query = f"SELECT quote FROM review_tags WHERE parent_asin='{asin}' AND (aspect='{row['aspect']}' OR aspect ILIKE '%{row['aspect']}%') AND sentiment='Negative' LIMIT 1"
                    sample_quote = conn.execute(q_query).fetchone()
                    item["sample_complaint"] = sample_quote[0] if sample_quote else None
                    swot["weaknesses"].append(item)
                elif 40 < row['pos_ratio'] < 75:
                    swot["controversial"].append(item)

            # Limit results for conciseness
            swot["strengths"] = swot["strengths"][:5]
            swot["weaknesses"] = swot["weaknesses"][:5]
            swot["controversial"] = swot["controversial"][:3]

            return json.dumps(swot, default=str)

        except Exception as e:
            return f"SWOT Error: {e}"
        finally:
            conn.close()

    def compare_head_to_head(self, asin_a: str, asin_b: str) -> str:
        """
        Compare two products directly on key aspects (Quality, Price, Design, etc.).
        Returns a side-by-side sentiment score table.
        """
        conn = self._get_conn()
        try:
            # Get common aspects mentioned in both products
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
            df = conn.execute(query).df()
            if df.empty:
                return f"Not enough shared data points to compare {asin_a} vs {asin_b}."
            
            return df.to_json(orient='records')
        except Exception as e:
            return f"Comparison Error: {e}"
        finally:
            conn.close()

    def analyze_customer_context(self, asin: str) -> str:
        """
        Analyze WHO is buying (Persona) and WHY (Intent/Occasion).
        Scans reviews for keywords like 'gift', 'daughter', 'guest room', 'christmas'.
        """
        conn = self._get_conn()
        try:
            # 1. Target Audience Analysis
            targets = {
                "Kids/Teens": ["daughter", "son", "kid", "child", "teen", "girl", "boy", "granddaughter", "grandson"],
                "Adults/Self": ["master bedroom", "myself", "husband", "wife", "we"],
                "Guest": ["guest room", "visitor", "airbnb", "spare room"],
                "College": ["dorm", "college", "campus", "student"]
            }
            
            # 2. Occasion Analysis
            occasions = {
                "Gift": ["gift", "birthday", "christmas", "present", "xmas"],
                "Renovation": ["remodel", "new house", "moving", "makeover"],
                "Replacement": ["replace", "old comforter", "worn out"]
            }

            results = {"target_audience": {}, "usage_occasion": {}}

            # Run keyword search queries
            for group, keywords in targets.items():
                kw_str = " OR ".join([f"text ILIKE '%{k}%'" for k in keywords])
                count = conn.execute(f"SELECT COUNT(*) FROM reviews WHERE parent_asin = '{asin}' AND ({kw_str})").fetchone()[0]
                if count > 0: results["target_audience"][group] = count

            for group, keywords in occasions.items():
                kw_str = " OR ".join([f"text ILIKE '%{k}%'" for k in keywords])
                count = conn.execute(f"SELECT COUNT(*) FROM reviews WHERE parent_asin = '{asin}' AND ({kw_str})").fetchone()[0]
                if count > 0: results["usage_occasion"][group] = count

            return json.dumps(results)

        except Exception as e:
            return f"Context Analysis Error: {e}"
        finally:
            conn.close()

    def answer(self, user_query: str, default_asin: str = None):
        """
        Agentic flow with Memory & Keyword Search.
        """
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
        
        # Tool declarations
        tool_declarations = [types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="get_product_dna",
                description="Get technical specs and variation stats (colors/sizes) of an ASIN.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"asin": types.Schema(type="STRING")},
                    required=["asin"]
                )
            ),
            types.FunctionDeclaration(
                name="get_product_swot",
                description="Get high-level Pros, Cons, and Controversial aspects of a product.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"asin": types.Schema(type="STRING")},
                    required=["asin"]
                )
            ),
            types.FunctionDeclaration(
                name="search_review_evidence",
                description="Search for specific review quotes. Use for deep-dives.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "asin": types.Schema(type="STRING"),
                        "aspect": types.Schema(type="STRING", description="Standard aspect"),
                        "sentiment": types.Schema(type="STRING"),
                        "keyword": types.Schema(type="STRING")
                    },
                    required=["asin"]
                )
            ),
            types.FunctionDeclaration(
                name="find_better_alternatives",
                description="Find better products in the same niche.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "current_asin": types.Schema(type="STRING"),
                        "aspect_criteria": types.Schema(type="STRING")
                    },
                    required=["current_asin"]
                )
            ),
            types.FunctionDeclaration(
                name="compare_head_to_head",
                description="Directly compare two products based on sentiment scores of shared aspects.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "asin_a": types.Schema(type="STRING"),
                        "asin_b": types.Schema(type="STRING")
                    },
                    required=["asin_a", "asin_b"]
                )
            ),
            types.FunctionDeclaration(
                name="analyze_customer_context",
                description="Analyze buyer personas (Who buys?) and occasions (Why buy?). Good for questions like 'Is this good for kids?' or 'Is it a good gift?'.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"asin": types.Schema(type="STRING")},
                    required=["asin"]
                )
            )
        ])]

        # Init session if needed
        if not self.chat_session:
            vocab = self._get_vocabulary()
            vocab_str = ", ".join(vocab)
            
            system_instructions = f"""
            You are 'The Detective', an elite Amazon Market Analyst.
            
            **STRATEGY:**
            1. **General:** Use `get_product_swot` for overview.
            2. **Detail:** Use `search_review_evidence` for quotes.
            3. **Compare:** Use `compare_head_to_head` when user asks 'A vs B'.
            4. **Context:** Use `analyze_customer_context` to understand the buyer (Gift? Kids?).
            
            **KNOWLEDGE BASE (Standard Aspects):**
            [{vocab_str}]

            **RULES:**
            1. **Memory:** Default ASIN: {default_asin}.
            2. **Citations:** Cite using [YYYY-MM-DD].
            3. **Language:** Answer in the same language as the query.
            """
            
            self.chat_session = self.client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(
                    tools=tool_declarations,
                    system_instruction=system_instructions
                )
            )

        try:
            response = self.chat_session.send_message(user_query)
            
            # Manual Loop (Reused)
            max_turns = 10
            for _ in range(max_turns):
                if response.function_calls:
                    parts = []
                    for fc in response.function_calls:
                        fname = fc.name
                        fargs = fc.args
                        print(f"🤖 Agent calling: {fname}({fargs})")
                        
                        if fname in tools_map:
                            result = tools_map[fname](**fargs)
                        else:
                            result = "Error: Tool not found"
                            
                        parts.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=fname,
                                response={"result": result}
                            )
                        ))
                    response = self.chat_session.send_message(parts)
                else:
                    return response.text
            
            return "Agent got stuck in a loop."

        except Exception as e:
            # Reset session on error to avoid stuck state
            self.chat_session = None
            return f"Detective Error: {e}"

if __name__ == "__main__":
    # Test
    agent = DetectiveAgent()
    # print(agent.answer("Hello"))
