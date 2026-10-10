import os
import sys
import httpx
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Connection Parameters from Environment Variables
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# List of Bluesky handles or DIDs to track
TARGET_CREATORS = [
    "bsky.app",
    "nytimes.com",
    "techcrunch.com"
]

BSKY_PUBLIC_API = "https://public.api.bsky.app/xrpc"

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_creator_profile(client: httpx.Client, handle: str) -> dict:
    """Fetch profile data from Bluesky public endpoint."""
    url = f"{BSKY_PUBLIC_API}/app.bsky.actor.getProfile"
    response = client.get(url, params={"actor": handle})
    response.raise_for_status()
    return response.json()

def fetch_author_feed(client: httpx.Client, handle: str, limit: int = 50) -> list:
    """Fetch public post feed for a specific actor."""
    url = f"{BSKY_PUBLIC_API}/app.bsky.feed.getAuthorFeed"
    response = client.get(url, params={"actor": handle, "limit": limit})
    response.raise_for_status()
    return response.json().get("feed", [])

def upsert_creator(cursor, profile: dict):
    """Upsert creator details into the creators table."""
    query = """
    INSERT INTO creators (did, handle, display_name, description, avatar_url, followers_count, follows_count, posts_count, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (did) DO UPDATE SET
        handle = EXCLUDED.handle,
        display_name = EXCLUDED.display_name,
        description = EXCLUDED.description,
        avatar_url = EXCLUDED.avatar_url,
        followers_count = EXCLUDED.followers_count,
        follows_count = EXCLUDED.follows_count,
        posts_count = EXCLUDED.posts_count,
        updated_at = NOW();
    """
    cursor.execute(query, (
        profile.get("did"),
        profile.get("handle"),
        profile.get("displayName"),
        profile.get("description"),
        profile.get("avatar"),
        profile.get("followersCount", 0),
        profile.get("followsCount", 0),
        profile.get("postsCount", 0)
    ))

def upsert_posts(cursor, creator_did: str, feed: list):
    """Bulk upsert feed posts into the posts table."""
    post_records = []
    
    for item in feed:
        post = item.get("post", {})
        record = post.get("record", {})
        
        # Parse ISO timestamp to PostgreSQL timestamp
        posted_at_str = record.get("createdAt")
        posted_at = datetime.fromisoformat(posted_at_str.replace("Z", "+00:00")) if posted_at_str else datetime.utcnow()
        
        post_records.append((
            post.get("uri"),
            post.get("cid"),
            creator_did,
            record.get("text", ""),
            post.get("replyCount", 0),
            post.get("repostCount", 0),
            post.get("likeCount", 0),
            post.get("quoteCount", 0),
            posted_at,
            psycopg2.extras.Json(post)  # Raw JSON metadata
        ))

    query = """
    INSERT INTO posts (uri, cid, creator_did, post_text, reply_count, repost_count, like_count, quote_count, posted_at, raw_payload)
    VALUES %s
    ON CONFLICT (uri) DO UPDATE SET
        reply_count = EXCLUDED.reply_count,
        repost_count = EXCLUDED.repost_count,
        like_count = EXCLUDED.like_count,
        quote_count = EXCLUDED.quote_count,
        ingested_at = NOW();
    """
    execute_values(cursor, query, post_records)

def run_ingestion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}", file=sys.stderr)
        return

    print("🚀 Starting Bluesky Ingestion Pipeline...")
    
    with httpx.Client(timeout=10.0) as client:
        for handle in TARGET_CREATORS:
            try:
                print(f"Fetching profile for @{handle}...")
                profile = fetch_creator_profile(client, handle)
                upsert_creator(cursor, profile)
                
                print(f"Fetching posts for @{handle}...")
                feed = fetch_author_feed(client, handle, limit=50)
                upsert_posts(cursor, profile["did"], feed)
                
                conn.commit()
                print(f"✅ Successfully ingested data for @{handle}")
            except Exception as e:
                conn.rollback()
                print(f"❌ Error processing handle {handle}: {e}", file=sys.stderr)

    cursor.close()
    conn.close()
    print("✨ Pipeline Finished.")

if __name__ == "__main__":
    run_ingestion()