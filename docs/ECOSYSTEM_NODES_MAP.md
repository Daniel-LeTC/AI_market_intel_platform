# AI ECOSYSTEM MAP (DETAILED DEEP DIVE)

## 🎯 Tầm nhìn Chiến lược
Bản đồ này mô tả chi tiết luồng dữ liệu và logic xử lý của hệ sinh thái AI, từ khâu tiếp nhận yêu cầu (ASIN/Social) đến việc phân tích sâu (Miner/Stats/Detective) và cuối cùng là tự động hóa tác vụ doanh nghiệp (CPAP).

---

## 🗺️ The Detailed Ecosystem Map (Mermaid)

```mermaid
graph TD
    %% --- STYLES (High Contrast) ---
    classDef flow fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef ai fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef creative fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#000;
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;

    %% --- LAYER 1: UNIFIED INPUT & DISCOVERY ---
    subgraph ACQ ["Layer 1: Unified Acquisition & Routing"]
        direction TB
        Input_User[("👤 User Input (ASIN / Keywords)")]:::flow
        
        %% E-Commerce Flow
        subgraph ECOM_FLOW ["E-Commerce Workflow"]
            Node_Resolver["🔍 ASIN Resolver (Parent/Child Check)"]:::flow
            Node_Forwarder{"Is Child?"}:::flow
            Node_Fetcher["📦 Metadata & Review Fetcher"]:::flow
        end
        
        %% Social Flow
        subgraph SOCIAL_FLOW ["Social Workflow Engine"]
            Node_Social_Plan["📅 Social Planning (Budget/Filter)"]:::flow
            Node_Social_Fetch["📱 Social Fetcher (TikTok/Meta)"]:::flow
        end
    end

    %% --- LAYER 2: DEEP INTELLIGENCE (AI CORE) ---
    subgraph INTEL ["Layer 2: AI Intelligence Core"]
        direction TB
        
        %% Ingest
        Node_Ingest["📥 Universal Ingest"]:::storage

        %% Miner Detail
        subgraph MINER_LOGIC ["AI Miner (Extraction)"]
            Node_Miner_Extract["🧠 Aspect/Sentiment Extraction"]:::ai
            Node_Miner_Evidence["🔗 Evidence Linking (Quotes/IDs)"]:::ai
        end

        %% Janitor Detail
        subgraph JANITOR_LOGIC ["Janitor (Standardization)"]
            Node_Janitor_Match["🧹 Vector/Fuzzy Matching"]:::ai
            Node_Janitor_Dict["📚 Canonical Dictionary"]:::storage
        end

        %% Stats Detail
        subgraph STATS_LOGIC ["Stats Engine (Processing)"]
            Node_Stats_Agg["∑ Aggregation"]:::ai
            Node_Stats_Weight["⚖️ Weighted Scoring (Bayesian/Rating Dist)"]:::ai
            Node_Stats_Impact["📉 Impact Score Calculation"]:::ai
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
    end

    %% --- LAYER 4: OUTPUT ---
    subgraph OUT ["Layer 4: Business Touchpoints"]
        UI_Dash["💻 Market Dashboard"]:::output
        UI_Mail["📧 Auto-Reports"]:::output
        UI_Biz_Sol["💼 Business Solutions (HR/Mkt/Sales)"]:::output
    end

    %% --- CONNECTIONS ---
    %% Input Flow
    Input_User --> Node_Resolver
    Node_Resolver --> Node_Forwarder
    Node_Forwarder -- Yes --> Node_Resolver
    Node_Forwarder -- No --> Node_Fetcher
    Input_User --> Node_Social_Plan
    Node_Social_Plan --> Node_Social_Fetch

    %% Ingest
    Node_Fetcher --> Node_Ingest
    Node_Social_Fetch --> Node_Ingest
    Node_Ingest --> Node_Miner_Extract

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
    Node_Reasoning --> UI_Dash
    Node_Reasoning --> UI_Mail

    %% THE BRIDGE (Detective -> CPAP)
    Node_Reasoning ==>|Strategic Insight| Node_Compiler

    %% CPAP Flow
    Node_Library --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> Node_Compiler
    Node_Compiler --> UI_Biz_Sol
```

---

## 🧩 Deep Dive Logic (Giải thích luồng)

### 1. Unified Acquisition (Không chỉ là Scraper)
- **E-Commerce:** Không cào mù quáng. Hệ thống có **ASIN Resolver** thông minh để check quan hệ Cha/Con. Nếu User đưa ASIN Con, hệ thống tự forward về Cha để lấy trọn bộ biến thể.
- **Social:** Có **Workflow Engine** riêng để lập kế hoạch (Planning), lọc Keyword và kiểm soát ngân sách trước khi cào (tránh tốn tiền vô ích).

### 2. AI Intelligence (Hộp đen được mở nắp)
- **Miner:** Không chỉ lấy text. Nó tách thành 2 bước: Trích xuất ý định (Extraction) và Link ngược lại bằng chứng (Evidence/Quote) để User kiểm chứng.
- **Janitor:** Sử dụng **Canonical Dictionary** kết hợp Matching thông minh để dọn dẹp data rác.
- **Stats Engine:** Logic tính toán 3 bước: Gom nhóm (Agg) -> Cân bằng trọng số (Weighted Scoring dựa trên Rating thật) -> Tính điểm tác động (Impact Score).
- **Detective:** Agentic AI sử dụng **RAG** để đọc hiểu data đã tính toán, không "chém gió".

### 3. CPAP (Hơn cả Media)
- **4-Layer Framework:** Domain -> Unit -> Task -> Optimization. Đảm bảo output nhất quán cho TOÀN BỘ doanh nghiệp (HR, Sales, Mkt...), không chỉ Media.
- **Library & Registry:** Kho chứa tri thức và quy luật của công ty.
- **Output:** Business Solutions (Giải pháp kinh doanh) đa dạng: JD tuyển dụng, Email sale, Kịch bản video, Listing...

### 4. The Bridge (Điểm chuyển giao chiến lược)
- **Detective ==> CPAP:** Mũi tên quan trọng nhất. Insight từ dữ liệu (ví dụ: "Khách chê giá đắt") tự động trở thành Input cho CPAP để tạo ra Content xử lý (ví dụ: "Viết email giải trình giá trị sản phẩm").