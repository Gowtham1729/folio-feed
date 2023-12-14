from datetime import datetime
from unittest.mock import patch

import pytest
from data_analyzer.analyzer import Analyzer
from data_analyzer.utils.models import Analysis, News

APPLE_NEWS_1 = News(
    id=1,
    category="equity",
    symbol="AAPL",
    src="example",
    src_url="https://www.example.com",
    img_src_url="https://example.com/img.png",
    headline="Apple launches new iPhone 12",
    summary="Apple launches new iPhone 12",
    publish_time="2020-05-17T10:00:00.000Z",
    sentiment=1,
    need_attention=False,
    reason=None,
)

APPLE_NEWS_2 = News(
    id=2,
    category="equity",
    symbol="AAPL",
    src="example",
    src_url="https://www.example.com",
    img_src_url="https://example.com/img.png",
    headline="Apple launches new iPad 5",
    summary="Apple launches new iPad 5",
    publish_time="2020-05-17T10:00:00.000Z",
    sentiment=1,
    need_attention=True,
    reason=None,
)


@pytest.fixture()
def analyzer():
    with patch("psycopg.connect") as mock_connect:
        mock_connect.return_value.cursor.return_value.fetchone.return_value = [
            1,
            "equity",
            "AAPL",
            "example",
            "https://www.example.com",
            "https://example.com/img.png",
            "Apple launches new iPhone 12",
            "Apple launches new iPhone 12",
            "2020-05-17T10:00:00.000Z",
            1,
            False,
            None,
        ]
        yield Analyzer()


class TestAnalyzer:
    @pytest.mark.parametrize(
        "symbol, news, expected",
        [
            (
                "AAPL",
                [
                    APPLE_NEWS_1,
                    APPLE_NEWS_2,
                ],
                Analysis(
                    category="equity",
                    symbol="AAPL",
                    date=datetime.now().date().isoformat(),
                    average_sentiment=1,
                    total_news=2,
                    positive_news=2,
                    negative_news=0,
                    neutral_news=0,
                    need_attention=True,
                ),
            ),
        ],
    )
    def test__analyze_symbol(self, symbol, news, expected):
        analyzer = Analyzer()
        actual = analyzer.analyze_symbol(symbol, news)
        assert actual.__dict__ == expected.__dict__

    def test__fetch_news(self, analyzer):
        expected_news = APPLE_NEWS_1
        result = analyzer.fetch_news(1)
        assert result.__dict__ == expected_news.__dict__
