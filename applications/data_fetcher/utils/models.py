from dataclasses import dataclass
from typing import Optional


@dataclass
class Ticker:
    ticker: str


@dataclass
class News:
    category: str
    symbol: str
    src: str
    src_url: str
    img_src_url: str
    headline: str
    summary: str
    publish_time: str
    sentiment: int
    need_attention: bool
    reason: Optional[str]
