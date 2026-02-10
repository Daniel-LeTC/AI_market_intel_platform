# AI ECOSYSTEM MAP (AS-IS & TO-BE)

## 🎯 Tầm nhìn Chiến lược
Bản đồ này mô tả toàn bộ hệ sinh thái công nghệ AI của Business Unit, kết nối việc thu thập dữ liệu (Acquisition), phân tích (Intelligence) và sáng tạo nội dung (Creative Generation).

---

## 🗺️ The Grand Map (Mermaid)

```mermaid
graph TD
    %% --- STYLES ---
    classDef acquisition fill:#e3f2fd,stroke:#2196f3,stroke-width:2px;
    classDef intelligence fill:#fff3e0,stroke:#ff9800,stroke-width:2px;
    classDef creative fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px;
    classDef output fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
    classDef hidden fill:#eceff1,stroke:#607d8b,stroke-width:2px,stroke-dasharray: 5 5;

    %% --- LAYER 1: ACQUISITION & DISCOVERY ---
    subgraph ACQUISITION ["Layer 1: Data Acquisition & Discovery"]
        direction TB
        Node_Parent_Hunter["🔎 Parent/Variation Hunter"]:::acquisition
        Node_Metadata_Deep["📦 Deep Metadata Scraper"]:::acquisition
        Node_Review_Deep["📝 Deep Review Scraper"]:::acquisition
        Node_TikTok_Feed["🎵 TikTok Feed Scraper"]:::acquisition
        Node_TikTok_Comment["💬 TikTok Comment Scraper"]:::acquisition
        Node_Meta_Ads["📢 Meta Ads Library"]:::acquisition
        Node_Social_Pricing["💰 Cost Estimator"]:::hidden
    end

    %% --- LAYER 2: INTELLIGENCE Core ---
    subgraph INTELLIGENCE ["Layer 2: AI Intelligence Core"]
        direction TB
        Node_Ingest["📥 Data Ingest"]:::intelligence
        Node_Miner["⛏️ Tag Miner (Gemini)"]:::intelligence
        Node_Janitor["🧹 Janitor (Normalization)"]:::intelligence
        Node_Stats["📊 Stats Engine (Sentiment/Impact)"]:::intelligence
        Node_Detective["🕵️ Detective Agent (RAG)"]:::intelligence
    end

    %% --- LAYER 3: CREATIVE (CPAP ENGINE) ---
    subgraph CREATIVE ["Layer 3: Creative Automation (CPAP)"]
        direction TB
        Node_Registry["📚 Asset Registry (Rules/Templates)"]:::creative
        Node_Compiler["⚙️ Prompt Compiler (4-Layer)"]:::creative
        Node_Domain_Adapter["🔌 Domain Adapters (HR/Ecom)"]:::creative
    end

    %% --- LAYER 4: OUTPUT & INTERACTION ---
    subgraph OUTPUT ["Layer 4: User Touchpoints"]
        direction TB
        UI_Dashboard["💻 Market Intel Dashboard"]:::output
        UI_Mailer["📧 Weekly Auto-Mailer"]:::output
        UI_Prompt_Gen["📝 Prompt Generator Tool"]:::output
    end

    %% --- CONNECTIONS ---
    %% Acquisition Flow
    Node_Parent_Hunter -->|Discovery List| Node_Metadata_Deep
    Node_Parent_Hunter -->|Discovery List| Node_Review_Deep
    
    %% Data Flow to Core
    Node_Metadata_Deep --> Node_Ingest
    Node_Review_Deep --> Node_Ingest
    Node_TikTok_Feed --> Node_Ingest
    Node_TikTok_Comment --> Node_Ingest
    Node_Meta_Ads --> Node_Ingest

    %% Intelligence Flow
    Node_Ingest --> Node_Miner
    Node_Miner --> Node_Janitor
    Node_Janitor --> Node_Stats
    Node_Stats --> Node_Detective
    Node_Stats --> UI_Dashboard
    Node_Detective --> UI_Mailer
    Node_Detective --> UI_Dashboard

    %% Creative Flow
    Node_Registry --> Node_Compiler
    Node_Domain_Adapter --> Node_Compiler
    Node_Compiler --> UI_Prompt_Gen

    %% Cross-Pollination (Future)
    Node_Detective -.->|Insight Context| Node_Compiler
    Node_Social_Pricing -.->|Budget Check| Node_TikTok_Feed
```

---

## 🧩 Node Dictionary (Từ điển Chức năng)

### 1. Acquisition Nodes
| ID | Tên Node | Trạng thái | Input | Output | Chức năng chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Node_Parent_Hunter** | Parent/Variation Hunter | ✅ Active | Seed ASIN | Variation Map | Phân tích quan hệ cha con, gom nhóm ASIN. |
| **Node_Metadata_Deep** | Deep Metadata Scraper | ✅ Active | ASIN List | Product DNA | Lấy Specs, Material, Brand, Listing info. |
| **Node_Review_Deep** | Deep Review Scraper | ✅ Active | ASIN List | Raw Reviews | Chiến thuật 5-star split thu thập feedback thô. |
| **Node_TikTok_Feed** | TikTok Feed Scraper | 💤 Sleeping | Keywords | Video Metrics | Cào video xu hướng theo Hashtag. |
| **Node_Meta_Ads** | Meta Ads Library | 💤 Sleeping | Keywords | Ads Info | Soi thư viện quảng cáo đối thủ. |

### 2. Intelligence Nodes
| ID | Tên Node | Trạng thái | Input | Output | Chức năng chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Node_Miner** | Tag Miner | ✅ Active | Raw Text | Raw Tags | Dùng Gemini trích xuất Aspect/Sentiment thô. |
| **Node_Janitor** | Data Janitor | ✅ Active | Raw Tags | Clean Aspects | Quy chuẩn hóa các thuật ngữ về tên gọi chuẩn. |
| **Node_Stats** | Stats Engine | ✅ Active | Clean Data | Impact Scores | Tính trọng số Sentiment dựa trên Rating thật. |
| **Node_Detective** | Detective Agent | ✅ Active | Stats/Query | Insights | Agentic AI tóm tắt Pain-points và cơ hội. |

### 3. Creative Nodes (CPAP)
| ID | Tên Node | Trạng thái | Input | Output | Chức năng chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Node_Compiler** | Prompt Compiler | ✅ Active | Request | Prompt | Biên dịch Task thành Prompt tối ưu 4 lớp. |
| **Node_Registry** | Asset Registry | ✅ Active | Unit Name | Context | Quản lý Brand Voice, Rules cho từng Domain. |

---

## 🚀 Strategic Integration Points (Các điểm chạm chiến lược)

1.  **Insight-to-Action:** Kết nối `Node_Detective` (Insight thị trường) thẳng vào `Node_Compiler` (Creative).
2.  **Parent-driven Ingestion:** Toàn bộ pipeline bắt đầu từ `Node_Parent_Hunter` để đảm bảo dữ liệu không bị rời rạc theo biến thể đơn lẻ.
3.  **Unified AI Command Center:** Gom UI_Prompt_Gen vào chung Dashboard với Market Intel để tạo thành bộ công cụ làm việc khép kín cho User.