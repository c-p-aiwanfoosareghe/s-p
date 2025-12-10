CREATE TABLE IF NOT EXISTS reels (
  id SERIAL PRIMARY KEY,
  platform VARCHAR(50) NOT NULL,
  post_id TEXT,
  url TEXT NOT NULL,
  title TEXT,
  uploader TEXT,
  posted_time TIMESTAMP WITH TIME ZONE,
  video_s3_key TEXT,
  raw_metadata JSONB,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  status VARCHAR(32) DEFAULT 'created',
  error TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS reels_unique_url ON reels (url);
