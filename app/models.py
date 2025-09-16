from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Csv_input(Base):
    """name,role,company,industry,location,linkedin_bio"""
    __tablename__ = "csv_inputs"

    id = Column(Integer,primary_key=True)
    name = Column(String(50),nullable=True)
    role = Column(String(50),nullable=True)
    company = Column(String(50),nullable=True)
    industry = Column(String(50),nullable=True)
    location = Column(String(50),nullable=True)
    linkedin_bio = Column(String(255), nullable=True)

class Offer(Base):

    __tablename__ = "offers"
    id = Column(Integer,primary_key=True)
    name = Column(String(50),nullable = True)
    value_props = Column(JSON, nullable=True)    
    ideal_use_cases = Column(JSON, nullable=True) 


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("csv_inputs.id"), nullable=False)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)

    intent = Column(String(50))
    score = Column(Integer)
    reasoning = Column(String(250))

    # relationships
    lead = relationship("Csv_input", backref="results")
    offer = relationship("Offer", backref="results")

Base.metadata.create_all(bind=engine)