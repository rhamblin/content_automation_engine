"""
Pydantic models for request validation and response formatting.
"""

from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

# --- Keyword Schemas ---

class KeywordCreate(BaseModel):
    keyword: str

class KeywordUpdate(BaseModel):
    keyword: str

class KeywordRead(BaseModel):
    keyword_id: UUID
    keyword: str

    class Config:
        orm_mode = True

# --- Niche Schemas ---

class NicheCreate(BaseModel):
    name: str
    domain: str
    default_budget: int

class NicheUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    default_budget: Optional[int] = None

class NicheRead(BaseModel):
    niche_id: UUID
    name: str
    domain: str
    default_budget: int
    keywords: List[KeywordRead] = []

    class Config:
        orm_mode = True
