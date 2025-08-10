-- ========================================
-- PostgreSQL UPDATE Script
-- Update existing expense_category records with user_id values
-- ========================================

-- First, let's see what categories currently exist
SELECT expense_category_id, expense_category_name, user_id 
FROM expense_category 
ORDER BY expense_category_id;

-- Update existing categories to assign them to specific users
-- You can modify these UPDATE statements based on your needs

-- Option 1: Make all existing categories global (user_id = NULL)
UPDATE expense_category SET user_id = NULL;

-- Option 2: Assign specific categories to specific users
-- UPDATE expense_category SET user_id = 1 WHERE expense_category_name IN ('Groceries', 'Utilities');
-- UPDATE expense_category SET user_id = 2 WHERE expense_category_name IN ('Entertainment');
-- UPDATE expense_category SET user_id = NULL WHERE expense_category_name NOT IN ('Groceries', 'Utilities', 'Entertainment');

-- Option 3: Assign all existing categories to user ID 1
-- UPDATE expense_category SET user_id = 1;

-- Verify the updates
SELECT expense_category_id, expense_category_name, user_id 
FROM expense_category 
ORDER BY user_id NULLS FIRST, expense_category_name;

-- Show summary of categories by user
SELECT 
    CASE 
        WHEN user_id IS NULL THEN 'Global Categories' 
        ELSE CONCAT('User ', user_id, ' Categories')
    END as category_type,
    COUNT(*) as count
FROM expense_category 
GROUP BY user_id 
ORDER BY user_id NULLS FIRST;
