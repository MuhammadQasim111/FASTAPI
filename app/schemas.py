from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import datetime

current_year = datetime.datetime.now().year

class BookBase(BaseModel):
    title: str
    author: str
    published_year: int = Field(..., ge=1000, le=current_year, description="Year between 1000 and current")
    summary: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    published_year: Optional[int] = Field(None, ge=1000, le=current_year, description="Year between 1000 and current")
    summary: Optional[str] = None

class BookOut(BookBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
