import os
from datetime import datetime
from typing import List

import psycopg
from utils.logging import get_logger
from utils.models import Analysis, News

logger = get_logger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "folio-feed")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


class Analyzer:
    def __init__(self):
        self.connection = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        self.cursor = self.connection.cursor()

    def get_today_news(self) -> List[News]:
        self.cursor.execute(
            """
            SELECT
                category,
                symbol,
                src,
                src_url,
                img_src_url,
                headline,
                summary,
                publish_time,
                sentiment
            FROM
                news_news
            WHERE
                symbol IN (SELECT ticker FROM news_ticker) AND 
                DATE(publish_time) = CURRENT_DATE
            """,
        )
        return [
            News(
                category=item[0],
                symbol=item[1],
                src=item[2],
                src_url=item[3],
                img_src_url=item[4],
                headline=item[5],
                summary=item[6],
                publish_time=item[7],
                sentiment=item[8],
            )
            for item in self.cursor.fetchall()
        ]

    def analyze_news(self, symbol: str, news: List[News]) -> Analysis:
        return Analysis(
            category=news[0].category,
            symbol=symbol,
            date=datetime.now().date().isoformat(),
            average_sentiment=sum([item.sentiment for item in news]) / len(news),
            total_news=len(news),
            positive_news=len([item for item in news if item.sentiment > 0]),
            negative_news=len([item for item in news if item.sentiment < 0]),
            neutral_news=len([item for item in news if item.sentiment == 0]),
            need_attention=False,
        )

    def insert_analysis(self, analysis: List[Analysis]):
        self.cursor.executemany(
            """
            INSERT INTO news_analysis
            (category, symbol, date, average_sentiment, total_news, positive_news, negative_news, need_attention)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            [
                (
                    item.category,
                    item.symbol,
                    item.date,
                    item.average_sentiment,
                    item.total_news,
                    item.positive_news,
                    item.negative_news,
                    item.need_attention,
                )
                for item in analysis
            ],
        )
        self.connection.commit()

    def analyze(self):
        logger.info(f"Fetching all News...")
        all_news = self.get_today_news()
        logger.info(f"News Count: {len(all_news)}")
        news = {}
        for item in all_news:
            if item.symbol not in news:
                news[item.symbol] = []
            news[item.symbol].append(item)

        logger.info(f"Analyzing News...")
        analysis = [self.analyze_news(symbol, news) for symbol, news in news.items()]
        logger.info(f"Analysis: {analysis}")
        logger.info(f"Inserting Analysis...")
        self.insert_analysis(analysis)
        logger.info(f"Analysis Finished!")


if __name__ == "__main__":
    analyzer = Analyzer()
    analyzer.analyze()
