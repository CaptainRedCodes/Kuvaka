from sqlalchemy import (
    Column, ForeignKey, Integer, String, JSON
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Provides a database session to FastAPI endpoints.
    Ensures the session is closed after the request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Csv_input(Base):
    """
    Stores uploaded leads from CSV.
    Columns:
        - name, role, company, industry, location, linkedin_bio
    """
    __tablename__ = "csv_inputs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=True)
    role = Column(String(50), nullable=True)
    company = Column(String(50), nullable=True)
    industry = Column(String(50), nullable=True)
    location = Column(String(50), nullable=True)
    linkedin_bio = Column(String(255), nullable=True)


class Offer(Base):
    """
    Stores Offer information.
    Columns:
        - name: Offer name
        - value_props: List of value propositions (JSON)
        - ideal_use_cases: List of ideal use cases (JSON)
    """
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    value_props = Column(JSON, nullable=True)
    ideal_use_cases = Column(JSON, nullable=True)


class Result(Base):
    """
    Stores Scoring Results.
    Links a Lead (Csv_input) with an Offer.
    Columns:
        - intent: Lead intent (High/Medium/Low)
        - score: Numeric score
        - reasoning: Explanation of score
    Relationships:
        - lead -> Csv_input
        - offer -> Offer
    """
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("csv_inputs.id"), nullable=False)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)

    intent = Column(String(50), nullable=True)
    score = Column(Integer, nullable=True)
    reasoning = Column(String(250), nullable=True)

    # Relationships
    lead = relationship("Csv_input", backref="results")
    offer = relationship("Offer", backref="results")


# Automatically creates tables (only for dev/test use)
Base.metadata.create_all(bind=engine)
