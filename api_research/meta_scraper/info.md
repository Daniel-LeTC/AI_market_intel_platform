# Meta (Facebook & Instagram) Scraper Ecosystem

*Note: Meta chống Bot cực gắt. Giá cao hơn TikTok. Ưu tiên độ ổn định (Reliability).*

## 1. Facebook Ads Library (The "Money" Spy)

**Actor Recommendation:** `curious_coder/facebook-ads-library-scraper`
*   **URL:** https://console.apify.com/actors/XtaWFhbtfxyzqrFmd/
*   **Price:** **$0.75 / 1,000 Ads**. (Rẻ nhất thị trường).
*   **Key Output Data:**
    *   `Spend` & `Reach Estimate`: **CỰC QUÝ**. Biết đối thủ chi bao nhiêu tiền.
    *   `Ad Creative`: Snapshot hình ảnh/video.
    *   `Page Name` & `Page ID`.
    *   `Publisher Platform`: Chạy trên FB, Insta hay Messenger?
    *   `Start Date` & `End Date`: Đo độ bền của Ads (Ads chạy lâu = Ads Win).

**Strategy:**
*   Chạy 1 tuần/lần cho list đối thủ.
*   Lọc theo `Spend` (nếu có data) hoặc `Start Date` (Active > 14 ngày).

---

## 2. Instagram Scraper (The "Visual" Spy)

### A. Instagram Post/Reel Scraper (Best Value)
*Actor:* `apify/instagram-scraper` (hoặc `API Dojo`).
*   **Price:** **$0.50 / 1,000 posts**. (Rất rẻ).
*   **Output Data:**
    *   Likes, Comments Count -> muốn lấy nội dung comment thì phải dùng 1 loại scraper riêng.
    *   Image/Video URL (High Res).
    *   Caption & Hashtags.
    *   *Video Duration (để phân tích Reels).*

### B. Instagram Profile Scraper
*Actor:* `apify/instagram-profile-scraper`.
*   **Price:** ~$2.50 / 1,000 profiles.
*   **Strategy:** Chỉ dùng để update Follower Count hàng ngày hay scount deep dive 1 profile cụ thể nào đó. (Scout).

---

## 3. Facebook Page/Post Scraper (The "Community" Spy)

*Actor:* `apify/facebook-pages-scraper`.
*Actor:* `apify/facebook-posts-scraper`.
*   **Price:** ~$10.00 / 1,000 pages. (Đắt).
*   **Price:** ~$5 / 1,000 posts. (Đắt).
* **output:** url, pageid, postid, số lượng comments, text, link image, like, shared
*   **Strategy:**
    *   Chỉ chạy 1 lần đầu để lấy Info (Email, Website, Creation Date).
    *   Sau đó dùng **Posts Scraper** để lấy bài viết mới.

---

## 4. Cost Estimation (Meta Scenario)

**Scenario: Monitor 1 Competitor (Monthly)**

1.  **Ads Spy (Weekly):** 4 lần x 50 active ads = 200 ads.
    *   Cost: ~$1.00.
2.  **Insta Reels Spy (Daily):** 30 ngày x 2 posts = 60 posts.
    *   Cost: ~$0.03 (Rẻ bèo).
3.  **FB Page Post (Daily):** 30 ngày x 2 posts = 60 posts.
    *   Cost: ~$0.10.

**Total Monthly:** **~$1.50 - $2.00 / Competitor.**

**Kết luận:**
Tuy đơn giá Meta đắt hơn TikTok, nhưng số lượng (Volume) post của Meta thấp hơn nhiều (vì Reach kém). Nên tổng chi phí hàng tháng vẫn **RẤT RẺ**.
Trọng tâm ngân sách nên dồn vào **Ads Library Scraper**.
