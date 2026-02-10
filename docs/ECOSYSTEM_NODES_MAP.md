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

    %% --- LAYER 1: ACQUISITION (BRIGHT SCRAPER & SOCIAL SCOUT) ---
    subgraph ACQUISITION ["Layer 1: Data Acquisition"]
        direction TB
        Node_Amz["🛒 Amazon Scraper"]:::acquisition
        Node_TikTok_Feed["🎵 TikTok Feed Scraper"]:::acquisition
        Node_TikTok_Comment["💬 TikTok Comment Scraper"]:::acquisition
        Node_Meta_Ads["📢 Meta Ads Library"]:::acquisition
        Node_Social_Pricing["💰 Cost Estimator"]:::hidden
    end

    %% --- LAYER 2: INTELLIGENCE (ANALYSIS ENGINE) ---
    subgraph INTELLIGENCE ["Layer 2: AI Intelligence Core"]
        direction TB
        Node_Ingest["📥 Data Ingest"]:::intelligence
        Node_Miner["⛏️ Tag Miner (Gemini)"]:::intelligence
        Node_Janitor["🧹 Janitor (Normalization)"]:::intelligence
        Node_Stats["📊 Stats Engine (Weighted Impact)"]:::intelligence
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
    %% Data Flow
    Node_Amz --> Node_Ingest
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
| ID | Tên Node | Trạng thái | Input | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Node_Amz** | Amazon Scraper | ✅ Active | ASIN List | Product Reviews & Metadata |
| **Node_TikTok_Feed** | TikTok Feed Scraper | 💤 Sleeping | Keywords | Video Metrics, Captions |
| **Node_TikTok_Comment** | TikTok Comment Scraper | 💤 Sleeping | Video URL | User Sentiments |
| **Node_Meta_Ads** | Meta Ads Library | 💤 Sleeping | Keywords | Competitor Ad Creatives |
| **Node_Social_Pricing** | Cost Estimator | 🚧 W.I.P | Request Volume | Estimated Cost ($) |

### 2. Intelligence Nodes
| ID | Tên Node | Trạng thái | Input | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Node_Miner** | Tag Miner | ✅ Active | Raw Text | Unstructured Tags |
| **Node_Janitor** | Data Janitor | ✅ Active | Raw Tags | Standardized Aspects |
| **Node_Stats** | Stats Engine | ✅ Active | Clean Data | Weighted Impact Scores |
| **Node_Detective** | Detective Agent | ✅ Active | Queries/Stats | Strategic Insights |

### 3. Creative Nodes (CPAP)
| ID | Tên Node | Trạng thái | Input | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Node_Compiler** | Prompt Compiler | ✅ Active | Task Request + Context | Optimized Prompt |
| **Node_Registry** | Asset Registry | ✅ Active | Unit Name | Brand Voice, Rules, Templates |

---

## 🚀 Strategic Integration Points (Các điểm chạm chiến lược)

1.  **Insight-to-Action:** Kết nối `Node_Detective` (Insight thị trường) thẳng vào `Node_Compiler` (Creative).
    *   *Ví dụ:* Detective phát hiện khách hàng ghét "khóa kéo dỏm" -> Compiler tự động tạo Prompt cho Media làm video "Test độ bền khóa kéo".
2.  **Budget Guardrail:** Kích hoạt `Node_Social_Pricing` làm Gatekeeper trước khi gọi các Node Social đắt tiền.
3.  **Unified Dashboard:** Gom UI_Prompt_Gen vào chung Dashboard với Market Intel để tạo thành **"AI Command Center"**.
