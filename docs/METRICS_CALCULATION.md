# Data Metrics & Calculation Logic Documentation

**Date:** January 21, 2026  
**Module:** Market Intelligence Dashboard (Bright Scraper Tool)

## 1. Introduction

This document details the methodologies used for calculating and displaying key performance indicators (KPIs) and analytical metrics within the Market Intelligence Dashboard. 

### The Selection Bias Problem
Previously, metrics were calculated based on the dataset of scraped reviews (`reviews` table). Due to the scraping strategy (sampling ~100 reviews per star rating to ensure balanced sentiment analysis), the resulting dataset does not represent the actual market distribution.
- **Example:** A product with 80% 5-star ratings on Amazon would appear to have ~20% 5-star ratings in our database due to the sampling limit.
- **Consequence:** Average Rating and Total Review counts were statistically incorrect.

### The Solution: Dual-Source Logic
We now utilize a dual-source approach:
1.  **Quantitative Metrics (KPIs):** Sourced directly from **Product Metadata** (`products` table), which reflects the "Source of Truth" from the platform (e.g., Amazon Product Page).
2.  **Qualitative Metrics (Sentiment):** Sourced from **Scraped Reviews** (`reviews` table), utilizing the biased sample to provide deep, balanced insights into both positive and negative aspects.

---

## 2. Metric Definitions

### 2.1. Executive Summary (Tab 1)

| Metric Name | Display Name | Data Source | Calculation Logic |
| :--- | :--- | :--- | :--- |
| **Total Reviews** | Total Ratings (Real) | `products.real_total_ratings` | Direct value extracted from the "countRatings" field in the scraped metadata. Represents the total number of ratings on the platform, not the count of rows in our DB. |
| **Average Rating** | Average Rating (Real) | `products.real_average_rating` | Direct value extracted from the "productRating" or "averageRating" field. |
| **Variations** | Variations Tracked | `reviews` table | `COUNT(DISTINCT child_asin)`. This metric remains based on the scraped dataset to show how many variations we have actually analyzed/ingested. |
| **Negative %** | Negative Rating % | `products.rating_breakdown` | Calculated by summing the percentage share of 1-star and 2-star ratings from the official histogram.<br>**Formula:** `(1_star_pct + 2_star_pct)` from Metadata JSON. |

### 2.2. Customer X-Ray (Tab 2)

| Metric Name | Data Source | Calculation Logic | Notes |
| :--- | :--- | :--- | :--- |
| **Rating Distribution** | `products.rating_breakdown` | Displays the JSON object `{"5": X%, "4": Y%, ...}` directly. | **FIXED:** Previously calculated via `GROUP BY rating_score` on scraped reviews, which resulted in a flat distribution. Now shows true market reality. |
| **Aspect Sentiment** | `review_tags` table | `SUM(Positive)` vs `SUM(Negative)` for each aspect. | **Qualitative Only.** This chart visualizes the *frequency of mention* within our sampled dataset. It answers "What are people talking about?" rather than "What percentage of all buyers think this?". |
| **Rating Trend** | `reviews` table | `AVG(rating_score)` grouped by Month. | **Potential Bias Warning.** Since we sample reviews historically, this trend line represents the average score of the *reviews we scraped*, not necessarily the historical average rating of the product at that point in time. It is useful for detecting spikes in negative feedback but not for absolute rating tracking. |

### 2.3. Market Showdown (Tab 3) - The "Beauty Pageant" Logic

**Problem:** Comparing products with vastly different review counts (e.g., 60k vs 1k) using sampled data creates false equivalencies. A "Veteran" product (60k) will have more varied complaints in the sample than a "Rookie" (1k), making the Rookie look artificially better.

**Solution:** Instead of a direct "Head-to-Head" fight on biased charts, we adopt a "Profile Comparison" approach across 3 independent rounds.

| Round | Metric | Logic | Goal |
| :--- | :--- | :--- | :--- |
| **1. Popularity & Trust** | `real_total_ratings` & `real_average_rating` | Direct comparison of Metadata. | Determine the "Heavyweight Champion" (Market Leader) vs. "Challenger". |
| **2. Stability (Safe Buy)** | `rating_breakdown` | Compare % of 4-star + 5-star ratings. | **Metric:** `Safe Buy Score`. Indicates which product is less risky to purchase based on official stats. |
| **3. Feature Signature** | `review_tags` (Positives) | Identify Top 3 most mentioned features in *Positive* reviews for each ASIN. | **Topic Modeling.** Instead of asking "Who has better battery?", we ask "What is this product known for?". (e.g., Product A: "Battery", Product B: "Price"). |

---

## 3. Data Mapping Reference

### Ingestion Mapping (Excel -> DuckDB)

The following mapping is applied during the ingestion of raw Apify/Scraper export files (Excel):

| Excel Raw Column | DuckDB Column (`products`) | Transformation |
| :--- | :--- | :--- |
| `productRating` | `real_average_rating` | Regex extraction of float (e.g., "4.5 out of 5" -> `4.5`). |
| `countRatings` | `real_total_ratings` | Cast to Integer. |
| `reviewSummary/fiveStar/percentage` | `rating_breakdown` (JSON) | Key "5" |
| `reviewSummary/fourStar/percentage` | `rating_breakdown` (JSON) | Key "4" |
| `reviewSummary/threeStar/percentage` | `rating_breakdown` (JSON) | Key "3" |
| `reviewSummary/twoStar/percentage` | `rating_breakdown` (JSON) | Key "2" |
| `reviewSummary/oneStar/percentage` | `rating_breakdown` (JSON) | Key "1" |

---

## 4. Known Limitations & Future Improvements

1.  **Weighted Sentiment Score (Not yet implemented):**
    *   Currently, "Aspect Sentiment" is an unweighted average of the scraped reviews.
    *   *Proposed Improvement:* Calculate a "Weighted Aspect Score" by combining the aspect sentiment from each star tier (from reviews) with the weight of that tier (from `rating_breakdown`).
    *   *Formula:* $Score = \sum_{i=1}^{5} (Sentiment_i \times Weight_i)$

2.  **Variation Metadata & Automated Enrichment:**
    *   Previously, metadata for Child ASINs was fragmented or missing.
    *   **Automated Enrichment Flow:** The `DataIngester` now automatically detects `variationId` in raw review scrapers and populates the `products` table with child-level metadata (image, title, specs) while maintaining a strict link to the validated `parent_asin`.
    *   This ensures that even if we only scrape reviews for a Parent ASIN, our `products` table becomes "enriched" with its active child variations.

3.  **Trend Accuracy:**
    *   The "Rating Trend over Time" graph is derived from sampled individual reviews. It does not reflect the "Average Rating" displayed on the product page at that specific past date.

## 5. Hybrid Sentiment Analysis Logic (Proposed Solution)

To address the trade-off between statistical accuracy and qualitative depth, the Aspect Sentiment Analysis employs a dual-view approach.

### 5.1. View 1: Detective Insights (Raw Mentions)
- **Goal:** Identify hidden product flaws and specific customer pain points.
- **Logic:** Unweighted count of mentions in the scraped dataset.
- **Why use it:** Because we sample 100 reviews per star rating, negative feedback is intentionally amplified. This view acts as a "magnifying glass" for R&D and Quality Control to see issues that might be statistically small but critical for improvement.
- **Terminology:** "Feature Frequency (Sampled)".

### 5.2. View 2: Market Impact (Weighted Sentiment)
- **Goal:** Understand the actual perception of the majority of the customer base.
- **Logic:** Weighted average combining Star-Tier Sentiment with Star-Tier Market Share.
- **Formula:** 
  $$Score_{Aspect} = \sum_{i=1}^{5} (Sentiment\_Rate_{i} \times Market\_Share\_Weight_{i})$$
  *   $Sentiment\_Rate_{i}$: Positivity rate of the aspect within the $i$-star review group in our DB.
  *   $Market\_Share\_Weight_{i}$: The percentage of $i$-star ratings from the official Amazon histogram.
- **Why use it:** Provides an accurate representation of the product's reputation. It prevents minor complaints from 1-star reviews from distorting the overall successful image of a high-rated product.
- **Terminology:** "Market Sentiment Score (Weighted)".