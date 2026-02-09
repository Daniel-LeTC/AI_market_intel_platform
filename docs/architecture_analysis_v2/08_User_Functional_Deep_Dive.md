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

## 2. Review Analysis: Mổ xẻ tâm lý khách hàng (AI Miner)

Hệ thống có cơ chế "Tiết kiệm tiền" (Trash Filter) và "Tự học" (RAG Shield) để đảm bảo dữ liệu sạch và rẻ.

```mermaid
graph TD
    subgraph INPUT ["1. INPUT"]
        R_Raw["Review thô từ Amazon"]
    end

    subgraph SMART_PROCESS ["2. XỬ LÝ THÔNG MINH"]
        direction TB
        Filter{"Bước 1: Lọc rác\n(Review < 10 chữ?)"}
        AutoTag["Tự động gán nhãn\n(Không tốn phí AI)"]
        AIRead["Gửi cho AI đọc hiểu\n(Dùng RAG Shield chống đẻ từ mới)"]
        
        Filter -- "Ngắn/Spam" --> AutoTag
        Filter -- "Chất lượng" --> AIRead
    end

    subgraph OUTPUT ["3. OUTPUT"]
        Xray["Bản đồ nhiệt Market X-Ray"]
    end

    R_Raw --> Filter
    AutoTag & AIRead --> Xray
```

**🔍 Giải thích cho User:**
*   **Tại sao chạy nhanh & rẻ?** Vì hệ thống không "ngu" gửi những review vô nghĩa (như "Good", "Bad") cho AI. Nó tự xử lý luôn.
*   **Tại sao từ khóa không bị loạn?** Vì mỗi khi đọc từ mới, nó luôn đối chiếu với "Từ điển chuẩn" (RAG Shield) để ép dữ liệu vào khuôn khổ, giúp biểu đồ của bạn luôn sạch sẽ.

---

## 3. Tab "Showdown": Thuật toán Weighted Score (Xử lý sai số mẫu)

Hệ thống không dùng trung bình cộng đơn giản. Chúng tôi dùng thuật toán **Ngoại suy (Extrapolation)** để khôi phục thị trường thực tế.

```mermaid
graph TD
    subgraph INPUT ["Đầu vào"]
        M1[Real Metadata: 4.8 sao / 60k Ratings]
        S1[Sample Data: 500 reviews cào về]
    end

    subgraph LOGIC ["Hộp xử lý logic (StatsEngine)"]
        direction TB
        Step1["Tính 'Mention Rate' trên mẫu cào về (ví dụ: 10% chê pin)"]
        Step2["Lấy 'Market Weight' từ biểu đồ sao Amazon (ví dụ: 80% là 5 sao)"]
        Step3["Công thức: Weighted Score = Mentions * Weight / Total"]
    end

    subgraph OUTPUT ["Kết quả"]
        Final["Real Score: Điểm số thực tế sau khi loại bỏ sai lệch mẫu"]
    end

    M1 & S1 --> LOGIC --> Final
```

**🔍 Giải thích cho User (Đúng bản chất code):**
*   "Tại sao tao cào 100 cái chê, 100 cái khen mà điểm vẫn cao?" -> Vì hệ thống biết rằng 100 cái chê đó chỉ đại diện cho 1% khách hàng (1 sao), còn 100 cái khen đại diện cho 80% khách hàng (5 sao). Hệ thống tự động nhân trọng số để ra kết quả **"Công bằng nhất"**.

---

## 4. Social Scout (Tách biệt hoàn toàn - WIP)

*Lưu ý: Đây là module Social Listening, không liên quan đến dữ liệu bán hàng Amazon.*

*   **Input:** Keyword/Hashtag trên TikTok/Meta.
*   **Processing:** Cào video, phân tích xu hướng, độ hot.
*   **Status:** **Đang hoàn thiện (WIP)**.
