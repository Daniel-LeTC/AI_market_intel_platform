# AI ECOSYSTEM MAP (MASTER ARCHITECTURE)

## 🎯 Mục đích Tài liệu
Tài liệu này cung cấp cái nhìn đa chiều về hệ sinh thái AI:
1.  **Executive View:** Tổng quan chiến lược (Value Stream).
2.  **Architect View:** Bản đồ chi tiết luồng dữ liệu (Detailed Logic).
3.  **Engineer View:** Chi tiết kỹ thuật implementation (Code Level).
4.  **Product User View:** Góc nhìn Jobs-to-be-Done và Tương tác (Interactive Console) cho R&D/Marketing.

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
    
    %% Dual Output Path
    Processor -->|Real-time Metrics| Dash
    Detective -->|Strategic Insight| Dash
    
    Detective ==>|Insight Context| Bridge
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
    classDef future fill:#ffffff,stroke:#607d8b,stroke-width:2px,color:#607d8b,stroke-dasharray: 5 5;

    %% --- LAYER 1: ACQUISITION ---
    subgraph ACQ ["Layer 1: Unified Acquisition"]
        direction TB
        Input_User[("👤 User Input")]:::flow
        subgraph ECOM_FLOW ["🛒 E-Commerce"]
            direction TB
            Node_Resolver["🔍 Resolver"]:::flow
            Node_Fetcher_Meta["📦 Meta Fetcher"]:::flow
            Node_Fetcher_Review["📝 Review Fetcher"]:::flow
            Node_Competitor_Auto["🤖 Competitor Auto"]:::future
        end
        subgraph SOCIAL_FLOW ["📱 Social"]
            direction TB
            Node_Social_Plan["📅 Planning"]:::flow
            Node_Social_Fetch["⚡ Fetcher"]:::flow
        end
    end

    %% --- LAYER 2: INTELLIGENCE ---
    subgraph INTEL ["Layer 2: Intelligence Core"]
        direction TB
        Node_Ingest["📥 Universal Ingest"]:::storage
        subgraph MINER_LOGIC ["⛏️ Miner Engine"]
            direction LR
            Node_Miner_Extract["🧠 Extraction"]:::ai
            Node_Miner_Evidence["🔗 Evidence"]:::ai
        end
        subgraph JANITOR_LOGIC ["🧹 Janitor Engine"]
            direction LR
            Node_Janitor_Match["🔍 Matching"]:::ai
            Node_Janitor_Dict["📚 Dictionary"]:::storage
        end
        subgraph STATS_LOGIC ["📊 Stats Engine"]
            direction LR
            Node_Stats_Agg["∑ Agg"]:::ai
            Node_Stats_Weight["⚖️ Bayes"]:::ai
            Node_Stats_Impact["📉 Impact"]:::ai
        end
        subgraph DETECTIVE_LOGIC ["🕵️ Detective Agent"]
            direction LR
            Node_RAG["🔍 RAG"]:::ai
            Node_Reasoning["🤔 Reasoning"]:::ai
        end
    end

    %% --- LAYER 3: CPAP ---
    subgraph CPAP ["Layer 3: CPAP Engine"]
        direction TB
        Node_Library["📚 Context Registry"]:::storage
        subgraph LAYERS ["4-Layer Compilation"]
            direction TB
            L1["L1: Domain (Brand)"]:::creative
            L2["L2: Unit (Dept)"]:::creative
            L3["L3: Task (Specific)"]:::creative
            L4["L4: Opt (Keywords)"]:::creative
        end
        Node_Compiler["⚙️ Prompt Compiler"]:::creative
    end

    %% --- LAYER 4: OUTPUT ---
    subgraph OUT ["Layer 4: Business Touchpoints"]
        direction TB
        subgraph DASHBOARD ["💻 Dashboard"]
            direction LR
            UI_Heatmap["🌡️ Heatmap"]:::output
            UI_Trend["📈 Trends"]:::output
            UI_Gallery["🖼️ Evidence"]:::output
        end
        UI_Mail["📧 Weekly Reports"]:::output
        UI_Biz_Sol["💼 Biz Solutions"]:::output
        Node_Feedback["✍️ Feedback Form"]:::flow
    end

    %% --- CONNECTIONS ---
    Input_User --> Node_Resolver
    Node_Resolver --> Node_Fetcher_Meta
    Node_Fetcher_Meta --> Node_Fetcher_Review
    Node_Fetcher_Review --> Node_Competitor_Auto
    Input_User --> Node_Social_Plan
    Node_Social_Plan --> Node_Social_Fetch
    
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
    Node_Reasoning ==>|Market Context| Node_Compiler
    
    Node_Library --> L1
    L1 --> L2 --> L3 --> L4 --> Node_Compiler
    Node_Compiler --> UI_Biz_Sol
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

## 💼 IV. THE PRODUCT USER VIEW (INTERACTIVE CONSOLE - REALITY MAPPED)
*Góc nhìn thực tế cho User: Map trực tiếp Jobs-to-be-Done vào các Module hệ thống.*

```mermaid
graph TD
    %% STYLES
    classDef job fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef sys fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef out fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef action fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;

    %% --- 1. USER JOBS (INPUT) ---
    subgraph INTENT ["1. User Intent (Choose Job)"]
        direction TB
        Job_Fix["🛠️ Fix Product Problems<br/>(Pain Points)"]:::job
        Job_Beat["⚔️ Analyze Competitors<br/>(Gap Analysis)"]:::job
        Job_Auto["⚡ Automate Content<br/>(Create Assets)"]:::job
    end

    %% --- 2. SYSTEM PROCESSING (TRANSPARENT BOX) ---
    subgraph SYSTEM ["2. System Execution (White Box)"]
        direction TB
        Node_Scan["📡 1. Scanning<br/>(Fetch Data)"]:::sys
        Node_Analyze["🧠 2. Analyzing<br/>(Mining & Stats)"]:::sys
        Node_Synth["🕵️ 3. Synthesizing<br/>(Detective Reasoning)"]:::sys
    end

    %% --- 3. INTERACTIVE OUTPUTS (TOUCHPOINTS) ---
    subgraph VIEW ["3. Interactive Views (Dashboard)"]
        direction TB
        Out_Issues["🔴 Prioritized Issues<br/>(Powered by StatsEngine)"]:::out
        Out_Evidence["🔍 Evidence Gallery<br/>(Quotes/Photos from Miner)"]:::out
        Out_Gap["📊 Competitor Matrix<br/>(Feature Comparison)"]:::out
    end

    %% --- 4. ACTIONABLE ARTIFACTS (CPAP OUTPUT) ---
    subgraph EDITOR ["4. Editor Workspace (Human-in-the-Loop)"]
        direction TB
        Act_Report["📧 R&D Report<br/>(Summary + Data)"]:::action
        Act_Content["📝 Optimized Content<br/>(Listing/Email/JD)"]:::action
        Act_Plan["📅 Strategic Plan<br/>(Next Steps)"]:::action
    end

    %% FLOW MAPPING
    Job_Fix --> Node_Scan
    Job_Beat --> Node_Scan
    
    %% Logic Data
    Node_Scan --> Node_Analyze
    Node_Analyze --> Node_Synth
    
    %% Logic Auto
    Job_Auto --> Node_Synth

    Node_Analyze --> Out_Issues
    Node_Analyze --> Out_Evidence
    Node_Synth --> Out_Gap

    %% User Interactive Loop
    Out_Issues --> Out_Evidence
    Out_Evidence --> Act_Plan
    Out_Gap --> Act_Content

    %% Automation Link
    Node_Synth ==>|Context| Act_Content
    Node_Synth ==>|Summary| Act_Report
```

---

## 📝 Giải thích Mapping (Code to User Value)

1.  **Transparent Processing:** Thay vì "Blackbox", hệ thống hiển thị rõ 3 bước xử lý: Lấy dữ liệu (`Fetcher`) -> Tính toán trọng số (`StatsEngine`) -> Suy luận (`Detective`). User hiểu tại sao ra kết quả này.
2.  **Evidence-Based:** Mọi insight (`Out_Issues`) đều link trực tiếp về bằng chứng (`Out_Evidence`). Đây là tính năng của `Node_Miner_Evidence` trong code.
3.  **Human-in-the-Loop:** Output nằm trong `Editor Workspace`. User có thể chỉnh sửa trước khi xuất bản, không phó mặc hoàn toàn cho AI.
