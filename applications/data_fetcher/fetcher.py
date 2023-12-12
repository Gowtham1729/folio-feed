import json
import os
from datetime import datetime
from typing import Dict, List

import pika
import psycopg
import requests
from utils.logging import get_logger
from utils.models import News, Ticker

logger = get_logger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "folio-feed")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

MARKETAUX_API_KEY = os.getenv(
    "MARKETAUX_API_KEY", "WCUoFK1UQ1ZvtCL7jlIVCTBkJHUDh7pDsPUAZdqV"
)
MAX_API_QUERIES = 100

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "news")


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
        self.rabbitmq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host="/",
                credentials=pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD),
            )
        )

    def get_tickers(self) -> List[Ticker]:
        self.cursor.execute("SELECT ticker FROM news_ticker")
        return [Ticker(ticker[0]) for ticker in self.cursor.fetchall()]

    def insert_news(self, news: List[News]) -> List[int]:
        ids = []
        for item in news:
            self.cursor.execute(
                """
                        INSERT 
                        INTO 
                        news_news 
                        (category, symbol, src, src_url, img_src_url, headline, summary, publish_time, sentiment, need_attention, reason) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, false, null)
                        ON CONFLICT DO NOTHING
                        RETURNING id
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
                ),
            )
            try:
                id_of_new_row = self.cursor.fetchone()[0]
                ids.append(id_of_new_row)
            except TypeError:
                logger.info(f"News already exists: {item.headline}")

        self.connection.commit()
        return ids

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
                        sentiment=0,
                        need_attention=False,
                        reason=None,
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
                page < 1
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
        ids = self.insert_news(news)

        logger.info(f"Sending News to RabbitMQ...")
        channel = self.rabbitmq_connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        for id_ in ids:
            channel.basic_publish(
                exchange="",
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps({"id": id_, "date": today_date}),
            )


if __name__ == "__main__":
    logger.info(f"Starting Fetcher...")
    fetcher = Fetcher()
    logger.info(f"Fetcher Started...")
    fetcher.fetch_news()
    logger.info(f"Fetcher Finished...")
