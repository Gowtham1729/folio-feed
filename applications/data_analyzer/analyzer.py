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
When you receive news data related to a stock, formatted as {"category": "str", "symbol": "str", "src": "str", "src_url": "str", "headline": "str", "summary": "str"}, analyze this information and produce a single JSON response. The output should strictly follow the structure {"sentiment_score": "float", "need_attention": "bool", "reason": "str"} and must adhere to these guidelines:

Sentiment Score: The sentiment score should range between -10 and 10, where -10 is highly negative, 0 is neutral, and 10 is highly positive. Assign extreme values (+10 or -10) only for news that is defined as 'highly impactful', based on its potential influence on the stock's performance and public sentiment. The stock here is indicated by the "symbol" field.

Need Attention: The "need_attention" field should be a boolean (true or false). Set it to true if the news is important and necessary for someone owning that stock in their portfolio to read. This field indicates that the news item is critical for stockholders to understand potential changes in stock value or company status.

Reason Field: The "reason" field should be a concise but comprehensive explanation, with maximum of 300 characters, outlining why this news item is critical for stockholders and its potential impact on the stock's performance and public perception.

External Data Use: The analysis should rely solely on the provided news data, without the use of external data sources.

Ensure all JSON keys are in lowercase for consistency. The output must only consist of this JSON structure, with no additional text or explanation outside the JSON response. Your response should be based solely on the content and context of the provided news data, avoiding external biases or assumptions.

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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                0,
                False,
            ),
        )

        self.cursor.execute(
            """
            UPDATE news_analysis
            SET 
                average_sentiment = 
                (
                    SELECT 
                        COALESCE(AVG(sentiment) FILTER ( WHERE sentiment != 0 ), 0) AS avg_sentiment
                    FROM 
                        news_news 
                    WHERE 
                        sentiment!=0 AND 
                        symbol = %s AND 
                        DATE(publish_time) = %s
                ), 
                total_news = total_news + 1, 
                positive_news = positive_news + %s, 
                negative_news = negative_news + %s, 
                neutral_news = neutral_news + %s, 
                need_attention = need_attention OR %s
            WHERE symbol = %s AND date = %s
            """,
            (
                news.symbol,
                date,
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
