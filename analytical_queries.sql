-- ====================================================================
-- BLUESKY CREATOR ANALYTICS - SAMPLE ANALYTICAL QUERIES
-- ====================================================================

-- 1. TOP PERFORMING POSTS ACROSS ALL CREATORS
-- Finds posts with the highest overall engagement (likes + reposts + replies).
SELECT 
    c.handle,
    p.post_text,
    p.like_count,
    p.repost_count,
    p.reply_count,
    (p.like_count + p.repost_count + p.reply_count) AS total_engagement,
    p.posted_at
FROM posts p
JOIN creators c ON p.creator_did = c.did
ORDER BY total_engagement DESC
LIMIT 10;


-- 2. CHANNEL ENGAGEMENT OVERVIEW
-- Aggregates creator performance metrics to compare account averages.
SELECT 
    c.handle,
    c.followers_count,
    COUNT(p.uri) AS total_posts_tracked,
    COALESCE(SUM(p.like_count), 0) AS total_likes,
    COALESCE(SUM(p.repost_count), 0) AS total_reposts,
    COALESCE(ROUND(AVG(p.like_count + p.repost_count + p.reply_count), 2), 0) AS avg_engagement_per_post,
    MAX(p.posted_at) AS last_posted_at
FROM creators c
LEFT JOIN posts p ON c.did = p.creator_did
GROUP BY c.did, c.handle, c.followers_count
ORDER BY avg_engagement_per_post DESC;


-- 3. WINDOW FUNCTION: TOP 3 POSTS PER CREATOR
-- Uses DENSE_RANK() to find each creator's top 3 highest-performing posts.
WITH ranked_posts AS (
    SELECT 
        c.handle,
        p.post_text,
        p.like_count,
        p.repost_count,
        p.posted_at,
        DENSE_RANK() OVER (
            PARTITION BY p.creator_did 
            ORDER BY (p.like_count + p.repost_count) DESC
        ) AS engagement_rank
    FROM posts p
    JOIN creators c ON p.creator_did = c.did
)
SELECT 
    handle,
    engagement_rank,
    post_text,
    like_count,
    repost_count,
    posted_at
FROM ranked_posts
WHERE engagement_rank <= 3
ORDER BY handle, engagement_rank;


-- 4. HOURLY POSTING ACTIVITY HEATMAP
-- Analyzes which hours of the day yield the highest volume and average engagement.
SELECT 
    EXTRACT(HOUR FROM p.posted_at) AS post_hour_utc,
    COUNT(p.uri) AS posts_published,
    ROUND(AVG(p.like_count), 2) AS avg_likes
FROM posts p
GROUP BY post_hour_utc
ORDER BY post_hour_utc ASC;
