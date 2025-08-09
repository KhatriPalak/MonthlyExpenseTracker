from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import Expense

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/expenses")
def add_expense():
    # Implement expense creation logic
    pass

@router.get("/expenses")
def get_expenses():
    # Retrieve all expenses and validate fields to avoid NoneType errors
    from fastapi import HTTPException
    db = next(get_db())
    expenses = db.query(Expense).all()
    result = []
    for exp in expenses:
        # Validate fields before conversion
        if exp.expense_id is None or exp.user_id is None or exp.expense_item_price is None or exp.expense_category_id is None or exp.expenditure_date is None:
            continue  # skip invalid records
        result.append({
            "expense_id": int(exp.expense_id),
            "user_id": int(exp.user_id),
            "expense_item_price": float(exp.expense_item_price),
            "expense_category_id": int(exp.expense_category_id),
            "expense_description": exp.expense_description or "",
            "expense_item_count": int(exp.expense_item_count) if exp.expense_item_count is not None else 1,
            "expenditure_date": exp.expenditure_date.isoformat()
        })
    if not result:
        raise HTTPException(status_code=404, detail="No expenses found or invalid data.")
    return result
