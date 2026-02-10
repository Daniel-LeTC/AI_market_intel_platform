# AI ECOSYSTEM MAP (OPTIMIZED LAYOUT)

## 🎯 Tầm nhìn Chiến lược
Bản đồ này mô tả hệ sinh thái AI tích hợp, được tối ưu hóa về mặt trình bày để đảm bảo tính rõ ràng, dễ đọc và thể hiện trọn vẹn luồng dữ liệu từ lúc thu thập đến khi tạo ra giá trị kinh doanh.

---

## 🗺️ The Map (Mermaid)

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

## 🧩 Giải mã Bản đồ (Dành cho Stakeholder)

### 1. Unified Acquisition (Lớp Thu thập)
*   **🛒 E-Commerce:** Tự động định tuyến và thu thập đa dạng dữ liệu (Thông số kỹ thuật, giá, ảnh user).
*   **📱 Social:** Luồng xử lý riêng biệt cho TikTok/Meta với cơ chế kiểm soát ngân sách.

### 2. AI Intelligence (Lớp Phân tích)
*   **⛏️ Miner:** Bóc tách khía cạnh và cảm xúc, luôn đi kèm bằng chứng (Quote) để đảm bảo tính minh bạch.
*   **🧹 Janitor:** Dọn dẹp và chuẩn hóa dữ liệu dựa trên Từ điển hệ thống (Canonical Dictionary).
*   **📊 Stats Engine:** Áp dụng toán học (Bayesian) để loại bỏ nhiễu và tính toán mức độ tác động thực tế (Net Impact).

### 3. CPAP Engine (Lớp Sáng tạo)
*   **⚙️ Compiler:** Đóng vai trò là **Node Thực thi**, biến các Insight thị trường thành các bộ Prompt chất lượng cao phục vụ toàn bộ doanh nghiệp.

### 4. Touchpoints & Loop (Lớp Đầu ra & Phản hồi)
*   **💻 Dashboard:** Cung cấp Heatmap, xu hướng và thư viện bằng chứng trực quan.
*   **✍️ Feedback:** Cho phép người dùng trực tiếp sửa sai cho AI, tạo vòng lặp tự học cho hệ thống.