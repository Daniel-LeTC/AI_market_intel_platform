# AI ECOSYSTEM MAP (MASTER ARCHITECTURE)

## 🎯 Mục đích Tài liệu
Tài liệu này cung cấp cái nhìn đa chiều về hệ sinh thái AI:
1.  **Executive View:** Tổng quan chiến lược (Value Stream).
2.  **Architect View:** Bản đồ chi tiết luồng dữ liệu (Detailed Logic).
3.  **Engineer View:** Chi tiết kỹ thuật implementation (Code Level).
4.  **Product User View:** Góc nhìn Jobs-to-be-Done cho R&D/Marketing.

---

## 🌍 I. THE EXECUTIVE VIEW (MACRO MAP)
*Góc nhìn dành cho BOD/Stakeholders: Bức tranh tổng thể.*

```mermaid
graph LR
    %% STYLES
    classDef blue fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef orange fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef purple fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;
    classDef green fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;

    User[("👤 User / Market")]:::blue
    
    subgraph ACQ ["LAYER 1: ACQUISITION"]
        Ecom["🛒 E-Commerce Engine"]:::blue
        Social["📱 Social Engine"]:::blue
    end
    
    subgraph INTEL ["LAYER 2: INTELLIGENCE CORE"]
        DB["📥 Universal DB"]:::orange
        Processor["🧠 AI Processor"]:::orange
        Detective["🕵️ Detective Agent"]:::orange
    end
    
    subgraph CREATIVE ["LAYER 3: CPAP ENGINE"]
        Bridge["🌉 The Bridge"]:::purple
        Compiler["⚙️ Prompt Compiler"]:::purple
    end
    
    subgraph OUT ["LAYER 4: OUTPUT"]
        Dash["💻 Dashboard"]:::green
        Sol["💼 Biz Solutions"]:::green
    end

    User --> ACQ
    ACQ --> DB
    DB --> Processor
    Processor --> Detective
    Detective --> Dash
    Detective ==>|Strategic Insight| Bridge
    Bridge --> Compiler
    Compiler --> Sol
```

---

## 🗺️ II. THE ARCHITECT VIEW (DETAILED DEEP DIVE)
*Góc nhìn dành cho Product Owners: Logic vận hành chi tiết & Feedback Loop.*

```mermaid
graph TB
    %% --- STYLES ---
    classDef flow fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef ai fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef creative fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#000;
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef hidden fill:#ffffff,stroke:#607d8b,stroke-width:2px,color:#607d8b,stroke-dasharray: 5 5;

    %% --- LAYER 1: ACQUISITION ---
    subgraph ACQ ["Layer 1: Unified Acquisition"]
        direction TB
        Input_User[("👤 User Input<br/>(ASIN / Keywords)")]:::flow
        
        subgraph ECOM_FLOW ["🛒 E-Commerce Workflow"]
            direction TB
            Node_Resolver["🔍 ASIN Resolver<br/>(Parent/Child Check)"]:::flow
            Node_Fetcher_Meta["📦 Metadata Fetcher<br/>(Specs/Price/Images)"]:::flow
            Node_Fetcher_Review["📝 Review Fetcher<br/>(Text/Rating/Photos)"]:::flow
            Node_Competitor_Auto["🤖 Competitor<br/>Auto-Discovery"]:::hidden
        end
        
        subgraph SOCIAL_FLOW ["📱 Social Workflow"]
            direction TB
            Node_Social_Plan["📅 Social Planning<br/>(Budget/Filter)"]:::flow
            Node_Social_Fetch["⚡ Social Fetcher<br/>(TikTok/Meta)"]:::flow
            Node_Social_Pricing["💰 Cost Estimator"]:::hidden
        end
    end

    %% --- LAYER 2: INTELLIGENCE CORE ---
    subgraph INTEL ["Layer 2: AI Intelligence Core"]
        direction TB
        Node_Ingest["📥 Universal Ingest<br/>(Blue-Green DB)"]:::storage

        subgraph MINER_LOGIC ["⛏️ AI Miner (Extraction)"]
            direction LR
            Node_Miner_Extract["🧠 Aspect/Sentiment<br/>Extraction"]:::ai
            Node_Miner_Evidence["🔗 Evidence Linking<br/>(Quotes/IDs)"]:::ai
        end

        subgraph JANITOR_LOGIC ["🧹 Janitor (Clean)"]
            direction LR
            Node_Janitor_Match["🔍 Fuzzy/Vector<br/>Matching"]:::ai
            Node_Janitor_Dict["📚 Canonical<br/>Dictionary"]:::storage
        end

        subgraph STATS_LOGIC ["📊 Stats Engine"]
            direction LR
            Node_Stats_Agg["∑ Aggregation"]:::ai
            Node_Stats_Weight["⚖️ Bayesian<br/>Smoothing"]:::ai
            Node_Stats_Impact["📉 Net Impact<br/>Calculation"]:::ai
        end

        subgraph DETECTIVE_LOGIC ["🕵️ Detective (Strategy)"]
            direction LR
            Node_RAG["🔎 RAG Retrieval<br/>(Data+Context)"]:::ai
            Node_Reasoning["🤔 Strategic<br/>Reasoning"]:::ai
        end
    end

    %% --- LAYER 3: CPAP ---
    subgraph CPAP ["Layer 3: CPAP Engine (Creative)"]
        direction TB
        Node_Library["📚 Prompt Library &<br/>Context Registry"]:::storage
        
        subgraph LAYERS ["4-Layer Compilation"]
            direction LR
            L1["L1: Domain"]:::creative
            L2["L2: Unit"]:::creative
            L3["L3: Task"]:::creative
            L4["L4: Opt"]:::creative
        end
        
        Node_Compiler["⚙️ Prompt Compiler<br/>(Execution Node)"]:::creative
    end

    %% --- LAYER 4: OUTPUT ---
    subgraph OUT ["Layer 4: Business Touchpoints"]
        direction TB
        subgraph DASHBOARD ["Interactive Dashboard"]
            direction LR
            UI_Heatmap["🌡️ Heatmap"]:::output
            UI_Trend["📈 Trends"]:::output
            UI_Gallery["🖼️ Evidence"]:::output
        end
        UI_Mail["📧 Weekly Reports"]:::output
        UI_Biz_Sol["💼 Business Solutions"]:::output
        Node_Feedback["✍️ Feedback Form"]:::flow
    end

    %% --- CONNECTIONS (Logical Flow) ---
    Input_User --> Node_Resolver
    Node_Resolver --> Node_Fetcher_Meta
    Node_Resolver --> Node_Fetcher_Review
    Input_User --> Node_Social_Plan
    Node_Social_Plan --> Node_Social_Fetch
    
    Node_Fetcher_Meta --> Node_Ingest
    Node_Fetcher_Review --> Node_Ingest
    Node_Social_Fetch --> Node_Ingest
    
    Node_Ingest --> Node_Miner_Extract
    Node_Miner_Extract --> Node_Miner_Evidence
    Node_Miner_Evidence --> Node_Janitor_Match
    Node_Janitor_Match <--> Node_Janitor_Dict
    Node_Janitor_Match --> Node_Stats_Agg
    
    Node_Stats_Agg --> Node_Stats_Weight
    Node_Stats_Weight --> Node_Stats_Impact
    Node_Stats_Impact --> Node_RAG
    Node_RAG --> Node_Reasoning
    
    Node_Reasoning --> UI_Heatmap
    Node_Reasoning --> UI_Mail
    Node_Fetcher_Review --> UI_Gallery
    
    %% THE BRIDGE
    Node_Reasoning ==>|Market Context| Node_Compiler
    
    Node_Library --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> Node_Compiler
    Node_Compiler --> UI_Biz_Sol

    %% FEEDBACK LOOP
    UI_Heatmap --> Node_Feedback
    Node_Feedback -.->|Correction| Node_Janitor_Dict
```

---

## ⚙️ III. THE ENGINEER VIEW (MICRO DETAILS)
*Góc nhìn dành cho Dev Team: Cấu trúc Code và Luồng dữ liệu thực tế.*

### 1. Intelligence Pipeline (Code Logic)
*Mô tả luồng xử lý trong `worker_api.py` và `miner.py`*

```mermaid
graph TD
    classDef cls fill:#fff9c4,stroke:#fbc02d,stroke-width:1px,color:#000;
    classDef db fill:#e0e0e0,stroke:#616161,stroke-width:1px,color:#000;
    
    subgraph WORKER ["Worker Process"]
        Trigger["API Trigger"] --> Scraper["AmazonScraper<br/>(Apify)"]
        Scraper --> JSON["Raw JSON"]
        JSON --> Ingester["DataIngester<br/>(Pandas)"]
    end
    
    subgraph DB ["DuckDB (Blue-Green)"]
        Ingester --> Reviews["Table: reviews"]
        Ingester --> Products["Table: products"]
    end
    
    subgraph AI ["AI Processing"]
        Reviews --> Miner["AIMiner<br/>(Gemini Flash 3.0)"]
        Miner --> Tags["Table: review_tags<br/>(Raw Aspect)"]
        Tags --> Janitor["TagNormalizer<br/>(Fuzzy Match)"]
        Janitor --> Dict["Table: aspect_mapping"]
        Janitor --> CleanTags["Standardized Tags"]
    end
    
    subgraph CALC ["Calculation"]
        CleanTags --> Engine["StatsEngine"]
        Products --> Engine
        Engine --> Impact["Table: product_stats<br/>(Weighted Score)"]
    end
```

### 2. CPAP Compilation Flow (Code Logic)
*Mô tả luồng xử lý trong `src/framework/compiler.py`*

```mermaid
graph LR
    classDef py fill:#e1bee7,stroke:#8e24aa,stroke-width:1px,color:#000;
    classDef file fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,color:#000;

    Req["Request (Dict)"] --> Compiler["PromptCompiler"]:::py
    
    subgraph REGISTRY ["AssetRegistry"]
        Rules["Domain Rules<br/>(YAML)"]:::file
        Tmpl["Jinja2 Template<br/>(.j2)"]:::file
    end
    
    Rules --> Compiler
    Tmpl --> Compiler
    
    subgraph RENDER ["Jinja2 Rendering"]
        Compiler --> Merge["Merge Context"]:::py
        Merge --> Final["Final Prompt String"]:::file
    end
```

---

## 💼 IV. THE PRODUCT USER VIEW (JOBS TO BE DONE)
*Góc nhìn dành cho R&D/Product Developer: Tập trung vào giải quyết vấn đề, ẩn đi kỹ thuật.*

```mermaid
graph TD
    %% STYLES
    classDef job fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef engine fill:#eeeeee,stroke:#9e9e9e,stroke-width:1px,color:#616161,stroke-dasharray: 5 5;
    classDef output fill:#ffecb3,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef action fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#000;

    %% --- 1. USER INTENT (JOBS) ---
    subgraph INTENT ["1. What do you want to do today?"]
        direction TB
        Job_Fix["🛠️ Fix Current Product<br/>(Pain Points)"]:::job
        Job_Beat["⚔️ Beat Competitors<br/>(Gap Analysis)"]:::job
        Job_Innovate["💡 Find New Ideas<br/>(Innovation Radar)"]:::job
    end

    %% --- 2. HIDDEN ENGINE (BLACK BOX) ---
    subgraph ENGINE ["2. The AI Processing Core (Hidden)"]
        direction TB
        Process["⚙️ Data Mining & Reasoning Engine"]:::engine
    end

    %% --- 3. ACTIONABLE OUTPUTS (R&D ARTIFACTS) ---
    subgraph OUTPUTS ["3. R&D Artifacts (Outputs)"]
        direction TB
        
        subgraph BOARD ["Improvement Board"]
            Out_Prioritized["🔴 Top 3 Critical Issues<br/>(Impact Score)"]:::output
            Out_Love["🟢 Top 5 Love Points<br/>(Preserve Features)"]:::output
        end
        
        subgraph GAP ["Competitor Gap Map"]
            Out_Feature_Gap["📊 Feature Comparison Matrix"]:::output
            Out_Price_Pos["💲 Pricing Recommendations"]:::output
        end
        
        subgraph RADAR ["Innovation Radar"]
            Out_Usage["🧘 New Usage Scenarios<br/>(Unusual Contexts)"]:::output
            Out_Social_Trend["🎵 Cross-channel Trends<br/>(TikTok vs Amazon)"]:::output
        end
    end

    %% --- 4. NEXT ACTIONS (BRIDGE) ---
    subgraph ACTIONS ["4. Recommended Actions (CPAP)"]
        direction TB
        Act_Design["🎨 Design Specs Draft"]:::action
        Act_Listing["📝 Listing Optimization"]:::action
        Act_Brief["🎬 Marketing Brief"]:::action
    end

    %% CONNECTIONS
    Job_Fix --> Process
    Job_Beat --> Process
    Job_Innovate --> Process

    Process --> Out_Prioritized
    Process --> Out_Love
    Process --> Out_Feature_Gap
    Process --> Out_Price_Pos
    Process --> Out_Usage
    Process --> Out_Social_Trend

    Out_Prioritized --> Act_Design
    Out_Feature_Gap --> Act_Listing
    Out_Usage --> Act_Brief
```

---

## 📝 Giải thích cho R&D (Ngôn ngữ loài người)

1.  **Bạn không cần biết ASIN là gì:** Bạn chỉ cần chọn mục tiêu ("Sửa lỗi", "Đánh đối thủ", hay "Tìm ý tưởng").
2.  **Product Improvement Board:** Trả lời câu hỏi *"Top 3 thứ nếu fix xong thì rating tăng rõ rệt?"*.
3.  **Competitor Gap Map:** Trả lời câu hỏi *"Đối thủ hơn/thua mình cái gì?"*.
4.  **Innovation Radar:** Trả lời câu hỏi *"Khách đang dùng sản phẩm đi đâu, làm gì mà mình chưa biết?"*.