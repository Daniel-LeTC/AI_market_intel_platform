# Database Architecture: ERD & Data Lineage

## 1. Entity Relationship Diagram (ERD)

### 🔴 Core Application (`scout_a.duckdb` / `scout_b.duckdb`)
The brain of Product Intelligence.

```mermaid
erDiagram
    %% Core Product Relationships
    product_parents ||--|{ products : "groups"
    products ||--o{ reviews : "has"
    products ||--|{ product_stats : "caches_metrics_for"
    
    %% AI Analysis
    reviews ||--o{ review_tags : "analyzed_into"
    review_tags }o--|| aspect_mapping : "normalized_by"

    product_parents {
        string parent_asin PK "The Canonical Anchor"
        string category "Strict Arena Definition"
        string niche "Flexible Sub-segment"
        string title
        string brand
        string image_url
        timestamp last_updated
    }

    products {
        string asin PK "Child/Variation ASIN"
        string parent_asin FK
        string title
        string brand
        double real_average_rating "Source of Truth"
        int real_total_ratings "Source of Truth"
        json rating_breakdown "Histogram {5: 100, 1: 20}"
        json specs_json "Raw Key-Value Pairs"
        string material "Extracted DNA"
        string target_audience "Extracted DNA"
        timestamp last_updated
    }

    reviews {
        string review_id PK
        string parent_asin FK "Partition Key"
        string child_asin
        string text "Raw Content"
        double rating_score
        date review_date
        string mining_status "PENDING, QUEUED, COMPLETED"
    }

    review_tags {
        uuid tag_id PK
        string review_id FK
        string parent_asin FK "Performance Denormalization"
        string aspect "Raw Extracted Term"
        string sentiment "Positive/Negative/Neutral"
        string quote "Evidence Slice"
        string category "AI-assigned bucket"
    }

    aspect_mapping {
        string raw_aspect PK "Dirty Term"
        string standard_aspect "Clean Canonical Term"
        string category
    }

    product_stats {
        string asin PK
        json metrics_json "Pre-calculated OLAP Cube"
        timestamp last_updated
    }
```

### 🔵 System & Operations (`system.duckdb`)
The Control Plane.

```mermaid
erDiagram
    users ||--o{ user_wallets : "funds"
    users ||--o{ scrape_queue : "requests"
    
    users {
        string user_id PK
        string username
        string password_hash "Bcrypt"
        string role "ADMIN/USER"
        float monthly_budget
    }

    user_wallets {
        string user_id FK
        float current_spend
        date last_reset
    }

    scrape_queue {
        string request_id PK
        string asin "Requested Target"
        string status "PENDING_APPROVAL -> COMPLETED"
        string requested_by FK
        string note
        timestamp created_at
    }

    user_feedback {
        int id PK
        string user_identity
        string feature_request
        string bug_report
    }
```

---

## 2. Data Usage Matrix (Code-to-Column Mapping)

### Table: `products` (The DNA Store)

| Column | Written By (Writer) | Read By (Reader) | Business Logic / Purpose |
| :--- | :--- | :--- | :--- |
| `asin` | `ingest.py` (Upsert), `worker_product_details.py` | `stats_engine.py` (Key), `ui/common.py` | Primary Key. Child Variation. |
| `parent_asin` | `ingest.py` (Filial Son Logic), `worker_parent_asin.py` | `miner.py` (Grouping), `ui/tabs/overview.py` (DNA Aggregation) | Foreign Key linking variation to family. Critical for aggregation. |
| `real_total_ratings` | `metadata_parser.py` (From Apify) | `stats_engine.py` (Weighted Logic), `ui/tabs/showdown.py` (Smart Match) | **Source of Truth** for Volume. Used to calculate "Estimated Impact". |
| `rating_breakdown` | `metadata_parser.py` (Parsed from JSON) | `stats_engine.py` (Weighted Logic) | The histogram needed to extrapolate sample data to population reality. |
| `material` | `worker_product_details.py` (Heuristic), `metadata_parser.py` | `ui/tabs/overview.py` (DNA Display) | Technical spec for product understanding. |

### Table: `reviews` (The Raw Voice)

| Column | Written By | Read By | Business Logic / Purpose |
| :--- | :--- | :--- | :--- |
| `text` | `ingest.py` (From XLSX/JSONL) | `miner.py` (AI Analysis) | Raw review content. The source of all insights. |
| `mining_status` | `ingest.py` (Default='PENDING'), `miner.py` (Update='COMPLETED'), `manage.py` (Reset) | `miner.py` (Filter WHERE PENDING) | **State Machine** for AI processing pipeline. |
| `rating_score` | `ingest.py` | `stats_engine.py` (Trend Analysis) | Used for Rating Trend Chart and as fallback if `rating_breakdown` missing. |

### Table: `review_tags` (The Intelligence)

| Column | Written By | Read By | Business Logic / Purpose |
| :--- | :--- | :--- | :--- |
| `aspect` | `miner.py` (From AI) | `normalizer.py` (To Clean), `stats_engine.py` (Aggregation) | The raw topic extracted (e.g., "too soft", "very thin"). |
| `sentiment` | `miner.py` (From AI) | `stats_engine.py` (Net Impact), `ui/tabs/showdown.py` (Battle) | Sentiment polarity. Drivers of "Visual Score". |
| `quote` | `miner.py` (From AI) | `ui/tabs/xray.py` (Evidence Drill-down), `audit_detective.py` (QA) | Proof snippet. Displayed when user clicks a heatmap cell. |

### Table: `product_stats` (The OLAP Cache)

| Column | Written By | Read By | Business Logic / Purpose |
| :--- | :--- | :--- | :--- |
| `metrics_json` | `stats_engine.py` (Serialize) | `ui/common.py` (Deserialize), `ui/tabs/*.py` | **Performance Optimization**. Stores heavy calculations (Weighted Sentiment, Trends) so UI loads instantly without recounting millions of rows. |

### Table: `scrape_queue` (The Gatekeeper)

| Column | Written By | Read By | Business Logic / Purpose |
| :--- | :--- | :--- | :--- |
| `status` | `ui/common.py` (Insert PENDING), `99_Admin_Console.py` (Approve/Reject), `worker_parent_asin.py` (Complete) | `99_Admin_Console.py` (Dashboard), `worker_api.py` | Workflow tracking for user requests. |

### Table: `aspect_mapping` (The Dictionary)

| Column | Written By | Read By | Business Logic / Purpose |
| :--- | :--- | :--- | :--- |
| `standard_aspect` | `normalizer.py` (Janitor AI) | `stats_engine.py` (Join), `ui/tabs/xray.py` (Grouping) | **Canonical Term**. Groups "soft", "softness", "texture" -> "Softness". Essential for clean charts. |
