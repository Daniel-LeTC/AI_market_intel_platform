# 🎨 Visual Architecture Reference

This document provides a visual breakdown of the **Bright Scraper Tool** system using Mermaid diagrams. It aggregates the structural and logical flows described in the other analysis documents.

## 1. System Landscape (High-Level)

A macroscopic view of how users, the system, and external dependencies interact.

```mermaid
graph TD
    %% Actors
    User((User / Analyst))
    Admin((SysAdmin / Dev))

    %% External Systems
    subgraph "External Ecosystem"
        Amazon[Amazon.com]
        Social[TikTok / Meta]
        Apify[Apify Cloud]
        Gemini[Google Gemini AI]
        CloudBatch[Google Cloud Batch]
        SendGrid[SendGrid Email]
    end

    %% The System
    subgraph "Bright Scraper Tool"
        style UI fill:#e1f5fe,stroke:#01579b
        style API fill:#e0f2f1,stroke:#004d40
        style DB fill:#fff3e0,stroke:#e65100
        style Core fill:#f3e5f5,stroke:#4a148c

        UI[Streamlit UI :8501]
        API[Worker API :8000]
        CLI[Manage CLI]
        
        DB[(DuckDB Cluster)]
        
        subgraph "Core Logic Modules"
            id1[Scrapers]
            id2[Ingester]
            id3[AI Miner]
            id4[Stats Engine]
        end
    end

    %% Interactions
    User -->|Browser HTTPS| UI
    Admin -->|SSH/Shell| CLI
    
    UI -->|HTTP Triggers| API
    UI -->|Reads Analytics| DB
    
    API -->|Dispatches| id1
    API -->|Dispatches| id2
    API -->|Dispatches| id3
    
    CLI -->|Controls| CloudBatch
    CLI -->|Direct Exec| id3

    %% External Calls
    id1 -->|Scrapes| Amazon
    id1 -->|Scrapes| Social
    id1 -->|Delegates| Apify
    
    id3 -->|Inference| Gemini
    id4 -->|Reports| SendGrid
    
    %% Data Persistence
    id1 & id2 & id3 & id4 -->|Read/Write| DB
```

---

## 2. The Core Data Pipeline (Sequence)

The journey of data from a User Request to Actionable Insights.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit UI
    participant API as Worker API
    participant Scraper as Scraper Module
    participant Ingest as Data Ingester
    participant DB as DuckDB (Storage)
    participant Miner as AI Miner
    participant Stats as Stats Engine

    Note over User, DB: Phase 1: Acquisition & Ingestion
    User->>UI: Enter ASINs & Click "Start"
    UI->>API: POST /trigger/weekly_report
    API->>Scraper: Spawn Background Task
    Scraper->>Scraper: Fetch Metadata & Reviews (Apify/Selenium)
    Scraper->>Ingest: Handover Raw JSON/XLSX
    
    rect rgb(230, 240, 255)
        Note right of Ingest: Blue-Green Deployment Logic
        Ingest->>DB: Upsert Products (Standby DB)
        Ingest->>DB: Swap Active <-> Standby Pointers
    end
    
    Ingest-->>API: Ingestion Complete
    
    Note over API, Stats: Phase 2: Intelligence & Analysis
    API->>Miner: Trigger AI Mining
    Miner->>DB: Fetch 'PENDING' Reviews
    loop Batch Processing
        Miner->>Miner: Generate Prompts
        Miner->>DB: Write Tags & Sentiment (Status: COMPLETED)
    end
    
    API->>Stats: Trigger Re-calculation
    Stats->>DB: Aggregate & Weight Metrics
    Stats->>DB: Cache Results in `product_stats`
    
    Stats-->>User: Email Report (SendGrid)
    User->>UI: View Interactive Dashboard (X-Ray/Showdown)
```

---

## 3. Database Schema (ERD)

A visual representation of the 3-Database Architecture (`scout`, `social`, `system`).

```mermaid
erDiagram
    %% --- SCOUT DATABASE (Product Intelligence) ---
    PRODUCT_PARENTS ||--|{ PRODUCTS : "groups"
    PRODUCTS ||--o{ REVIEWS : "has"
    PRODUCTS ||--|| PRODUCT_STATS : "caches"
    REVIEWS ||--o{ REVIEW_TAGS : "analyzed_into"
    REVIEW_TAGS }o--|| ASPECT_MAPPING : "normalized_by"

    PRODUCT_PARENTS {
        string parent_asin PK
        string category
        string niche
        string title
        timestamp last_updated
    }

    PRODUCTS {
        string asin PK
        string parent_asin FK
        double real_average_rating
        int real_total_ratings
        json rating_breakdown
        json specs_json
    }

    REVIEWS {
        string review_id PK
        string parent_asin FK
        string text
        double rating_score
        string mining_status
    }

    REVIEW_TAGS {
        uuid tag_id PK
        string review_id FK
        string aspect
        string sentiment
        string quote
    }

    PRODUCT_STATS {
        string asin PK
        json metrics_json
    }

    %% --- SYSTEM DATABASE (Ops) ---
    USERS ||--o{ USER_WALLETS : "has"
    USERS ||--o{ SCRAPE_QUEUE : "requests"

    USERS {
        string user_id PK
        string username
        string role
        float monthly_budget
    }

    USER_WALLETS {
        string user_id FK
        float current_spend
    }

    SCRAPE_QUEUE {
        string request_id PK
        string asin
        string status
    }
```

---

## 4. Admin & Orchestration Flow

How the system manages background tasks and scaling.

```mermaid
flowchart TD
    subgraph "Control Plane"
        UI_Admin[Admin Console UI]
        CLI[Manage.py]
    end

    subgraph "Orchestration Layer"
        API[Worker API :8000]
        Router[Social Router]
        Wallet[WalletGuard]
    end

    subgraph "Execution Layer"
        direction TB
        Proc1[Subprocess: Headless Browser]
        Proc2[Thread: AI Miner]
        Proc3[Thread: Data Ingester]
        Proc4[Cloud: Batch Job]
    end

    %% Trigger Flows
    UI_Admin -->|HTTP POST| API
    UI_Admin -->|HTTP POST| Router
    CLI -->|Direct Call| Proc4
    
    %% API Dispatch
    API -->|BackgroundTasks| Proc1
    API -->|BackgroundTasks| Proc2
    API -->|BackgroundTasks| Proc3
    
    %% Logic Checks
    Router -->|Check Funds| Wallet
    Wallet -- Yes --> Proc1
    Wallet -- No --> Reject[Return 402 Payment Required]

    %% Feedback Loop
    Proc2 -->|Write| DB[(DB)]
    Proc4 -->|Write| DB
    DB -->|Status Check| UI_Admin
```
