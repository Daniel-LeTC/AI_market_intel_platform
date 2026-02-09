# 🔬 Functional Deep Dive: Under the Hood

Tài liệu này giải thích cơ chế hoạt động chi tiết của các tính năng chính. Dùng để trả lời câu hỏi: **"Cái nút này thực sự tính toán cái gì?"**.

---

## 1. Nút "Start Analysis": Cỗ máy đọc hiểu tự động

Khi bạn nhập mã sản phẩm (ASIN) và bấm nút Start, hệ thống kích hoạt 3 "Công nhân ảo" làm việc tuần tự.

```mermaid
graph TD
    subgraph INPUT ["1. INPUT (Bạn cung cấp)"]
        ASIN["Mã sản phẩm (ASIN)"]
    end

    subgraph WORKER_1 ["Giai đoạn 1: Người đi chợ ảo (Collector)"]
        style WORKER_1 fill:#e3f2fd,stroke:#2196f3
        Step1A[("Truy cập trang sản phẩm")]
        Step1B["Quét toàn bộ: Giá, Ảnh, Mô tả"]
        Step1C["Tải toàn bộ 5,000+ Reviews mới nhất"]
        Step1D{"Lọc rác sơ bộ"}
        
        Step1A --> Step1B --> Step1C --> Step1D
        Step1D -- "Loại bỏ review ảo/spam" --> CleanRaw[Dữ liệu thô sạch]
    end

    subgraph WORKER_2 ["Giai đoạn 2: Người đọc thuê (AI Reader)"]
        style WORKER_2 fill:#fff3e0,stroke:#ff9800
        Step2A["Đọc từng câu trong 5,000 reviews"]
        Step2B{"Phân tách ý (Topic Detection)"}
        Step2C{"Chấm điểm cảm xúc (Sentiment)"}
        
        CleanRaw --> Step2A --> Step2B
        Step2B -- "Ví dụ: 'Pin' + 'Yếu'" --> Step2C
        Step2C -- "Điểm: Tiêu cực (-1)" --> TagDB[Dữ liệu phân mảnh]
    end

    subgraph WORKER_3 ["Giai đoạn 3: Thủ thư (Organizer)"]
        style WORKER_3 fill:#e8f5e9,stroke:#4caf50
        Step3A["Gom nhóm từ đồng nghĩa"]
        Step3B["Tính toán tần suất lặp lại"]
        
        TagDB --> Step3A
        Step3A -- "Gom 'Mềm', 'Mịn', 'Êm' -> Softness" --> Step3B
        Step3B --> FinalData[Insight hoàn chỉnh]
    end

    INPUT --> WORKER_1 --> WORKER_2 --> WORKER_3
```

**🔍 User Feedback Check:**
*   **Kiểm tra GĐ 3:** Vào tab *X-Ray*, xem các nhóm từ khóa (Aspects) đã được gom chuẩn chưa? Có bị tách lẻ tẻ (ví dụ: "Color" và "Colour" vẫn là 2 dòng) không?

---

## 2. Tab "Showdown": Thuật toán Công bằng (Fairness Engine)

Tại sao **Amazon Rating** nói 4.8 sao, mà **Bright Scraper** lại đánh giá thấp hơn? Đây là logic "Vạch trần sự thật".

```mermaid
flowchart LR
    subgraph SOURCE ["Nguồn dữ liệu gốc"]
        AMZ_Rating["Amazon Rating: 4.8 sao"]
        Review_Vol["Số lượng Review: 50 cái"]
    end

    subgraph LOGIC ["Hộp xử lý logic (The Processing)"]
        direction TB
        Rule1{"Quy tắc 1: Tin cậy theo số đông"}
        Rule2{"Quy tắc 2: Kiểm chứng bằng AI"}
        Calc["Tính toán lại (Weighted Calc)"]

        AMZ_Rating --> Rule1
        Review_Vol --> Rule1
        Rule1 -- "Ít review -> Giảm độ tin cậy" --> Calc
        
        AMZ_Rating --> Rule2
        Rule2 -- "AI đọc thấy nhiều chê bai ẩn" --> Calc
    end

    subgraph RESULT ["Kết quả hiển thị"]
        Real_Score["Real Score: 4.2 sao"]
        Advice["Lời khuyên: Chưa đủ uy tín"]
    end

    SOURCE --> LOGIC --> RESULT
```

**🔍 User Feedback Check:**
*   **Kiểm tra Logic:** Tìm một sản phẩm có Rating cao (5 sao) nhưng ít review (dưới 20 cái). Hệ thống có tự động "kéo" điểm xuống để cảnh báo rủi ro không? Nếu nó vẫn hiện 5 sao tuyệt đối -> **Báo lỗi ngay**.

---

## 3. "Detective Agent": Cơ chế Chống bịa đặt (Anti-Hallucination)

Làm sao để đảm bảo con AI không "chém gió" số liệu?

```mermaid
sequenceDiagram
    participant User
    participant Guard as "Người gác cổng (Context Guard)"
    participant Library as "Kho dữ liệu (Database)"
    participant Brain as "Bộ não AI"

    User->>Guard: Hỏi: "Tại sao sản phẩm A bị chê nhiều?"
    
    Note over Guard: Bước 1: Giới hạn phạm vi
    Guard->>Guard: Xác định User đang xem sản phẩm nào (Context Locking)
    
    Note over Guard, Library: Bước 2: Lấy bằng chứng
    Guard->>Library: Trích xuất 50 reviews tiêu cực nhất của A
    Library-->>Guard: Trả về dữ liệu thô (Facts)
    
    Note over Guard, Brain: Bước 3: Phân tích dựa trên bằng chứng
    Guard->>Brain: Gửi câu hỏi + Dữ liệu thô kèm theo
    Brain->>Brain: Tổng hợp câu trả lời CHỈ TỪ dữ liệu được gửi
    
    Brain-->>User: Trả lời kèm trích dẫn ("Khách hàng phàn nàn về pin...")
```
