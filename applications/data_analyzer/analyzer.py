import json
import os
import time
from datetime import datetime
from typing import List, Optional, Tuple

import pika
import psycopg
from utils.logging import get_logger
from utils.models import Analysis, News
from vertexai.language_models import TextGenerationModel

logger = get_logger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "folio-feed")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "news")

GCP_PROJECT = os.getenv("GCP_PROJECT", "folio-feed-403709")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL_NAME", "text-bison")
MODEL_PARAMETERS = {
    "candidate_count": 1,
    "max_output_tokens": 1024,
    "temperature": 1,
    "top_k": 40,
}

PROMPT = """"
When you receive news data related to a stock, formatted as {"category": "str", "symbol": "str", "src": "str", "src_url": "str", "headline": "str", "summary": "str"}, you are to analyze this information and produce a single JSON response. The output should strictly follow the structure {"sentiment_score": "float", "need_attention": "bool", "reason": "str"} and must adhere to these guidelines:

The sentiment score should range between -1 and 1, where -1 is highly negative, 0 is neutral, and 1 is highly positive. This score should reflect the potential impact of the news on the stock's performance and public sentiment.

The "need_attention" field should be a boolean (true or false). Set it to true if the news is likely to significantly influence the stock's performance or public perception. If set to true, provide a brief explanation in the "reason" field, outlining why this news item demands attention.

If "need_attention" is false, the "reason" field should either be an empty string or a concise explanation of why the news is considered to have little or no impact.

Ensure all JSON keys are in lowercase (e.g., "sentiment_score," "need_attention," "reason") for consistency.

The output must only consist of this JSON structure, with no additional text or explanation outside the JSON response.

Your response should be based solely on the content and context of the provided news data, avoiding external biases or assumptions.

Analyze the given data and output only the following JSON structure:
{"sentiment_score": float, "need_attention": bool, "reason": string}
"""


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
        self.model = TextGenerationModel.from_pretrained(model_name=MODEL_NAME)

    def get_today_news(self) -> List[News]:
        self.cursor.execute(
            """
            SELECT
                id,
                category,
                symbol,
                src,
                src_url,
                img_src_url,
                headline,
                summary,
                publish_time,
                sentiment,
                need_attention,
                reason
            FROM
                news_news
            WHERE
                symbol IN (SELECT ticker FROM news_ticker) AND 
                DATE(publish_time) = CURRENT_DATE
            """,
        )
        return [
            News(
                id=item[0],
                category=item[1],
                symbol=item[2],
                src=item[3],
                src_url=item[4],
                img_src_url=item[5],
                headline=item[6],
                summary=item[7],
                publish_time=item[8],
                sentiment=item[9],
                need_attention=item[10],
                reason=item[11],
            )
            for item in self.cursor.fetchall()
        ]

    def fetch_news(self, id_: int) -> News:
        self.cursor.execute(
            """
            SELECT
                id,
                category,
                symbol,
                src,
                src_url,
                img_src_url,
                headline,
                summary,
                publish_time,
                sentiment,
                need_attention,
                reason
            FROM
                news_news
            WHERE
                id = %s
            """,
            (id_,),
        )
        item = self.cursor.fetchone()
        return News(
            id=item[0],
            category=item[1],
            symbol=item[2],
            src=item[3],
            src_url=item[4],
            img_src_url=item[5],
            headline=item[6],
            summary=item[7],
            publish_time=item[8],
            sentiment=item[9],
            need_attention=item[10],
            reason=item[11],
        )

    def analyze_symbol(self, symbol: str, news: List[News]) -> Analysis:
        return Analysis(
            category=news[0].category,
            symbol=symbol,
            date=datetime.now().date().isoformat(),
            average_sentiment=sum([item.sentiment for item in news]) / len(news),
            total_news=len(news),
            positive_news=len([item for item in news if item.sentiment > 0]),
            negative_news=len([item for item in news if item.sentiment < 0]),
            neutral_news=len([item for item in news if item.sentiment == 0]),
            need_attention=any([item for item in news if item.need_attention]),
        )

    def insert_analysis(self, analysis: List[Analysis]):
        self.cursor.executemany(
            """
            INSERT INTO news_analysis
            (category, symbol, date, average_sentiment, total_news, positive_news, negative_news, neutral_news, need_attention)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, date) DO UPDATE SET average_sentiment = EXCLUDED.average_sentiment, total_news = EXCLUDED.total_news, positive_news = EXCLUDED.positive_news, negative_news = EXCLUDED.negative_news, neutral_news = EXCLUDED.neutral_news, need_attention = EXCLUDED.need_attention
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
                    item.neutral_news,
                    item.need_attention,
                )
                for item in analysis
            ],
        )
        self.connection.commit()

    def update_ai_news_analysis(self, news: List[News]):
        self.cursor.executemany(
            """
            UPDATE news_news
            SET sentiment = %s, need_attention = %s, reason = %s
            WHERE id = %s
            """,
            [
                (
                    item.sentiment,
                    item.need_attention,
                    item.reason,
                    item.id,
                )
                for item in news
            ],
        )
        self.connection.commit()

    def ai_analysis(self, news: News) -> Tuple[float, bool, Optional[str]]:
        query = f"""{PROMPT}
            input: {{"category": "{news.category}", "symbol": "{news.symbol}", "src": "{news.src}", "src_url": "{news.src_url}", "headline": "{news.headline}", "summary": "{news.summary}"}}
            output:
            """
        response = self.model.predict(query, **MODEL_PARAMETERS)
        logger.info(f"Response: {response.text}")

        try:
            cleaned_response = (
                response.text.replace("```", "")
                .replace("JSON\n", "")
                .replace("json\n", "")
                .strip()
            )
            json_response = json.loads(cleaned_response)
            logger.info(f"Response JSON Parse Success")
            time.sleep(5)
            return (
                json_response["sentiment_score"],
                json_response["need_attention"],
                json_response["reason"],
            )
        except Exception as e:
            logger.info(f"Response Parsing Failed")
            logger.error(f"Error: {e}")
            time.sleep(5)
            return 0, False, None

    def update_daily_analysis(self, news: News, date: str):
        self.cursor.execute(
            """
            INSERT INTO news_analysis
            (category, symbol, date, average_sentiment, total_news, positive_news, negative_news, neutral_news, need_attention)
            VALUES (%s, %s, %s, %s, 1, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                news.category,
                news.symbol,
                date,
                0,
                0,
                0,
                0,
                False,
            ),
        )

        self.cursor.execute(
            """
            UPDATE news_analysis
            SET 
                average_sentiment = (SELECT AVG(sentiment) FROM news_news), 
                total_news = total_news + 1, 
                positive_news = positive_news + %s, 
                negative_news = negative_news + %s, 
                neutral_news = neutral_news + %s, 
                need_attention = need_attention OR %s
            WHERE symbol = %s AND date = %s
            """,
            (
                1 if news.sentiment > 0 else 0,
                1 if news.sentiment < 0 else 0,
                1 if news.sentiment == 0 else 0,
                True if news.need_attention else False,
                news.symbol,
                date,
            ),
        )
        self.connection.commit()

    def analyze_news(self, ch, method, properties, body: str):
        body_dict = json.loads(body)
        id_ = body_dict.get("id")
        date = body_dict.get("date")
        if not date or not id_:
            logger.error(f"Invalid Input: {body}")
            return

        logger.info(f"Analyzing News...")
        news = self.fetch_news(id_)
        sentiment, need_attention, reason = self.ai_analysis(news)
        news.sentiment = sentiment
        news.need_attention = need_attention
        news.reason = reason
        logger.info(f"News Analysis: {news}")

        logger.info(f"Updating AI Analysis...")
        self.update_ai_news_analysis([news])
        logger.info(f"AI Analysis Updated!")

        logger.info(f"Updating {news.symbol} Analysis on date {date}...")
        self.update_daily_analysis(news, date)
        logger.info(f"Analysis Updated!")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def analyze(self):
        logger.info(f"Fetching all News...")
        all_news = self.get_today_news()
        logger.info(f"News Count: {len(all_news)}")
        news = {}
        for item in all_news:
            if item.symbol not in news:
                news[item.symbol] = []
            news[item.symbol].append(item)

        logger.info(f"News AI Analysis...")
        for symbol, news_list in news.items():
            for item in news_list:
                sentiment, need_attention, reason = self.ai_analysis(item)
                item.sentiment = sentiment
                item.need_attention = need_attention
                item.reason = reason

        logger.info(f"Updating AI Analysis...")
        self.update_ai_news_analysis(all_news)

        logger.info(f"Analyzing Each Symbol...")
        analysis = [self.analyze_symbol(symbol, news) for symbol, news in news.items()]
        logger.info(f"Analysis: {analysis}")

        logger.info(f"Inserting Analysis...")
        self.insert_analysis(analysis)
        logger.info(f"Analysis Finished!")


if __name__ == "__main__":
    analyzer = Analyzer()
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=pika.PlainCredentials(
                username=RABBITMQ_USERNAME, password=RABBITMQ_PASSWORD
            ),
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_consume(
        queue=RABBITMQ_QUEUE,
        on_message_callback=lambda ch, method, properties, body: analyzer.analyze_news(
            ch, method, properties, body
        ),
        auto_ack=False,
    )
    logger.info(f"Waiting for news...")
    channel.start_consuming()
