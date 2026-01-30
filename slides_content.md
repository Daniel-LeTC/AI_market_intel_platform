# PRODUCT INTELLIGENCE PLATFORM (PIP)
*Hệ thống phân tích Review & Thị trường Amazon*

---

## SLIDE 1: GIỚI THIỆU
- **Công cụ:** Product Intelligence Platform (PIP).
- **Mục tiêu:** Cung cấp dữ liệu review đã qua xử lý từ Amazon để hỗ trợ nghiên cứu sản phẩm & phản ứng thị trường.
- **Đối tượng sử dụng:** Bộ phận R&D, Product Development.

---

## SLIDE 2: BỐI CẢNH & THÁCH THỨC
- **Khối lượng dữ liệu lớn:** Việc đọc và tổng hợp thủ công hàng trăm review cho từng ASIN tốn rất nhiều thời gian nhân sự.
- **Góc nhìn phân tán:** Khó tổng hợp được bức tranh toàn cảnh về điểm mạnh/yếu của cả một dòng sản phẩm (Product Line) hoặc Ngách (Niche) nếu chỉ làm thủ công.
- **Củng cố nhận định chuyên môn:** Với khối lượng dữ liệu khổng lồ và phân tán, việc xử lý bằng sức người khó có thể bao quát hết 100% chi tiết trong thời gian ngắn. Công cụ này đóng vai trò là "trợ lý dữ liệu", giúp lượng hóa các ý kiến khách hàng thành số liệu khách quan để củng cố cho những quyết định chuyên môn của bạn.

---

## SLIDE 3: CƠ CHẾ HOẠT ĐỘNG
- **Thu thập dữ liệu (On-Demand):** Dữ liệu được thu thập theo yêu cầu (Request) hoặc lấy từ kho dữ liệu có sẵn.
- **Chiến lược lấy mẫu (Sampling Strategy):**
    - Hệ thống lấy mẫu phân tầng theo số sao (ví dụ: lấy mẫu đều 100 review cho mỗi mức từ 1 đến 5 sao) để đảm bảo có đủ dữ liệu phân tích đa chiều.
    - *Lưu ý:* Tổng lượng review thu về phụ thuộc vào thực tế sản phẩm (có thể đạt ~500 reviews nếu đủ dữ liệu, hoặc ít hơn nếu sản phẩm còn mới).
- **AI Hỗ trợ (AI Assistant):** Sử dụng LLM (Gemini 3.0) để phân tích ngữ nghĩa, tóm tắt nội dung và đưa ra các góc nhìn tham khảo, giúp tiết kiệm thời gian đọc hiểu.

---

## SLIDE 4: TÍNH NĂNG - TỔNG QUAN (EXECUTIVE SUMMARY)
- **Product DNA:** Hệ thống tự động trích xuất các thông số kỹ thuật (Material, Niche, Brand...) từ trang sản phẩm.
- **Biến thể (Variations):** Tự động phát hiện và liệt kê các Child ASINs có review, giúp xác định biến thể nào đang bán tốt.
- **Priority Actions:** Dựa trên tần suất xuất hiện của các từ khóa tiêu cực, hệ thống gợi ý Top 3 vấn đề nổi cộm nhất mà khách hàng đang phàn nàn (Dựa trên số lượng review thực tế).

---

## SLIDE 5: TÍNH NĂNG - THẤU HIỂU KHÁCH HÀNG (CUSTOMER X-RAY)
- **Sentiment Analysis (Phân tích cảm xúc):**
    - **Raw Volume (Dữ liệu mẫu):** Số lượng ý kiến đếm được trực tiếp trong tập review vừa thu thập. Dùng để thấy các xu hướng nhỏ, chi tiết.
    - **Impact Score (Dữ liệu thực tế ước tính):** Con số phản ánh quy mô thật trên toàn bộ thị trường.
        - *Cách tính:* Hệ thống lấy tỷ lệ khách hàng nhắc đến một vấn đề trong mẫu (ví dụ: 10% khách 5 sao khen "Vải mát"), sau đó nhân với tổng số lượng Review thực tế trên Amazon.
        - *Ví dụ:* Nếu sản phẩm có 10.000 review thật, Impact Score sẽ chỉ ra có khoảng 1.000 người (10%) đang thực sự hài lòng về vải. 
        - **Giá trị:** Giúp bạn nhìn thấy quy mô thật của từng vấn đề, tránh việc bị quá tập trung vào vài lời chê đơn lẻ mà bỏ qua những thế mạnh đang được số đông ủng hộ.
- **Heatmap (Bản đồ nhiệt):** So sánh nhanh mức độ quan tâm và hài lòng của khách hàng giữa nhiều sản phẩm cạnh tranh.

---

## SLIDE 6: TÍNH NĂNG - SO SÁNH ĐỐI THỦ (MARKET SHOWDOWN)
- **Chế độ so sánh:**
    - **Smart Matching:** Tự động đề xuất đối thủ có Rating tương đồng (+/- 30%) và cùng phân khúc sản phẩm.
    - **Manual Selection:** Cho phép bạn tự chọn bất kỳ đối thủ nào từ danh sách để đối soát.
- **Proven Quality (Chất lượng kiểm chứng):**
    - *Cách tính:* Ưu tiên số lượng khách hàng hài lòng thực tế (Absolute Volume). 
    - *Ví dụ:* Sản phẩm A (5 sao, 2 review) sẽ xếp sau sản phẩm B (4.5 sao, 1000 review) vì số lượng khách hàng thực tế được thỏa mãn của bên B lớn hơn và tin cậy hơn nhiều.

---

## SLIDE 7: TÍNH NĂNG - TRỢ LÝ AI (STRATEGY HUB)
- **Chat với Dữ liệu:** Hỏi đáp trực tiếp với AI. Bạn có thể yêu cầu AI đưa ra **dẫn chứng (Quotes)** trực tiếp từ review trong cơ sở dữ liệu để kiểm chứng tính xác thực.
- **Quick Prompts linh hoạt:** Các câu lệnh mẫu (Viết Content, Tóm tắt Insight) hoàn toàn dựa trên dữ liệu thật của ASIN và có thể được người dùng tùy chỉnh/định nghĩa lại cho sát with nhu cầu.

---

## SLIDE 8: LỘ TRÌNH PHÁT TRIỂN (PHASING STRATEGY)
- **Triết lý phát triển:** "Làm đúng việc - Đúng thời điểm". Chúng tôi chia dự án thành các giai đoạn để tập trung tối đa vào giá trị cốt lõi là SẢN PHẨM.
- **Phase 1 (Hiện tại - Product Insight):**
    - **Đối tượng:** Đội ngũ Phát triển Sản phẩm (R&D / Product Developers).
    - **Mục tiêu:** Cung cấp dữ liệu để Cải tiến sản phẩm cũ & Định hình sản phẩm mới.
    - **Chức năng trọng tâm:**
        - *Phân tích Sản phẩm (Product Aspects):* Soi kỹ từng thông số, chất liệu, thiết kế qua lăng kính phản hồi của khách hàng.
        - *Tìm kiếm "Khoảng trống" (Gap Analysis):* Phát hiện những nhu cầu khách hàng mong muốn nhưng sản phẩm hiện tại (của mình hoặc đối thủ) chưa đáp ứng được.
    - **Giới hạn:** Chỉ tập trung vào khía cạnh sản phẩm, chưa bao gồm các tính năng quản lý kho bãi hay marketing tự động.
- **Phase 2 (Tương lai - Market Radar):**
    - **Mục tiêu:** Mở rộng phạm vi quan sát sang Mạng xã hội (Social Listening) để bắt trend sớm cho R&D.

---

## SLIDE 9: PHẢN HỒI & HỖ TRỢ (FEEDBACK LOOP)
- **Lắng nghe người dùng:** Mọi yêu cầu thêm tính năng (Feature Request) hoặc báo lỗi đều được ghi nhận để hoàn thiện hệ thống.
- **Liên hệ:** 
    - Email: `thanhnt@teecom.vn` (Team T0408 - Ngô Trí Thanh).
- **Mục tiêu:** Xây dựng một công cụ hỗ trợ nghiên cứu sản phẩm thực dụng và sát với nhu cầu thực tế.

---

## SLIDE 10: TÍNH MINH BẠCH & GIỚI HẠN (TRANSPARENCY)
- **Về dữ liệu (Sampling):** Hệ thống không lấy toàn bộ lịch sử review (có thể lên tới hàng chục ngàn). Chúng tôi tập trung lấy mẫu 10 trang review mới nhất cho mỗi loại sao để phản ánh **Xu hướng hiện tại** (Current Trend). Điều này phù hợp với thực tế nghiên cứu vì các phản hồi mới nhất mới là yếu tố quyết định thị trường.
- **Về tốc độ:** Do phụ thuộc vào việc truy xuất dữ liệu từ Amazon, việc cập nhật ASIN mới không thể diễn ra tức thì. Trung bình 1 lượt xử lý (Batch) mất tầm 5-10 phút.
- **Về độ chính xác:** AI giúp tự động hóa việc tổng hợp và phân loại dữ liệu từ hàng ngàn review gốc sang dạng thông tin có cấu trúc. Hệ thống cung cấp một nguồn dữ liệu tập trung và khách quan, giúp bạn giải phóng thời gian khỏi việc bóc tách dữ liệu lẻ tẻ để tập trung tối đa vào việc phân tích chiến lược.

---

## SLIDE 11: QUY TRÌNH SỬ DỤNG (USAGE FLOW - SUMMARY)
1. **Đăng nhập & Lựa chọn:** Chọn ASIN có sẵn hoặc yêu cầu mã mới (Request New ASIN).
2. **Xử lý dữ liệu:** Hệ thống xử lý tự động, mất khoảng 5-10 phút để hoàn tất thu thập và phân tích cho các yêu cầu mới.
3. **Phân tích đa chiều:** Sử dụng các Tab Executive, X-Ray và Showdown để có cái nhìn từ tổng quan đến chi tiết.
4. **Khai thác Insight:** Dùng Strategy Hub để trò chuyện với AI và trích xuất chiến lược hành động.