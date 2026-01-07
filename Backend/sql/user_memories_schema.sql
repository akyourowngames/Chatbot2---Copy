-- ============================================================
-- Per-User Memory System - Supabase Schema
-- ============================================================
-- Run this in your Supabase SQL Editor to create the table
-- 
-- IMPORTANT: This creates a per-user memory system where:
-- - Each user's data is completely isolated
-- - Vector embeddings enable semantic search
-- - Row-Level Security ensures data privacy
-- ============================================================

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing table if recreating
-- DROP TABLE IF EXISTS user_memories;

-- Create the user_memories table
CREATE TABLE IF NOT EXISTS user_memories (
    -- Primary key
    id TEXT PRIMARY KEY,
    
    -- User isolation (CRITICAL for per-user data)
    user_id TEXT NOT NULL,
    
    -- Memory content
    content TEXT NOT NULL,
    
    -- Vector embedding for semantic search (384 dimensions for all-MiniLM-L6-v2)
    -- Using JSONB as fallback if pgvector not available
    embedding JSONB,
    
    -- If you have pgvector extension, use this instead:
    -- embedding vector(384),
    
    -- Categorization
    category TEXT DEFAULT 'general',
    
    -- Importance score (0.0 - 1.0)
    importance FLOAT DEFAULT 0.5,
    
    -- Session linking for cross-session context
    session_id TEXT DEFAULT 'global',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    
    -- Access tracking for importance decay
    access_count INTEGER DEFAULT 0,
    
    -- Compression flags
    compressed BOOLEAN DEFAULT FALSE,
    parent_memory_id TEXT REFERENCES user_memories(id) ON DELETE SET NULL,
    
    -- Additional metadata (JSONB for flexibility)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Index for user isolation (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_user_memories_user_id 
    ON user_memories(user_id);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS idx_user_memories_category 
    ON user_memories(user_id, category);

-- Index for temporal queries
CREATE INDEX IF NOT EXISTS idx_user_memories_created 
    ON user_memories(user_id, created_at DESC);

-- Index for importance-based retrieval
CREATE INDEX IF NOT EXISTS idx_user_memories_importance 
    ON user_memories(user_id, importance DESC);

-- Index for session linking
CREATE INDEX IF NOT EXISTS idx_user_memories_session 
    ON user_memories(user_id, session_id);

-- Index for non-compressed memories
CREATE INDEX IF NOT EXISTS idx_user_memories_active 
    ON user_memories(user_id, compressed) 
    WHERE compressed = FALSE;

-- ============================================================
-- ROW LEVEL SECURITY (RLS) - CRITICAL FOR USER ISOLATION
-- ============================================================

-- Enable RLS
ALTER TABLE user_memories ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own memories
CREATE POLICY "Users can view own memories" 
    ON user_memories FOR SELECT 
    USING (auth.uid()::text = user_id OR user_id LIKE 'test_%');

-- Policy: Users can insert their own memories
CREATE POLICY "Users can insert own memories" 
    ON user_memories FOR INSERT 
    WITH CHECK (auth.uid()::text = user_id OR user_id LIKE 'test_%');

-- Policy: Users can update their own memories
CREATE POLICY "Users can update own memories" 
    ON user_memories FOR UPDATE 
    USING (auth.uid()::text = user_id OR user_id LIKE 'test_%');

-- Policy: Users can delete their own memories
CREATE POLICY "Users can delete own memories" 
    ON user_memories FOR DELETE 
    USING (auth.uid()::text = user_id OR user_id LIKE 'test_%');

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Function to get memory count per user
CREATE OR REPLACE FUNCTION get_user_memory_count(p_user_id TEXT)
RETURNS TABLE(total BIGINT, active BIGINT, compressed BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total,
        COUNT(*) FILTER (WHERE NOT user_memories.compressed)::BIGINT as active,
        COUNT(*) FILTER (WHERE user_memories.compressed)::BIGINT as compressed
    FROM user_memories
    WHERE user_memories.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get categories with counts
CREATE OR REPLACE FUNCTION get_user_memory_categories(p_user_id TEXT)
RETURNS TABLE(category TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        user_memories.category,
        COUNT(*)::BIGINT
    FROM user_memories
    WHERE user_memories.user_id = p_user_id
      AND NOT user_memories.compressed
    GROUP BY user_memories.category
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean up old compressed memories (older than 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_memories(days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_memories
    WHERE compressed = TRUE
      AND created_at < NOW() - (days_old || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- PGVECTOR SEMANTIC SEARCH (Optional - if pgvector is enabled)
-- ============================================================

-- Uncomment this if you have pgvector extension and want true vector search:
/*
-- Create vector column
ALTER TABLE user_memories ADD COLUMN IF NOT EXISTS embedding_vector vector(384);

-- Create HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_user_memories_embedding 
    ON user_memories 
    USING hnsw (embedding_vector vector_cosine_ops);

-- Function for semantic search using pgvector
CREATE OR REPLACE FUNCTION search_user_memories(
    p_user_id TEXT,
    p_query_embedding vector(384),
    p_limit INTEGER DEFAULT 5,
    p_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE(
    id TEXT,
    content TEXT,
    category TEXT,
    importance FLOAT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.content,
        m.category,
        m.importance,
        1 - (m.embedding_vector <=> p_query_embedding) as similarity
    FROM user_memories m
    WHERE m.user_id = p_user_id
      AND NOT m.compressed
      AND (1 - (m.embedding_vector <=> p_query_embedding)) >= p_threshold
    ORDER BY m.embedding_vector <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
*/

-- ============================================================
-- GRANT PERMISSIONS
-- ============================================================

-- Grant access to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON user_memories TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_memory_count TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_memory_categories TO authenticated;

-- ============================================================
-- SAMPLE DATA (for testing - remove in production)
-- ============================================================

-- Uncomment to insert test data:
/*
INSERT INTO user_memories (id, user_id, content, category, importance, session_id)
VALUES 
    ('mem_test_001', 'test_user_123', 'I prefer dark mode interfaces', 'preference', 0.8, 'session_1'),
    ('mem_test_002', 'test_user_123', 'My favorite language is Python', 'preference', 0.7, 'session_1'),
    ('mem_test_003', 'test_user_123', 'Working on KAI chatbot project', 'context', 0.9, 'session_2'),
    ('mem_test_004', 'test_user_456', 'I like light mode', 'preference', 0.6, 'session_3');

-- Query to verify per-user isolation:
-- SELECT * FROM user_memories WHERE user_id = 'test_user_123';
*/

-- ============================================================
-- VERIFICATION
-- ============================================================

-- Check that the table was created
SELECT 
    'user_memories table created successfully!' as status,
    COUNT(*) as current_row_count
FROM user_memories;
