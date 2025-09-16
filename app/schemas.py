from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class CsvBase(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=50)
    linkedin_bio: Optional[HttpUrl] = None

class CsvCreate(CsvBase):
    pass

class CsvResponse(BaseModel):
    message:str

    class Config:
        orm_mode = True

class OfferBase(BaseModel):
    name: Optional[str]
    value_props: Optional[List[str]]
    ideal_use_cases: Optional[List[str]]

class OfferCreate(OfferBase):
    pass

class OfferResponse(BaseModel):
    name: str
    message: str

    class Config:
        orm_mode = True

class ResultCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=50)

class ResultResponse(ResultCreate):
    intent: str = Field(..., max_length=50)
    score: int = Field(..., ge=0)
    reasoning: str 

    class Config:
        orm_mode = True
