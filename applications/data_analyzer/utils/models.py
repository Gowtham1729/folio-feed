from dataclasses import dataclass


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
    sentiment: str


@dataclass
class Analysis:
    category: str
    symbol: str
    date: str
    average_sentiment: float
    total_news: int
    positive_news: int
    negative_news: int
    neutral_news: int
    need_attention: bool
