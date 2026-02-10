# AI ECOSYSTEM MAP (STRATEGIC ARCHITECTURE)

## 🎯 Tầm nhìn Chiến lược
Bản đồ này mô tả hệ sinh thái AI tích hợp: Từ **Thu thập dữ liệu thị trường** đến **Phân tích thông minh** và cuối cùng là **Tự động hóa sáng tạo (CPAP)**.

---

## 🗺️ The Strategic Map (Mermaid)

```mermaid
graph TD
    %% --- STYLES (Optimized Contrast) ---
    classDef acquisition fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000;
    classDef intelligence fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000;
    classDef creative fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#000;
    classDef output fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000;
    classDef hidden fill:#cfd8dc,stroke:#455a64,stroke-width:2px,color:#000,stroke-dasharray: 5 5;

    %% --- LAYER 1: ACQUISITION & DISCOVERY ---
    subgraph ACQUISITION ["Layer 1: Data Acquisition & Discovery"]
        direction TB
        Node_Parent_Hunter["🔎 Parent/Variation Hunter"]:::acquisition
        Node_Metadata_Deep["📦 Deep Metadata Scraper"]:::acquisition
        Node_Review_Deep["📝 Deep Review Scraper"]:::acquisition
        Node_Social_Nodes["📱 Social Scrapers (TT/Meta)"]:::hidden
    end

    %% --- LAYER 2: INTELLIGENCE CORE ---
    subgraph INTELLIGENCE ["Layer 2: AI Intelligence Core"]
        direction TB
        Node_Miner["⛏️ Tag Miner (Gemini)"]:::intelligence
        Node_Janitor["🧹 Janitor (Normalization)"]:::intelligence
        Node_Stats["📊 Stats Engine (Sentiment)"]:::intelligence
        Node_Detective["🕵️ Detective Agent (RAG)"]:::intelligence
    end

    %% --- LAYER 3: CREATIVE BRIDGE (CPAP ENGINE) ---
    subgraph CREATIVE ["Layer 3: Creative Automation (CPAP)"]
        direction TB
        Node_Registry["📚 Asset Registry (Context)"]:::creative
        Node_Compiler["⚙️ Prompt Compiler (Execution)"]:::creative
        Node_Adapter["🔌 Domain Adapters"]:::creative
    end

    %% --- LAYER 4: USER OUTPUT ---
    subgraph OUTPUT ["Layer 4: User Touchpoints"]
        direction TB
        UI_Dashboard["💻 Market Intel Dashboard"]:::output
        UI_Mailer["📧 Weekly Auto-Mailer"]:::output
        UI_Creative_App["📝 AI Creative Studio"]:::output
    end

    %% --- THE STRATEGIC FLOW ---
    %% Step 1: Discovery
    Node_Parent_Hunter -->|ASIN Map| Node_Metadata_Deep
    Node_Parent_Hunter -->|ASIN Map| Node_Review_Deep
    
    %% Step 2: Analysis Pipeline
    Node_Metadata_Deep --> Node_Miner
    Node_Review_Deep --> Node_Miner
    Node_Miner --> Node_Janitor
    Node_Janitor --> Node_Stats
    Node_Stats --> Node_Detective

    %% Step 3: THE BRIDGE (Insight-to-Action)
    %% Detective nạp Insight làm Input cho Compiler để đẻ ra Prompt thực thi
    Node_Detective ==>|Market Insights| Node_Compiler
    Node_Registry --> Node_Compiler
    Node_Adapter --> Node_Compiler

    %% Step 4: Final Delivery
    Node_Detective --> UI_Dashboard
    Node_Detective --> UI_Mailer
    Node_Compiler --> UI_Creative_App
```

---

## 🧩 Node Dictionary (Từ điển Chức năng)

### 1. Acquisition Nodes
| ID | Tên Node | Trạng thái | Chức năng chính |
| :--- | :--- | :--- | :--- |
| **Node_Parent_Hunter** | Parent Hunter | ✅ Active | Phân tích quan hệ cha con, quy hoạch thị trường. |
| **Node_Metadata_Deep** | Deep Metadata | ✅ Active | Lấy DNA sản phẩm (Specs, Brand, Listing). |
| **Node_Review_Deep** | Review Scraper | ✅ Active | Thu thập voice of customer qua 5-star split. |
| **Node_Social_Nodes** | Social Scrapers | 💤 Sleeping | Cào TikTok/Meta (Đang chờ budget & workflow). |

### 2. Intelligence Core
| ID | Tên Node | Trạng thái | Chức năng chính |
| :--- | :--- | :--- | :--- |
| **Node_Miner** | Tag Miner | ✅ Active | Dùng Gemini trích xuất Aspect/Sentiment thô. |
| **Node_Janitor** | Data Janitor | ✅ Active | Quy chuẩn hóa dữ liệu về ngôn ngữ chung. |
| **Node_Stats** | Stats Engine | ✅ Active | Tính trọng số Impact dựa trên Rating dân số thực. |
| **Node_Detective** | Detective Agent | ✅ Active | RAG Agent cung cấp insight chiến lược. |

### 3. Creative Bridge (CPAP)
| ID | Tên Node | Trạng thái | Chức năng chính |
| :--- | :--- | :--- | :--- |
| **Node_Compiler** | Prompt Compiler | ✅ Active | **Node Chuyển Tiếp**: Biến Insight thành Prompt hành động. |
| **Node_Registry** | Asset Registry | ✅ Active | Quản lý Context (Brand Voice, Rules) cho AI. |
| **Node_Adapter** | Domain Adapter | ✅ Active | Tùy biến logic Prompt cho từng phòng ban (HR, Mkt). |

---

## 🚀 Strategic Integration: Insight-to-Action
Điểm nhấn lớn nhất của hệ thống là mũi tên **`Node_Detective ==> Node_Compiler`**. 
- Không dừng lại ở việc báo cáo "Khách hàng chê gì".
- Hệ thống tự động chuyển context đó sang CPAP để tạo ra các Prompt thực thi (ví dụ: Viết lại Listing sửa lỗi, Tạo kịch bản video xử lý khủng hoảng truyền thông).
