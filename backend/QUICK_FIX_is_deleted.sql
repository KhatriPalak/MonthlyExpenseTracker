-- ========================================
-- IMMEDIATE FIX: Add is_deleted column
-- Run this in your PostgreSQL database
-- ========================================

-- Step 1: Add the is_deleted column
ALTER TABLE expense_category 
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;

-- Step 2: Update existing records to mark them as not deleted
UPDATE expense_category 
SET is_deleted = FALSE 
WHERE is_deleted IS NULL;

-- Step 3: Add index for better performance
CREATE INDEX idx_expense_category_is_deleted 
ON expense_category(is_deleted);

-- Step 4: Verify the change
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'expense_category'
ORDER BY ordinal_position;

-- Step 5: Show current categories
SELECT expense_category_id, expense_category_name, user_id, is_deleted 
FROM expense_category 
ORDER BY expense_category_id;

SELECT 'is_deleted column added successfully!' as status;
