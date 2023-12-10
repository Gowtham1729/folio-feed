import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import psycopg
import requests
from utils.logging import get_logger

logger = get_logger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "folio-feed")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY", "demo")
MAX_API_QUERIES = 100


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


class Fetcher:
    def __init__(self):
        self.connection = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        self.marketaux_news_url = f"https://api.marketaux.com/v1/news/all"
        self.cursor = self.connection.cursor()

    def get_tickers(self) -> List[Ticker]:
        self.cursor.execute("SELECT ticker FROM news_ticker")
        return [Ticker(ticker[0]) for ticker in self.cursor.fetchall()]

    def insert_news(self, news: List[News]):
        for item in news:
            self.cursor.execute(
                """
                        INSERT 
                        INTO 
                        news_news 
                        (category, symbol, src, src_url, img_src_url, headline, summary, publish_time, sentiment) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                (
                    item.category,
                    item.symbol,
                    item.src,
                    item.src_url,
                    item.img_src_url,
                    item.headline,
                    item.summary,
                    item.publish_time,
                    item.sentiment,
                ),
            )
        self.connection.commit()

    def to_news(self, items: Dict, tickers_list: List[str]) -> List[News]:
        news = []
        for item in items:
            for entity in item.get("entities", []):
                if entity.get("symbol") not in tickers_list:
                    continue
                news.append(
                    News(
                        category=entity.get("type"),
                        symbol=entity.get("symbol"),
                        src=item.get("source"),
                        src_url=item.get("url"),
                        img_src_url=item.get("image_url"),
                        headline=item.get("title"),
                        summary=item.get("description"),
                        publish_time=item.get("published_at"),
                        sentiment=item.get("sentiment_score", 0),
                    )
                )
        return news

    def fetch_news(self):
        logger.info(f"Fetching Tickers...")
        tickers = self.get_tickers()
        tickers_list = [ticker.ticker for ticker in tickers]
        logger.info(f"Ticker List: {tickers_list}")

        ticker_symbols = ",".join(tickers_list)
        today_date = datetime.today().strftime("%Y-%m-%d")
        page = 1
        news_url = f"{self.marketaux_news_url}?symbols={ticker_symbols}&published_on={today_date}"

        logger.info(f"Fetching News from the URl {news_url} ...")
        response = requests.get(f"{news_url}&page={page}&api_token={MARKETAUX_API_KEY}")
        news = []
        if response.status_code == 200:
            response_json = response.json()
            news += self.to_news(response_json["data"], tickers_list)
            logger.info(f"Total News: {response_json['meta']['found']}")

            while (
                page < MAX_API_QUERIES
                and page
                <= response_json["meta"]["found"] // response_json["meta"]["limit"]
            ):
                page += 1
                logger.info(f"Fetching News from the URl {news_url}&page={page} ...")
                response = requests.get(
                    f"{news_url}&page={page}&api_token={MARKETAUX_API_KEY}"
                )
                if response.status_code == 200:
                    response_json = response.json()
                    news += self.to_news(response_json["data"], tickers_list)
                else:
                    logger.error(
                        f"Error fetching news from the URL {news_url}&page={page}"
                    )
                    logger.error(f"Response: {response.json()}")
                    break
        else:
            logger.error(f"Error fetching news from the URL {news_url}")
            logger.error(f"Response: {response.json()}")

        logger.info(f"Finished fetching News: {[n.headline for n in news]}")
        logger.info(f"Inserting News...")
        self.insert_news(news)


if __name__ == "__main__":
    logger.info(f"Starting Fetcher...")
    fetcher = Fetcher()
    logger.info(f"Fetcher Started...")
    fetcher.fetch_news()
    logger.info(f"Fetcher Finished...")
