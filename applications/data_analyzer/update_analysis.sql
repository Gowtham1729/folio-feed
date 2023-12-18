WITH news_stats AS (
    SELECT
        COALESCE(AVG(sentiment) FILTER ( WHERE sentiment != 0 ), 0) AS avg_sentiment,
        COUNT(*) AS total_news_count,
        COUNT(*) FILTER (WHERE sentiment > 0) AS positive_news_count,
        COUNT(*) FILTER (WHERE sentiment < 0) AS negative_news_count,
        COUNT(*) FILTER (WHERE sentiment = 0) AS neutral_news_count,
        BOOL_OR(need_attention) AS any_need_attention
    FROM
        news_news
    WHERE
        DATE(publish_time) = '2023-12-17'
        AND symbol = 'NFLX'
)
UPDATE
    news_analysis
SET
    average_sentiment = news_stats.avg_sentiment,
    total_news = news_stats.total_news_count,
    positive_news = news_stats.positive_news_count,
    negative_news = news_stats.negative_news_count,
    neutral_news = news_stats.neutral_news_count,
    need_attention = news_stats.any_need_attention
FROM
    news_stats
WHERE
    news_analysis.symbol = 'NFLX'
    AND news_analysis.date = '2023-12-17';
