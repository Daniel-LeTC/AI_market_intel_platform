# AI ECOSYSTEM MAP (MODULAR STRATEGY)

## 🎯 Tầm nhìn Chiến lược
Tài liệu này cung cấp hai góc nhìn về hệ sinh thái AI:
1.  **Macro View:** Bức tranh tổng thể về luồng giá trị (Value Stream).
2.  **Micro View:** Chi tiết kỹ thuật của từng cỗ máy (Engine) bên trong.

---

## 🌍 I. MACRO VIEW: THE BIG PICTURE
*Góc nhìn dành cho Management: Luồng đi từ Dữ liệu thô đến Giải pháp kinh doanh.*

```mermaid
graph LR
    %% STYLES
    classDef blue fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef orange fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef purple fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;
    classDef green fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;

    %% NODES
    User[("👤 User / Market")]:::blue
    
    subgraph ACQ ["LAYER 1: ACQUISITION"]
        Ecom["🛒 E-Commerce Engine"]:::blue
        Social["📱 Social Engine"]:::blue
    end
    
    subgraph INTEL ["LAYER 2: INTELLIGENCE CORE"]
        DB["📥 Universal DB"]:::orange
        Processor["🧠 AI Processor<br/>(Miner + Janitor + Stats)"]:::orange
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

    %% FLOW
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

## ⚙️ II. MICRO VIEW: DEEP DIVE INTO ENGINES
*Góc nhìn dành cho Technical/Product Team: Logic xử lý chi tiết.*

### 1. The Intelligence Engine (Lõi Phân tích)
*Quy trình biến dữ liệu thô thành chỉ số có ý nghĩa.*

```mermaid
graph TD
    classDef raw fill:#e0e0e0,stroke:#616161,stroke-width:1px,color:#000;
    classDef ai fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000;
    classDef logic fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000;

    Input["📥 Raw Data (Review/Text)"]:::raw
    
    subgraph MINER ["Phase 1: Mining"]
        direction TB
        Extract["🧠 Gemini Extraction"]:::ai
        Evidence["🔗 Link Evidence/Quote"]:::logic
    end
    
    subgraph JANITOR ["Phase 2: Cleaning"]
        direction TB
        Dict["📚 Canonical Dictionary"]:::raw
        Match["🧹 Fuzzy/Vector Match"]:::logic
    end
    
    subgraph STATS ["Phase 3: Scoring"]
        direction TB
        Agg["∑ Aggregation"]:::logic
        Bayes["⚖️ Bayesian Smoothing"]:::logic
        Impact["📉 Net Impact Score"]:::ai
    end

    Input --> Extract
    Extract --> Evidence
    Evidence --> Match
    Match <--> Dict
    Match --> Agg
    Agg --> Bayes
    Bayes --> Impact
```

### 2. The Acquisition Engine (Bộ Thu thập)
*Cơ chế định tuyến thông minh để lấy đúng dữ liệu.*

```mermaid
graph TD
    classDef flow fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef ext fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;

    User[("👤 User Input")]:::flow
    Resolver["🔍 ASIN Resolver"]:::flow
    Check{"Is Child?"}:::flow
    
    subgraph FETCHERS
        Meta["📦 Metadata Fetcher<br/>(Specs/Images)"]:::ext
        Rev["📝 Review Fetcher<br/>(5-Star Split)"]:::ext
    end
    
    Ingest["📥 DB Ingest"]:::flow

    User --> Resolver
    Resolver --> Check
    Check -- Yes --> Resolver
    Check -- No --> Meta
    Check -- No --> Rev
    Meta --> Ingest
    Rev --> Ingest
```

### 3. The CPAP Bridge (Cầu nối Sáng tạo)
*Biến Insight thành Hành động.*

```mermaid
graph LR
    classDef ctx fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef eng fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;

    Insight["🕵️ Detective Insight"]:::ctx
    Lib["📚 Prompt Library"]:::ctx
    Registry["®️ Brand Context"]:::ctx
    
    subgraph COMPILER ["⚙️ 4-Layer Compiler"]
        direction TB
        L1[Domain] --> L2[Unit]
        L2 --> L3[Task]
        L3 --> L4[Opt]
    end
    
    Output["📝 Final Prompt / Content"]:::eng

    Insight --> COMPILER
    Lib --> COMPILER
    Registry --> COMPILER
    COMPILER --> Output
```

---

## 📝 Ghi chú Kỹ thuật
*   **Macro Map:** Dùng để trình bày chiến lược, roadmap tổng quan cho BOD.
*   **Micro Maps:** Dùng để thảo luận chi tiết quy trình, fix bug, tối ưu hóa với team R&D và Marketing.
