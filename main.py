import requests

API_TOKEN = "96577bd0-188f-43a5-8c5b-082661ada035"
DATASET_ID = "gd_le8e811kzy4ggddlq"


def main():
    url = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={DATASET_ID}&include_errors=true"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    # Payload CHUẨN: Tách biệt Input và Config
    payload = {
        "input": [
            {"url": "https://www.amazon.com/dp/B07XF4NGQP"},
            {"url": "https://www.amazon.com/dp/B07SX1Z6DZ"},
        ],
        # Mẹo phá limit: Một số dataset nó nhận tham số ở đây
        "options": {"max_results": 500, "num_of_reviews": 500},
        "deliver": {
            "type": "gcs",
            "bucket": "my-scraper-data-2026",
            "credentials": {
                "client_email": "bright-data-uploader@bright-data-uploader.iam.gserviceaccount.com",
                "private_key": r"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDUchYvk6YUXhUp\n8DXluTyxN8qPYpcdeGQuZPBzvTlbXfDVlyYOFTTdffVNIHgB41gCl+qtMHGBXi7B\nTOApiVkPlaFNMgCmtTBFc3VV7PddQRR+8N9aOLxrDxzZnpX86azB9Ji5/5AaE+/D\nybXhLgAvEl5+cM1W3iBIX3/TFgZafGMnfv0rPEbUn3605Ec7AuQyZm7p/jZAIYv2\nel4IhA1K2iQAlZfC61x2u1mxs0fT5hbrBGufHIQV+ZD7prGwQVytKkOrGijKU+K4\ntVQRJF1SxRSY5mp63Ll1EV/dYvKpbpyOFye5bwQ3I+UEzWVIyvm+fUeZkNqtGHIZ\nbG1rIFHDAgMBAAECggEABAWZTB/h8+tbppyz3U9jI3TyCNvhDrKreg6SiyzIy+Uc\nr/zgDUIAHoKJ2DXZcvbmwPA3H6QJChEKScHwUaj8sb68VbWw7UPR3NOH1zwYt/NW\nKLJCFp2rWrJOPzc+EXjFB5j4751NRGK4CWW/FtSKaVm4kz4Ec45zkwGUoTgYbH8U\ng7F/GcZaQQHLg4aFgw3QiCdZnNHMfmqQrwoX1MgfxfxZBxftVtZ9Y62XWNjmeCrn\nXm4QJpD3NvGhxVdCfC4bqKvLqE+nD7qDyDcFe/Zk/W50f8aB3vqDLDGqMsRoQDHr\nR9HFrzbkiO8/LRRsc0hX6kElYd3SiK6JunG3e1xoyQKBgQDrXeZKLnJUj/7nTASY\nVQRlXL3WmnP4/DGWEmz4iu0LEe/qiNONHcsKaebfCO8eUYv6eU/ep4n7M7Xq79G+\nGlvPDN8RrcFHqlOlDcWcc5vAlA32XPAxFyOrvP2o622kCTOW7EjDYHNNJjkP1JYQ\ Lok6JDJgewom0y2yiaVcDY6duQKBgQDnEcp362zSRhpTK6BPWYQEkSNu59AfTWql\nuorf+e/Ih2vM2DANf+sEvjMesA+NtlAOGM872cY0eF0LoXBrb/lFVKPaAcgEZD2q\nJxEfgihIwt+9OtNdVgaQKa1qTkAz/NHBPqFzjqfe9zY0bVpxyChJhH2x5x/NmdsQ\nko3IqFjJWwKBgQCZ9/tGW8v+9ZPSyy/WVwdhJ6IoWTG0l4X4nmUa0gbvTvSbgJaj\nofHJBi45iSajtsTTPbi59u+UnOdMoUWcDrIwaEMk1X2y3AGL38594kLpX/EiUPnv\noyt6lU96yUgYHszY1gljhhznQzHg4TiprUen+TXbV6H0dAFY4iKCbXv2QQKBgQCz\ nn+7m3gqQQ5K/SNCsHog0DKeg1W/Chan7/1Fp3595IVy5tu1T8Ta/TyPqHS9aGHmP\nG9YtTpN3woGCQxNjUX5TWQKuvGfCkjIljY0QE1xBg8vuDEa27eLYOq3mT8I1J7nf\nIVLcw+7XsxFeHAwNG23GCMq1e1gLuijDb0nszIGItQKBgCJu8beqKFBTsm6CKgZl\nQpxLObrwRsXybn9qYIyXq//OGi5UnBCAqttu6zjO39GFTGvNm3qN6YeyAeXWZty1\nDwQufQD3ntO2PII0eozTR3M9fEzy2jrLuuk6rLgbxlgzL1CKsgWXqDyYT06LFb4v\njcZ0706YudB6Bavjw0A6Jm+b\n-----END PRIVATE KEY-----\n",
            },
            "directory": "scraped_reviews_data/raw/",
            "filename": {
                "extension": "csv",
                "template": "amazon_reviews_{[job]}_{[datetime]}",
            },
        },
    }

    res = requests.post(url, headers=headers, json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")


if __name__ == "__main__":
    main()
