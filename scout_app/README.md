# 🕵️ RnD Scout UI - The Detective Agent

Welcome to the frontend of **RnD Scout**. This app provides a visual interface to explore Amazon competitor data and chat with a specialized AI Analyst.

---

## 🎨 Features

### 1. Home Dashboard 🏠
- **Product DNA:** High-level specs (Material, Niche, Brand) extracted from R&D sheets.
- **AI Intelligence:** Heatmap of sentiments and top pain points based on thousands of reviews.
- **Evidence Board:** Direct citations (Quotes) from customers, filtered by aspect and sentiment.

### 2. The Arena (Battle Mode) ⚔️
- Side-by-side comparison of two ASINs.
- **Shared Features:** See who wins on common attributes (e.g., Softness).
- **Exclusive Features:** Identify unique selling points (USPs) or unique flaws.

### 3. AI Detective V4.4 🕵️‍♂️
An agentic chat interface that doesn't just talk, but **acts**.
- **Context Awareness:** Remembers the last ASIN discussed.
- **Evidence Search:** Can find specific quotes using synonyms (Vietnamese/English).
- **Market Scout:** Can recommend "better" products from the same niche based on sentiment scores.
- **Variation Intel:** Understands the complexity of color/size combinations.

---

## 🚀 How to Run

```bash
uv run streamlit run scout_app/Market_Intelligence.py
```

### 💡 Tips for 'The Detective'
- Ask: *"What are the top 3 complaints for this product?"*
- Ask: *"Is there anything better in the same category but with better durability?"*
- Ask: *"Does it have many colors? List the most popular ones."*
- Ask: *"Show me evidence of people complaining about holes after washing."*

---

## ⚙️ Technical Notes
- **Database:** Connects to `scout.duckdb` in **Read-Only** mode to allow parallel background processing.
- **AI Model:** Powered by `gemini-2.5-flash-lite`.
- **Latency:** SQL queries are indexed for sub-second response on datasets up to 100k+ tags.