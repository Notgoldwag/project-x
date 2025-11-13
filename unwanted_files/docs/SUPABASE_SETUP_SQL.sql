-- ============================================
-- SUPABASE DATABASE SETUP FOR PROMPT INJECTION
-- ============================================

-- This file contains SQL commands to set up your Supabase database
-- for the Prompt Injection feature integration

-- ============================================
-- 1. CREATE INJECTIONS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS "Injections" (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    risk FLOAT NOT NULL CHECK (risk >= 0 AND risk <= 100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_injections_user_id ON "Injections"(user_id);
CREATE INDEX IF NOT EXISTS idx_injections_created_at ON "Injections"(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_injections_risk ON "Injections"(risk);

-- ============================================
-- 2. UPDATE USERS TABLE
-- ============================================

-- Add columns to existing Users table
ALTER TABLE "Users" 
ADD COLUMN IF NOT EXISTS promptsanalyzed INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS threatsblocked INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS successrate INTEGER DEFAULT 100;

-- Add constraint to ensure valid values
ALTER TABLE "Users" 
ADD CONSTRAINT check_promptsanalyzed_positive CHECK (promptsanalyzed >= 0),
ADD CONSTRAINT check_threatsblocked_positive CHECK (threatsblocked >= 0),
ADD CONSTRAINT check_successrate_range CHECK (successrate >= 0 AND successrate <= 100);

-- ============================================
-- 3. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on Injections table
ALTER TABLE "Injections" ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own injections
CREATE POLICY "Users can read own injections"
ON "Injections"
FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can only insert their own injections
CREATE POLICY "Users can insert own injections"
ON "Injections"
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only delete their own injections
CREATE POLICY "Users can delete own injections"
ON "Injections"
FOR DELETE
USING (auth.uid() = user_id);

-- Enable RLS on Users table (if not already enabled)
ALTER TABLE "Users" ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own data
CREATE POLICY "Users can read own data"
ON "Users"
FOR SELECT
USING (auth.uid() = id);

-- Policy: Users can update their own data
CREATE POLICY "Users can update own data"
ON "Users"
FOR UPDATE
USING (auth.uid() = id);

-- ============================================
-- 4. HELPFUL VIEWS (OPTIONAL)
-- ============================================

-- View: User injection statistics
CREATE OR REPLACE VIEW user_injection_stats AS
SELECT 
    user_id,
    COUNT(*) as total_injections,
    AVG(risk) as avg_risk,
    MAX(risk) as max_risk,
    MIN(risk) as min_risk,
    COUNT(CASE WHEN risk >= 60 THEN 1 END) as high_risk_count,
    MAX(created_at) as last_injection_at
FROM "Injections"
GROUP BY user_id;

-- View: Recent injections (last 50 per user)
CREATE OR REPLACE VIEW recent_injections AS
SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
    FROM "Injections"
) ranked
WHERE rn <= 50;

-- ============================================
-- 5. USEFUL QUERIES
-- ============================================

-- Query: Get user's injection history (last 50)
-- SELECT * FROM "Injections" 
-- WHERE user_id = auth.uid() 
-- ORDER BY created_at DESC 
-- LIMIT 50;

-- Query: Get user stats
-- SELECT promptsanalyzed, threatsblocked, successrate 
-- FROM "Users" 
-- WHERE id = auth.uid();

-- Query: Count high-risk injections
-- SELECT COUNT(*) as high_risk_count 
-- FROM "Injections" 
-- WHERE user_id = auth.uid() AND risk >= 60;

-- ============================================
-- 6. CLEANUP QUERIES (USE WITH CAUTION)
-- ============================================

-- Delete all injections for a specific user
-- DELETE FROM "Injections" WHERE user_id = 'YOUR_USER_ID';

-- Reset user stats
-- UPDATE "Users" 
-- SET promptsanalyzed = 0, threatsblocked = 0, successrate = 100 
-- WHERE id = 'YOUR_USER_ID';

-- Drop all injection-related objects (DANGEROUS - USE ONLY FOR TESTING)
-- DROP VIEW IF EXISTS user_injection_stats CASCADE;
-- DROP VIEW IF EXISTS recent_injections CASCADE;
-- DROP TABLE IF EXISTS "Injections" CASCADE;

-- ============================================
-- 7. VERIFICATION QUERIES
-- ============================================

-- Check if tables exist
-- SELECT table_name 
-- FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('Injections', 'Users');

-- Check if columns exist in Users table
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'Users' 
-- AND column_name IN ('promptsanalyzed', 'threatsblocked', 'successrate');

-- Check RLS policies
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
-- FROM pg_policies 
-- WHERE tablename IN ('Injections', 'Users');

-- ============================================
-- NOTES
-- ============================================

-- 1. Make sure to run these commands in your Supabase SQL Editor
-- 2. Test RLS policies after setup to ensure security
-- 3. The Users table should already exist from your previous setup
-- 4. Back up your database before running ALTER TABLE commands
-- 5. Test with a non-admin user to verify RLS policies work

-- ============================================
-- EXAMPLE TEST DATA (OPTIONAL)
-- ============================================

-- Insert test injection (replace YOUR_USER_ID)
-- INSERT INTO "Injections" (user_id, prompt, risk)
-- VALUES ('YOUR_USER_ID', 'Test injection prompt', 75.5);

-- Update test user stats (replace YOUR_USER_ID)
-- UPDATE "Users" 
-- SET promptsanalyzed = 10, threatsblocked = 3, successrate = 70
-- WHERE id = 'YOUR_USER_ID';
