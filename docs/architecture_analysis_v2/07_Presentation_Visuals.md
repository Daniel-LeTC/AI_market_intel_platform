# 📊 Presentation Visuals for End-Users

This document contains simplified diagrams designed for stakeholder presentations. They focus on **Business Value** and **User Workflow** rather than Technical Implementation.

## 1. The "Big Picture" (Hệ thống làm gì?)

Dùng cái này để giải thích tổng quan các khối chức năng của App.

```mermaid
graph LR
    subgraph INPUT ["1. INPUT (Đầu vào)"]
        A[User nhập ASIN]
        B[Link TikTok/Facebook]
    end

    subgraph BLACKBOX ["2. THE MAGIC BOX (Xử lý)"]
        direction TB
        Hunter[("🤖 Data Hunter
(Tự động đi thu thập review, giá, thông số)")]
        Cleaner[("🧹 Data Cleaner
(Lọc rác, chuẩn hóa từ đồng nghĩa)")]
        Brain[("🧠 AI Analyst
(Đọc hiểu từng review, phân tích khen chê)")]
        
        Hunter --> Cleaner --> Brain
    end

    subgraph OUTPUT ["3. OUTPUT (Kết quả)"]
        direction TB
        Dash[("📊 Dashboard 4 Chiều
(X-Ray, Showdown, DNA, Strategy)")]
        Chat[("💬 Detective Bot
(Hỏi đáp chiến lược 1-1)")]
        Report[("📧 Weekly Email
(Báo cáo tự động vào T2 hàng tuần)")]
    end

    INPUT --> BLACKBOX --> OUTPUT
```

## 2. The "User Journey" (User phải làm gì?)

Dùng cái này để hướng dẫn User cách test và luồng đi từ A-Z.

```mermaid
sequenceDiagram
    participant User
    participant App as Bright Scraper Tool
    participant Email

    Note over User, App: Bước 1: Thu thập dữ liệu
    User->>App: Nhập mã ASIN sản phẩm cần soi
    User->>App: Bấm "Start Analysis"
    App-->>User: "Đang chạy... đi uống cafe đi bro (30p)"
    
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

## 3. The "Feedback Checklist" (Cần User soi cái gì?)

Đưa cái bảng này cho User bắt họ tick vào từng mục.

| Module (Chức năng) | User cần kiểm tra (Feedback) | Mức độ quan trọng |
| :--- | :--- | :--- |
| **Market X-Ray** | Các cột "Aspect" (Ví dụ: Softness, Thickness) đã chuẩn chưa? Có bị trùng lặp không? | 🔥 CAO NHẤT |
| **Product Showdown** | Điểm số "Weighted Score" có phản ánh đúng chất lượng sản phẩm so với đối thủ không? | 🔥 CAO |
| **Detective Bot** | Khi hỏi "Tại sao thằng A bán chạy hơn?", câu trả lời có logic không hay chém gió? | ⭐ TB |
| **Data Quality** | Thông tin cơ bản (Giá, Title, Hình ảnh) có bị sai lệch so với Amazon/TikTok không? | ⭐ TB |
