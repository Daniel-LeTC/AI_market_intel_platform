# 🔬 Functional Deep Dive: Metadata & Reviews

Tài liệu này giải thích cơ chế hoạt động chi tiết của các tính năng chính. Dùng để trả lời câu hỏi: **"Cái nút này thực sự tính toán cái gì?"**.

---

## 1. Metadata Extraction: Xây dựng bản đồ DNA sản phẩm

Hệ thống không chỉ lấy giá, nó "soi" kỹ thuật để xây dựng DNA sản phẩm từ các thông tin thô trên Amazon.

```mermaid
graph TD
    subgraph INPUT ["1. INPUT (Amazon Page)"]
        Source["Bảng thông số kỹ thuật + Mô tả sản phẩm"]
    end

    subgraph PROCESSING ["2. PROCESSING (DNA Extractor)"]
        direction TB
        Step1["Quét các trường dữ liệu: Material, Brand, Style, Target Audience"]
        Step2["Chuẩn hóa dữ liệu (Ví dụ: '100% Cotton' -> 'Cotton')"]
        Step3["Gán nhãn loại sản phẩm (Category Inference)"]
    end

    subgraph OUTPUT ["3. OUTPUT (Product DNA)"]
        DNA["Hồ sơ sản phẩm hoàn chỉnh"]
    end

    Source --> Step1 --> Step2 --> Step3 --> DNA
```

**🔍 User Feedback Check:**
*   **Kiểm tra:** Vào tab *Overview*, xem phần "Product Specs". Nếu Amazon ghi là "Memory Foam" mà App ghi là "Cotton" -> **Báo lỗi dữ liệu**.

---

## 2. Review Analysis: Mổ xẻ tâm lý khách hàng (AI Review Miner)

Đây là cỗ máy đọc hiểu 5,000+ reviews để bóc tách khen/chê.

```mermaid
graph TD
    subgraph INPUT ["1. INPUT"]
        R_Raw["5,000+ Reviews thô"]
    end

    subgraph PROCESSING ["2. PROCESSING"]
        direction TB
        StepA["AI đọc từng câu và gán nhãn khía cạnh (Aspect)"]
        StepB["Chấm điểm cảm xúc (Sentiment: -1 đến +1)"]
        StepC["Lấy ví dụ thực tế (Quote) làm bằng chứng"]
    end

    subgraph OUTPUT ["3. OUTPUT"]
        Xray["Bản đồ nhiệt Market X-Ray"]
    end

    R_Raw --> StepA --> StepB --> StepC --> Xray
```

---

## 3. Tab "Showdown": Thuật toán Công bằng (Fairness Engine)

Tại sao **Amazon Rating** nói 4.8 sao, mà **Bright Scraper** lại đánh giá thấp hơn?

```mermaid
flowchart LR
    subgraph SOURCE ["Nguồn dữ liệu gốc"]
        AMZ_Rating["Amazon Rating: 4.8 sao"]
        Review_Vol["Số lượng Review: 50 cái"]
    end

    subgraph LOGIC ["Hộp xử lý logic (The Processing)"]
        direction TB
        Rule1{"Tin cậy theo số đông: Ít review -> Giảm điểm"}
        Rule2{"Kiểm chứng bằng AI: Review ảo/Spam -> Loại bỏ"}
        Calc["Tính toán lại (Weighted Calc)"]
    end

    subgraph RESULT ["Kết quả hiển thị"]
        Real_Score["Real Score: 4.2 sao"]
    end

    SOURCE --> Rule1 --> Calc
    SOURCE --> Rule2 --> Calc
    Calc --> Real_Score
```

---

## 4. Social Scout (Tách biệt hoàn toàn - WIP)

*Lưu ý: Đây là module Social Listening, không liên quan đến dữ liệu bán hàng Amazon.*

*   **Input:** Keyword/Hashtag trên TikTok/Meta.
*   **Processing:** Cào video, phân tích xu hướng, độ hot.
*   **Status:** **Đang hoàn thiện (WIP)**.