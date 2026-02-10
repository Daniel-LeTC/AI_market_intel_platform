# AI ECOSYSTEM MAP (MASTER ARCHITECTURE)

## 🎯 Mục đích Tài liệu
Tài liệu này cung cấp cái nhìn đa chiều về hệ sinh thái AI:
1.  **Executive View:** Tổng quan chiến lược cho Ban Lãnh đạo.
2.  **Architect View:** Bản đồ chi tiết luồng dữ liệu và logic hệ thống.
3.  **Engineer View:** Chi tiết kỹ thuật từng module để triển khai/bảo trì.

---

## 🌍 I. THE EXECUTIVE VIEW (MACRO MAP)
*Góc nhìn dành cho BOD/Stakeholders: Bức tranh luồng giá trị (Value Stream).*

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

## 🗺️ II. THE ARCHITECT VIEW (DETAILED STRATEGIC MAP)
*Dành cho Product Owners/Architects: Luồng vận hành chi tiết và các điểm chạm.*

```mermaid
graph TD
    %% --- STYLES ---
    classDef flow fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef ai fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef creative fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#000;
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef hidden fill:#ffffff,stroke:#607d8b,stroke-width:2px,color:#607d8b,stroke-dasharray: 5 5;

    %% --- LAYER 1: UNIFIED ACQUISITION ---
    subgraph ACQ ["Layer 1: Unified Acquisition & Routing"]
        direction TB
        Input_User[("👤 User Input")]:::flow
        
        subgraph ECOM_FLOW ["E-Commerce Workflow"]
            Node_Resolver["🔍 ASIN Resolver"]:::flow
            Node_Forwarder{"Is Child?"}:::flow
            Node_Competitor_Auto["🤖 Competitor Discovery"]:::hidden
            Node_Fetcher_Meta["📦 Metadata Fetcher"]:::flow
            Node_Fetcher_Review["📝 Review Fetcher"]:::flow
        end
        
        subgraph SOCIAL_FLOW ["Social Workflow Engine"]
            Node_Social_Plan["📅 Social Planning"]:::flow
            Node_Social_Fetch["📱 Social Fetcher"]:::flow
            Node_Social_Pricing["💰 Cost Estimator"]:::hidden
        end
    end

    %% --- LAYER 2: DEEP INTELLIGENCE (AI CORE) ---
    subgraph INTEL ["Layer 2: AI Intelligence Core"]
        direction TB
        Node_Ingest["📥 Universal Ingest"]:::storage

        subgraph MINER_LOGIC ["AI Miner"]
            Node_Miner_Extract["🧠 Extraction"]:::ai
            Node_Miner_Evidence["🔗 Evidence Linking"]:::ai
        end

        subgraph JANITOR_LOGIC ["Janitor"]
            Node_Janitor_Match["🧹 Matching"]:::ai
            Node_Janitor_Dict["📚 Dictionary"]:::storage
        end

        subgraph STATS_LOGIC ["Stats Engine"]
            Node_Stats_Agg["∑ Aggregation"]:::ai
            Node_Stats_Weight["⚖️ Bayesian Smooth"]:::ai
            Node_Stats_Impact["📉 Impact Score"]:::ai
        end

        subgraph DETECTIVE_LOGIC ["Detective Agent"]
            Node_RAG["🔍 RAG Retrieval"]:::ai
            Node_Reasoning["🤔 Reasoning"]:::ai
        end
    end

    %% --- LAYER 3: CPAP ---
    subgraph CPAP ["Layer 3: CPAP Engine"]
        direction TB
        Node_Library["📚 Registry"]:::storage
        
        subgraph LAYERS ["4-Layer Compilation"]
            L1[Domain] --> L2[Unit] --> L3[Task] --> L4[Opt]
        end
        
        Node_Compiler["⚙️ Compiler"]:::creative
        Node_Adapter["🔌 Adapters"]:::creative
    end

    %% --- LAYER 4: OUTPUT ---
    subgraph OUT ["Layer 4: Touchpoints"]
        UI_Dash["💻 Dashboard"]:::output
        UI_Mail["📧 Auto-Reports"]:::output
        UI_Biz_Sol["💼 Business Solutions"]:::output
        Node_Feedback["✍️ Feedback Loop"]:::flow
    end

    %% CONNECTIONS (Simplified for Clarity)
    Input_User --> Node_Resolver
    Node_Resolver --> Node_Forwarder
    Node_Forwarder -- No --> Node_Fetcher_Meta & Node_Fetcher_Review
    Input_User --> Node_Social_Plan --> Node_Social_Fetch

    Node_Fetcher_Meta & Node_Fetcher_Review & Node_Social_Fetch --> Node_Ingest
    Node_Ingest --> Node_Miner_Extract --> Node_Miner_Evidence
    Node_Miner_Evidence --> Node_Janitor_Match <--> Node_Janitor_Dict
    Node_Janitor_Match --> Node_Stats_Agg --> Node_Stats_Weight --> Node_Stats_Impact
    Node_Stats_Impact --> Node_RAG --> Node_Reasoning

    Node_Reasoning ==>|Insight| Node_Compiler
    Node_Library --> L1
    L4 --> Node_Compiler --> UI_Biz_Sol
    Node_Reasoning --> UI_Dash & UI_Mail

    UI_Dash --> Node_Feedback -.-> Node_Janitor_Dict
```

---

## ⚙️ III. THE ENGINEER VIEW (MICRO DETAILS)
*Góc nhìn dành cho Dev Team: Logic xử lý cụ thể.*

### 1. The Intelligence Pipeline
```mermaid
graph TD
    classDef raw fill:#e0e0e0,stroke:#616161,stroke-width:1px,color:#000;
    classDef ai fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    
    Raw["📥 Raw Data"]:::raw --> Extract["🧠 Gemini Extract"]:::ai
    Extract --> Evidence["🔗 Quote Linking"]:::raw
    Evidence --> Fuzzy["🧹 Fuzzy Match"]:::ai
    Fuzzy <--> Dict["📚 Dictionary"]:::raw
    Fuzzy --> Bayes["⚖️ Bayesian Score"]:::ai
    Bayes --> Impact["📉 Impact Score"]:::ai
```

### 2. The CPAP Compilation Flow
```mermaid
graph LR
    classDef ctx fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;
    
    Req["Request"] --> L1["Company Rules"]:::ctx
    L1 --> L2["Dept Rules"]:::ctx
    L2 --> L3["Task Template"]:::ctx
    L3 --> L4["Keyword Optimization"]:::ctx
    L4 --> Final["📝 Final Prompt"]
```

---

## 📝 Giải thích các khái niệm mới (Strategic Concepts)

1.  **Unified Acquisition:** Không chỉ là scraper, mà là bộ định tuyến thông minh (Routing) để lấy đúng dữ liệu với chi phí thấp nhất.
2.  **The Bridge (Detective -> CPAP):** Điểm chuyển đổi giá trị cốt lõi - biến Insight thụ động thành Hành động chủ động (Automation).
3.  **Feedback Loop:** Cơ chế tự học giúp hệ thống ngày càng chính xác theo domain của doanh nghiệp.