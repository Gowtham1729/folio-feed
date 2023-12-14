from unittest.mock import patch

import pytest
from data_fetcher.fetcher import Fetcher
from data_fetcher.utils.models import News, Ticker

APPLE_NEWS_1 = News(
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
        mock_connect.return_value.cursor.return_value.fetchall.return_value = [
            "AAPL",
            "GOOG",
        ]
        yield Fetcher()


class TestAnalyzer:
    def test_get_tickers(self, analyzer):
        expected_tickers = [Ticker(ticker="AAPL"), Ticker(ticker="GOOG")]
        result = analyzer.get_tickers()
        assert result == expected_tickers
