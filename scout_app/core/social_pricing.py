from dataclasses import dataclass

@dataclass
class PricingInfo:
    platform: str
    unit_price: float  # Price per 1,000 items
    base_fee: float    # Fixed fee per run
    speed: str         # 'Fast', 'Medium', 'Slow'
    description: str

SOCIAL_PRICING = {
    "TIKTOK_FEED": PricingInfo(
        platform="TikTok",
        unit_price=0.30,
        base_fee=0.0,
        speed="Fast",
        description="Cào video theo Hashtag hoặc Profile. Rẻ, nhanh."
    ),
    "FB_ADS": PricingInfo(
        platform="Facebook Ads",
        unit_price=5.00,  # $5 per 1k ads
        base_fee=0.50,    # $0.50 start fee
        speed="Slow",
        description="Soi thư viện quảng cáo đối thủ. Đắt nhưng giá trị cao."
    ),
    "INSTA_POSTS": PricingInfo(
        platform="Instagram",
        unit_price=3.50,
        base_fee=0.20,
        speed="Medium",
        description="Cào ảnh/video Tagged hoặc Reels."
    )
}

def estimate_cost(platform_key: str, item_count: int) -> float:
    """
    Calculate estimated cost based on platform and quantity.
    """
    if platform_key not in SOCIAL_PRICING:
        return 0.0
    
    price = SOCIAL_PRICING[platform_key]
    item_cost = (item_count / 1000) * price.unit_price
    total = price.base_fee + item_cost
    return round(total, 2)
