# AI ECOSYSTEM MAP (FULL STRATEGIC VIEW)

## 🎯 Tầm nhìn Chiến lược
Bản đồ này tổng hợp toàn bộ các Node chức năng (cả hiện tại và tương lai), thể hiện luồng dữ liệu khép kín từ **Thu thập -> Phân tích -> Sáng tạo -> Phản hồi**.

---

## 🗺️ The Map (Mermaid)

```mermaid
graph TD
    %% --- STYLES (High Contrast) ---
    classDef flow fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef ai fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef creative fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#000;
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef hidden fill:#ffffff,stroke:#607d8b,stroke-width:2px,color:#607d8b,stroke-dasharray: 5 5;

    %% --- LAYER 1: UNIFIED ACQUISITION ---
    subgraph ACQ ["Layer 1: Unified Acquisition & Routing"]
        direction TB
        Input_User[("👤 User Input (ASIN / Keywords)")]:::flow
        
        %% E-Commerce Flow
        subgraph ECOM_FLOW ["E-Commerce Workflow"]
            Node_Resolver["🔍 ASIN Resolver (Parent/Child Check)"]:::flow
            Node_Forwarder{"Is Child?"}:::flow
            Node_Competitor_Auto["🤖 Competitor Auto-Discovery (Future)"]:::hidden
            Node_Fetcher_Meta["📦 Metadata Fetcher<br/>(Specs, Material, Images, Price)"]:::flow
            Node_Fetcher_Review["📝 Review Fetcher<br/>(Text, Rating, Date, User Photos)"]:::flow
        end
        
        %% Social Flow
        subgraph SOCIAL_FLOW ["Social Workflow Engine"]
            Node_Social_Plan["📅 Social Planning (Budget/Filter)"]:::flow
            Node_Social_Fetch["📱 Social Fetcher (TikTok/Meta)"]:::flow
            Node_Social_Pricing["💰 Cost Estimator"]:::hidden
        end
    end

    %% --- LAYER 2: DEEP INTELLIGENCE (AI CORE) ---
    subgraph INTEL ["Layer 2: AI Intelligence Core"]
        direction TB
        
        %% Ingest
        Node_Ingest["📥 Universal Ingest (Blue-Green DB)"]:::storage

        %% Miner Detail
        subgraph MINER_LOGIC ["AI Miner (Extraction)"]
            Node_Miner_Extract["🧠 Aspect/Sentiment Extraction"]:::ai
            Node_Miner_Evidence["🔗 Evidence Linking (Quotes/IDs)"]:::ai
            Node_Miner_Image["👁️ Image Analysis (Future)"]:::hidden
        end

        %% Janitor Detail
        subgraph JANITOR_LOGIC ["Janitor (Standardization)"]
            Node_Janitor_Match["🧹 Vector/Fuzzy Matching"]:::ai
            Node_Janitor_Dict["📚 Canonical Dictionary"]:::storage
        end

        %% Stats Detail
        subgraph STATS_LOGIC ["Stats Engine (Processing)"]
            Node_Stats_Agg["∑ Aggregation"]:::ai
            Node_Stats_Weight["⚖️ Bayesian Smoothing<br/>(Chống bias)"]:::ai
            Node_Stats_Impact["📉 Impact Score Calculation<br/>(Volume x Severity)"]:::ai
        end

        %% Detective Detail
        subgraph DETECTIVE_LOGIC ["Detective Agent (Reasoning)"]
            Node_RAG["🔍 RAG Retrieval (Data + Context)"]:::ai
            Node_Reasoning["🤔 Strategic Reasoning"]:::ai
        end
    end

    %% --- LAYER 3: CPAP (CREATIVE & BUSINESS AUTOMATION) ---
    subgraph CPAP ["Layer 3: CPAP Engine (4-Layer Framework)"]
        direction TB
        Node_Library["📚 Prompt Library & Context Registry"]:::storage
        
        subgraph LAYERS ["4-Layer Compilation"]
            L1["L1: Domain (Company)"]:::creative
            L2["L2: Unit (Department)"]:::creative
            L3["L3: Task (Specific)"]:::creative
            L4["L4: Optimization"]:::creative
        end
        
        Node_Compiler["⚙️ Prompt Compiler"]:::creative
        Node_Adapter["🔌 Domain Adapters"]:::creative
    end

    %% --- LAYER 4: OUTPUT & FEEDBACK ---
    subgraph OUT ["Layer 4: Business Touchpoints"]
        subgraph DASHBOARD ["Interactive Dashboard"]
            UI_Heatmap["🌡️ Aspect Heatmap"]:::output
            UI_Trend["📈 Sentiment Trendline"]:::output
            UI_Gallery["🖼️ Evidence Gallery"]:::output
        end
        UI_Mail["📧 Auto-Reports"]:::output
        UI_Biz_Sol["💼 Business Solutions"]:::output
        Node_Feedback["✍️ User Feedback Form"]:::flow
    end

    %% --- CONNECTIONS ---
    %% Input Flow
    Input_User --> Node_Resolver
    Node_Resolver --> Node_Forwarder
    Node_Forwarder -- Yes --> Node_Resolver
    Node_Forwarder -- No --> Node_Fetcher_Meta
    Node_Forwarder -- No --> Node_Fetcher_Review
    Node_Resolver -.-> Node_Competitor_Auto
    Input_User --> Node_Social_Plan
    Node_Social_Plan --> Node_Social_Fetch
    Node_Social_Plan -.-> Node_Social_Pricing

    %% Ingest
    Node_Fetcher_Meta --> Node_Ingest
    Node_Fetcher_Review --> Node_Ingest
    Node_Social_Fetch --> Node_Ingest
    Node_Ingest --> Node_Miner_Extract
    Node_Ingest -.-> Node_Miner_Image

    %% AI Loop
    Node_Miner_Extract --> Node_Miner_Evidence
    Node_Miner_Evidence --> Node_Janitor_Match
    Node_Janitor_Match <--> Node_Janitor_Dict
    Node_Janitor_Match --> Node_Stats_Agg
    
    %% Stats Loop
    Node_Stats_Agg --> Node_Stats_Weight
    Node_Stats_Weight --> Node_Stats_Impact
    Node_Stats_Impact --> Node_RAG

    %% Detective Loop
    Node_RAG --> Node_Reasoning
    Node_Reasoning --> UI_Heatmap
    Node_Reasoning --> UI_Mail

    %% OUTPUTS
    Node_Stats_Impact --> UI_Heatmap
    Node_Stats_Impact --> UI_Trend
    Node_Fetcher_Review --> UI_Gallery

    %% THE BRIDGE (Detective -> CPAP)
    Node_Reasoning ==>|Strategic Insight| Node_Compiler

    %% CPAP Flow
    Node_Library --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> Node_Compiler
    Node_Adapter --> Node_Compiler
    Node_Compiler --> UI_Biz_Sol

    %% FEEDBACK LOOP
    UI_Heatmap --> Node_Feedback
    Node_Feedback -.->|Correction| Node_Janitor_Dict
    Node_Feedback -.->|Retrain| Node_Miner_Extract
```

---

## 🧩 Giải mã Bản đồ (Dành cho Stakeholder)

### 1. Unified Acquisition (Đầu vào)
*   **Resolver:** Tự động định tuyến ASIN Cha/Con, đảm bảo không sót biến thể.
*   **Fetchers:** Thu thập đầy đủ dữ liệu đa phương tiện (Ảnh, Text, Metadata).
*   **Social:** Quy trình riêng có kiểm soát ngân sách (Budget Check) trước khi cào dữ liệu đắt đỏ.

### 2. AI Intelligence (Lõi xử lý)
*   **Miner:** Tách Aspect (Khía cạnh) và Sentiment (Cảm xúc), có link ngược về bằng chứng gốc.
*   **Stats Engine:** Không dùng trung bình cộng đơn giản. Áp dụng **Bayesian Smoothing** để dữ liệu ít review không bị nhiễu, tính ra **Impact Score** (Mức độ ảnh hưởng thật sự).
*   **Janitor:** Bộ lọc thông minh, học từ Feedback của người dùng để ngày càng chuẩn xác.

### 3. CPAP (Cầu nối sáng tạo)
*   **4-Layer:** Đảm bảo mọi đầu ra (Content, Email, JD) đều tuân thủ Brand Voice và Quy định công ty.
*   **The Bridge:** Insight từ Detective (Vd: "Lỗi khóa kéo") tự động kích hoạt CPAP để tạo tài liệu xử lý (Vd: "Email xin lỗi khách hàng").

### 4. Feedback Loop (Cơ chế tự học)
*   Hệ thống không tĩnh. Khi User sửa sai trên Dashboard, thông tin đó quay ngược lại để cập nhật Từ điển (Dictionary) và Model, giúp AI ngày càng "khôn" hơn theo domain đặc thù của công ty.
