-- Migration script to add expense_name column to expense table

-- Add the expense_name column to the expense table
ALTER TABLE expense 
ADD COLUMN IF NOT EXISTS expense_name VARCHAR(200);

-- Optional: Update existing expenses to copy description to name if needed
-- UPDATE expense SET expense_name = expense_description WHERE expense_name IS NULL;

-- Verify the column was added
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'expense' 
AND column_name = 'expense_name';