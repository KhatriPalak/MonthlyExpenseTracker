-- ========================================
-- PostgreSQL Migration Script
-- Add is_deleted column to expense_category table
-- ========================================

-- Check current table structure (optional - for reference)
\d expense_category;

-- Step 1: Add the is_deleted column (default FALSE for existing records)
ALTER TABLE expense_category 
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;

-- Step 2: Update any existing records to ensure they are marked as not deleted
UPDATE expense_category SET is_deleted = FALSE WHERE is_deleted IS NULL;

-- Step 3: Add index for better performance on is_deleted queries
CREATE INDEX idx_expense_category_is_deleted ON expense_category(is_deleted);

-- Step 4: Add composite index for user_id and is_deleted queries
CREATE INDEX idx_expense_category_user_id_is_deleted ON expense_category(user_id, is_deleted);

-- Step 5: Remove the old unique constraint on expense_category_name (if it exists)
-- This allows for soft-deleted categories to have the same name as active ones
-- Note: You may need to check if this constraint exists first
-- ALTER TABLE expense_category DROP CONSTRAINT IF EXISTS expense_category_expense_category_name_key;

-- Step 6: Add a new unique constraint that only applies to non-deleted categories for the same user
-- This prevents duplicate active categories for the same user
CREATE UNIQUE INDEX idx_expense_category_unique_active 
ON expense_category(expense_category_name, user_id) 
WHERE is_deleted = FALSE;

-- Step 7: Also create a unique constraint for global categories (user_id IS NULL)
CREATE UNIQUE INDEX idx_expense_category_unique_global_active 
ON expense_category(expense_category_name) 
WHERE user_id IS NULL AND is_deleted = FALSE;

-- Step 8: Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'expense_category' 
ORDER BY ordinal_position;

-- Step 9: Show sample data
SELECT expense_category_id, expense_category_name, user_id, is_deleted 
FROM expense_category 
ORDER BY user_id NULLS FIRST, expense_category_name 
LIMIT 10;

-- Step 10: Show indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'expense_category'
ORDER BY indexname;

SELECT 'Migration completed successfully! is_deleted column added to expense_category table.' as status;
