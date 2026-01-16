# TikTok Scraper Ecosystem: The "Budget Beast" & The "Heavyweight"

Tài liệu tổng hợp các Actor TikTok trên Apify.
**RECOMMENDATION:** Dùng bộ **"Budget Ecosystem"** (Option 1) cho 99% nhu cầu vì giá rẻ hơn 10 lần và tốc độ cao.

---

# OPTION 1: THE BUDGET ECOSYSTEM (Khuyên Dùng)
**Đặc điểm:** Giá đồng hạng **$0.30 / 1,000 records**. Tốc độ thần sầu. Output sạch.

### 1. 🏯 TikTok Comments Scraper (The Sniper)
*Actor:* `XomSRf7d0qf3mVj1y`
*URL:* https://console.apify.com/actors/XomSRf7d0qf3mVj1y/
*Price:* **$0.30 / 1,000 comments**

**Output Schema:**
```json
{
  "id": "7353781970163272993",
  "text": "Comment content here...",
  "diggCount": 246,
  "replyCommentTotal": 3,           // Quan trọng để lọc debate
  "createTimeISO": "2024-08-06T11:21:16.000Z",
  "uniqueId": "user_handle",
  "cid": "7399984975553086214",
  "videoWebUrl": "..."
}
```

### 2. 🕺 TikTok Post/Video Scraper (The Scout)
*Actor:* `5K30i8aFccKNF5ICs`
*URL:* https://console.apify.com/actors/5K30i8aFccKNF5ICs/
*Price:* **$0.30 / 1,000 posts** (Rẻ hơn 10 lần so với mức $3.00 cũ).

**Key Features:**
- Có **`subtitleInformation`**: Lấy được sub (caption) mà không cần Whisper AI.
- Có `bookmarks`: Chỉ số Buying Intent.

**Output Schema:**
```json
{
  "id": "7353781970163272993",
  "title": "full tutorial #digitalproducts...",
  "views": 101399,
  "likes": 7420,
  "comments": 201,
  "shares": 1236,
  "bookmarks": 7195,                // Save count
  "hashtags": ["digitalproducts"],
  "uploadedAt": 1712185805,
  "video": {
    "url": "https://v45.tiktokcdn-eu.com/...", // No watermark (thường là vậy)
    "duration": 223.9
  },
  "song": { "title": "original sound", "artist": "jacksonstips" },
  "subtitleInformation": [          // GOLD MINE: Subtitle text
    { "lang": "eng-US", "url": "..." }
  ]
}
```

### 3. 👤 TikTok Profile Scraper (The Feed Reader)
*Actor:* `ssOXktOBaQQiYfhc4`
*URL:* https://console.apify.com/actors/ssOXktOBaQQiYfhc4/
*Price:* **$0.30 / 1,000 posts**
*Use Case:* Quét toàn bộ video của 1 KOL cụ thể.

**Output Schema:** (Tương tự Post Scraper nhưng kèm Collab Info)
```json
{
  "id": "7524427347697896726",
  "title": "Video title...",
  "views": 489994,
  "collabInfo": {                   // Detect paid partnership / collab
    "collaborators": [ { "username": "f1", "name": "Formula 1" } ]
  }
}
```

### 4. TikTok User Scraper (The Network Spy)
*Actor:* `nZqIUKyoBelvbSn1g`
*URL:* https://console.apify.com/actors/nZqIUKyoBelvbSn1g/
*Price:* **$0.30 / 1,000 users**
*Use Case:* Quét thông tin chi tiết của list Followers.

**Output Schema:**
```json
{
    "id": "7043896727212409862",
    "username": "a3k113",
    "followers": 94,
    "following": 1477,
    "likes": 38,
    "videos": 2,
    "verified": true,
    "bio": "🌺",
    "hasEmail": false,
    "region": "SA"
}
```

---

# OPTION 2: THE LEGACY PREMIUM (Dùng khi cần tính năng dị)
*Actor:* `GdWCkxBtKWOsKjdch` (All-in-One)
*Price:* **$3.00 / 1,000 results** (Đắt gấp 10 lần).

**Khi nào nên dùng thằng này?**
- Khi cần các trường dị mà bộ Budget không có (ví dụ: Music Meta cực chi tiết, hoặc Author Meta rất sâu trong cùng 1 request).
- Khi bộ Budget bị lỗi (Plan B).

**Output Schema (Legacy):**
*(Tham khảo file cũ hoặc docs trên Apify)*
