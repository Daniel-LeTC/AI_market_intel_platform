# 📊 Presentation Visuals for End-Users (Refactored)

This document contains simplified diagrams designed for stakeholder presentations. They focus on **Business Value** and **User Workflow** rather than Technical Implementation.

## 1. The Two-Track Strategy (Hai mũi nhọn tấn công)

Hệ thống được chia làm 2 phân khu độc lập để tránh nhiễu dữ liệu.

```mermaid
graph TD
    subgraph TRACK_A ["TRACK A: MARKET INTELLIGENCE (Sẵn sàng)"]
        direction TB
        A1[Quét Amazon: Metadata + Reviews]
        A2[Phân tích DNA Sản phẩm & Chấm điểm đối thủ]
    end

    subgraph TRACK_B ["TRACK B: SOCIAL SCOUT (Đang phát triển - WIP)"]
        direction TB
        B1[Quét TikTok/Meta: Video + Comments]
        B2[Bắt Trend & Theo dõi độ phủ thương hiệu]
    end

    TRACK_A --> Dash[Dashboard Phân Tích Thị Trường]
    TRACK_B --> Trend[Báo Cáo Xu Hướng Mạng Xã Hội]
```

## 2. Market Intelligence Deep Dive (Cái hộp Amazon làm gì?)

Giải thích cho User rằng chúng ta không chỉ đọc review, chúng ta "số hóa" sản phẩm bằng cách bóc tách Metadata và Reviews.

```mermaid
graph LR
    Input[ASIN] --> Hunter[Data Hunter]
    
    subgraph PROCESS ["Xử lý đa luồng"]
        direction TB
        P1["📂 DNA Extractor: Bóc tách thông số (Chất liệu, Đối tượng, Tính năng)"]
        P2["🧠 Review Miner: Đọc hiểu khen/chê từ khách hàng"]
    end

    Hunter --> P1
    Hunter --> P2
    
    P1 --> Output["Bản đồ DNA & So sánh thông số"]
    P2 --> Output2["Bản đồ nhiệt Market X-Ray"]
```

## 3. The "User Journey" (User phải làm gì?)

```mermaid
sequenceDiagram
    participant User
    participant App as Bright Scraper Tool
    participant Email

    Note over User, App: Bước 1: Thu thập dữ liệu
    User->>App: Nhập mã ASIN sản phẩm cần soi
    User->>App: Bấm "Start Analysis"
    App-->>User: "Đang chạy... hệ thống đang bóc tách DNA & Review (30p)"
    
    Note over User, App: Bước 2: Phân tích & Soi mói
    User->>App: Mở Tab "Market X-Ray"
    User->>App: 🔍 Check: Biểu đồ nhiệt có đúng thực tế không?
    
    User->>App: Mở Tab "Product Showdown"
    User->>App: 🔍 Check: So sánh đối thủ A vs B có chuẩn không?
    
    User->>App: Chat với "Detective Agent"
    User->>App: 🔍 Check: Hỏi khó nó xem nó trả lời ngáo không?
    
    Note over User, App: Bước 3: Báo cáo định kỳ
    App->>Email: Tự động gửi PDF báo cáo (Weekly R&D)
    User->>Email: 🔍 Check: Số liệu trong mail có khớp trên App không?
```

## 4. The "Feedback Checklist" (Cần User soi cái gì?)

| Module (Chức năng) | User cần kiểm tra (Feedback) | Mức độ quan trọng |
| :--- | :--- | :--- |
| **Market X-Ray** | Các cột "Aspect" (Ví dụ: Softness, Thickness) đã chuẩn chưa? Có bị trùng lặp không? | 🔥 CAO NHẤT |
| **Product Showdown** | Điểm số "Weighted Score" có phản ánh đúng chất lượng sản phẩm so với đối thủ không? | 🔥 CAO |
| **Product DNA** | Thông số kỹ thuật (Chất liệu, đối tượng) bóc tách từ Amazon có chính xác không? | ⭐ TB |
| **Detective Bot** | Khi hỏi "Tại sao thằng A bán chạy hơn?", câu trả lời có logic không hay chém gió? | ⭐ TB |