from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas

async def get_books(db: AsyncSession):
    result = await db.execute(select(models.Book))
    return result.scalars().all()

async def get_book(db: AsyncSession, book_id: int):
    result = await db.execute(select(models.Book).where(models.Book.id == book_id))
    return result.scalar_one_or_none()

async def create_book(db: AsyncSession, book: schemas.BookCreate):
    new_book = models.Book(**book.model_dump())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

async def update_book(db: AsyncSession, book_id: int, book_data: schemas.BookUpdate):
    db_book = await get_book(db, book_id)
    if not db_book:
        return None
    
    update_data = book_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    await db.commit()
    await db.refresh(db_book)
    return db_book

async def delete_book(db: AsyncSession, book_id: int):
    db_book = await get_book(db, book_id)
    if not db_book:
        return None
    await db.delete(db_book)
    await db.commit()
    return db_book
