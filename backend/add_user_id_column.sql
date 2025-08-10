-- ========================================
-- PostgreSQL Migration Script
-- Add user_id column to expense_category table
-- ========================================

-- Check current table structure (optional - for reference)
\d expense_category;

-- Step 1: Add the user_id column (nullable to allow global categories)
ALTER TABLE expense_category 
ADD COLUMN user_id INTEGER;

-- Step 2: Add foreign key constraint to reference the user table
ALTER TABLE expense_category 
ADD CONSTRAINT fk_expense_category_user 
FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE SET NULL;

-- Step 3: Add index for better performance
CREATE INDEX idx_expense_category_user_id ON expense_category(user_id);

-- Step 4: Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'expense_category' 
ORDER BY ordinal_position;

-- Step 5: Insert default categories into the table
-- Clear existing categories first (optional)
-- DELETE FROM expense_category; -- Uncomment this if you want to start fresh

-- Insert Global Categories (user_id = NULL - available to all users)
INSERT INTO expense_category (expense_category_name, user_id) VALUES
('Food & Dining', NULL),
('Transportation', NULL),
('Shopping', NULL),
('Entertainment', NULL),
('Bills & Utilities', NULL),
('Healthcare', NULL),
('Travel', NULL),
('Education', NULL),
('Personal Care', NULL),
('Groceries', NULL),
('Other', NULL);

-- Insert User-Specific Categories for User ID 1 (example)
INSERT INTO expense_category (expense_category_name, user_id) VALUES
('Personal Projects', 1),
('Gym Membership', 1),
('Coffee & Snacks', 1);

-- Step 6: Show current data
SELECT expense_category_id, expense_category_name, user_id 
FROM expense_category 
ORDER BY user_id NULLS FIRST, expense_category_name;

-- Success message
SELECT 'Migration completed successfully! user_id column added to expense_category table.' as status;
