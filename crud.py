from sqlalchemy.orm import Session
import models, schemas
from datetime import date
from typing import List, Optional


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

# Category operations
def get_category(db: Session, category_id: int):
    return (
        db.query(models.Category).filter(models.Category.id == category_id).first()
    )

def get_user_categories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Category)
        .filter(models.Category.owner_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_user(db: Session, user: schemas.UserCreate):
    from auth import get_password_hash

    try:
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            email=user.email, username=user.username, hashed_password=hashed_password
        )

        # Add the user to the database
        db.add(db_user)
        # Commit the transaction
        db.commit()
        # Refresh the user to get the id and other generated fields
        db.refresh(db_user)
        # Return the created user
        return db_user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return None

def create_category(db: Session, category: schemas.CategoryCreate, user_id: int):
    db_category = models.Category(**category.model_dump(), owner_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(
    db: Session, category_id: int, category: schemas.CategoryCreate
):
    db_category = get_category(db, category_id=category_id)
    for key, value in category.model_dump().items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id=category_id)
    db.delete(db_category)
    db.commit()

# Expense operations
def get_expense(db: Session, expense_id: int):
    return db.query(models.Expense).filter(models.Expense.id == expense_id).first()

def get_user_expenses(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Expense)
        .filter(models.Expense.owner_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_expense(db: Session, expense: schemas.ExpenseCreate, user_id: int):
    db_expense = models.Expense(**expense.model_dump(), owner_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def update_expense(db: Session, expense_id: int, expense: schemas.ExpenseCreate):
    db_expense = get_expense(db, expense_id=expense_id)
    for key, value in expense.model_dump().items():
        setattr(db_expense, key, value)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def delete_expense(db: Session, expense_id: int):
    db_expense = get_expense(db, expense_id=expense_id)
    db.delete(db_expense)
    db.commit()


