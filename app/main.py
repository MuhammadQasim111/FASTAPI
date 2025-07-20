from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, AsyncGenerator, Optional
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field

from app import models, schemas, crud
from app.database import engine, Base, SessionLocal
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    

app = FastAPI(title="📚 Book Catalog API", lifespan=lifespan)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

@app.get("/books/", response_model=List[schemas.BookOut])
async def read_books(db: AsyncSession = Depends(get_db)):
    return await crud.get_books(db)

@app.get("/books/{book_id}", response_model=schemas.BookOut)
async def read_book(book_id: int, db: AsyncSession = Depends(get_db)):
    book = await crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.post("/books/", response_model=schemas.BookOut, status_code=201)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_book(db, book)

@app.put("/books/{book_id}", response_model=schemas.BookOut)
async def update_book(book_id: int, book: schemas.BookUpdate, db: AsyncSession = Depends(get_db)):
    updated_book = await crud.update_book(db, book_id, book)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@app.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    db_book = await crud.get_book(db, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    await crud.delete_book(db, book_id)
    return
