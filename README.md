Markdown
# 📊 Bluesky Creator Analytics & Engagement Pipeline

A lightweight, production-grade ETL pipeline and relational data model designed to track, store, and analyze creator engagement metrics on the decentralized [Bluesky (AT Protocol)](https://bsky.app) network.

Built with **Python**, **PostgreSQL** (hosted via **Supabase**), and **SQL Window Functions**, this repository demonstrates how to ingest unstructured JSON payloads from public APIs, structure them into relational schemas, and query channel-level engagement trends.

---

## 🏗️ Architecture Overview

           ┌──────────────────────────────┐
           │   Bluesky AT Protocol API    │
           │  (Public HTTP XRPC Endpoints)│
           └──────────────┬───────────────┘
                          │
                          ▼
           ┌──────────────────────────────┐
           │    Python ETL (ingest.py)    │
           │  • httpx (Async-ready HTTP)  │
           │  • psycopg2 (Bulk Upserts)   │
           │  • python-dotenv (Secrets)   │
           └──────────────┬───────────────┘
                          │
                          ▼
           ┌──────────────────────────────┐
           │     PostgreSQL / Supabase    │
           │  • Creators & Posts Schemas  │
           │  • JSONB Raw Metadata Storage│
           │  • Analytical SQL Views      │
           └──────────────────────────────┘

---

## ✨ Key Features

* **Zero API Key Ingestion:** Leverages Bluesky's open AT Protocol XRPC public endpoints (`app.bsky.actor.getProfile` and `app.bsky.feed.getAuthorFeed`).
* **Idempotent Upserts:** Employs PostgreSQL `ON CONFLICT` constraints to ensure safe, repeatable ingestion runs without duplicate records.
* **Semi-Structured Hybrid Storage:** Stores standardized post statistics alongside raw post JSON payloads inside `JSONB` columns for future feature extraction.
* **Advanced SQL Analytics:** Includes pre-written window functions and aggregation queries for creator rankings, engagement velocity, and hourly posting heatmaps.

---

## 📁 Repository Structure

```text
bluesky-creator-analytics/
├── sql/
│   ├── schema.sql              # Table definitions, indices, and views
│   └── analytical_queries.sql  # Insights, rankings, and window functions
├── src/
│   └── ingest.py               # Main Python ingestion pipeline script
├── .env.example                # Environment variables template
├── .gitignore                  # Prevents secrets & cache from hitting Git
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
🚀 Quick Start & Setup
1. Prerequisites
Python 3.10 or higher

PostgreSQL database (Local or hosted via Supabase)

2. Clone Repository & Install Dependencies
Bash
git clone [https://github.com/your-username/bluesky-creator-analytics.git](https://github.com/your-username/bluesky-creator-analytics.git)
cd bluesky-creator-analytics

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
3. Environment Configuration
Create a .env file in the project root based on .env.example:

Code snippet
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_database_password
DB_HOST=aws-0-us-west-1.pooler.supabase.com
DB_PORT=5432
Note: Do not commit .env to version control. It is ignored by .gitignore to keep credentials secure.

🗄️ Database Schema Setup
Run the following SQL commands in your PostgreSQL query editor or Supabase SQL Console to initialize the schema:

SQL
-- 1. Tracked Creators Table
CREATE TABLE IF NOT EXISTS creators (
    did VARCHAR(255) PRIMARY KEY,
    handle VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    avatar_url TEXT,
    followers_count INT DEFAULT 0,
    follows_count INT DEFAULT 0,
    posts_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Creator Posts Table
CREATE TABLE IF NOT EXISTS posts (
    uri VARCHAR(255) PRIMARY KEY,
    cid VARCHAR(255) NOT NULL,
    creator_did VARCHAR(255) NOT NULL REFERENCES creators(did) ON DELETE CASCADE,
    post_text TEXT,
    reply_count INT DEFAULT 0,
    repost_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    quote_count INT DEFAULT 0,
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_payload JSONB,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indices
CREATE INDEX IF NOT EXISTS idx_posts_creator_posted ON posts(creator_did, posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at DESC);
🏃 Running the Ingestion Pipeline
Execute the Python script to fetch profile metadata and recent posts for target creator handles:

Bash
python src/ingest.py
Sample Output:
Plaintext
🚀 Starting Bluesky Ingestion Pipeline...
Fetching profile for @bsky.app...
Fetching posts for @bsky.app...
✅ Successfully ingested data for @bsky.app
Fetching profile for @nytimes.com...
Fetching posts for @nytimes.com...
✅ Successfully ingested data for @nytimes.com
✨ Pipeline Finished.
📈 Sample SQL Analytical Queries
Top Posts per Creator using Window Functions (DENSE_RANK)
SQL
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
🛠️ Tech Stack
Language: Python 3.14

Database: PostgreSQL / Supabase

Libraries: httpx, psycopg2-binary, python-dotenv

Data Sources: Bluesky AT Protocol Public XRPC API

📜 License
Distributed under the MIT License. See LICENSE for more details.