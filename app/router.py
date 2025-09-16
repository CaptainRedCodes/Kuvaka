import csv
import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.services.scoring import Scoring
from .models import Csv_input, Offer, Result, get_db
from .schemas import CsvResponse, OfferCreate, OfferResponse, ResultResponse

router = APIRouter()


@router.post("/offer", response_model=OfferResponse)
async def create_offer(offer: OfferCreate, db: Session = Depends(get_db)):
    """
    Create a new offer in the database.
    - Rejects if an offer with the same name already exists.
    """
    existing = db.query(Offer).filter(Offer.name == offer.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Offer already exists")

    db_offer = Offer(
        name=offer.name,
        value_props=offer.value_props,
        ideal_use_cases=offer.ideal_use_cases,
    )
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)

    return {"name": offer.name, "message": "Uploaded successfully"}


@router.post("/upload", response_model=CsvResponse)
async def upload_leads(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload leads from a CSV file.
    - Clears all existing leads and results before inserting new data.
    - File must be a `.csv`.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Clear old data before inserting new leads
    db.query(Result).delete()
    db.query(Csv_input).delete()
    db.commit()

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

    count = 0
    for row in reader:
        lead = Csv_input(
            name=row.get("name", ""),
            role=row.get("role", ""),
            company=row.get("company", ""),
            industry=row.get("industry", ""),
            location=row.get("location", ""),
            linkedin_bio=row.get("linkedin_bio", ""),
        )
        db.add(lead)
        count += 1

    db.commit()
    return {"message": f"{count} leads uploaded successfully. Previous data cleared."}


@router.post("/score", response_model=OfferResponse)
async def score_leads(offer_name: str, db: Session = Depends(get_db)):
    """
    Score all uploaded leads for a given offer.
    - Clears existing results for the offer before scoring.
    - Uses bulk scoring for better performance.
    """
    offer = db.query(Offer).filter(Offer.name == offer_name).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Remove previous results for this offer
    db.query(Result).filter(Result.offer_id == offer.id).delete()
    db.commit()

    all_leads = db.query(Csv_input).all()
    if not all_leads:
        return {
            "name": offer.name,
            "value_props": offer.value_props,
            "ideal_use_cases": offer.ideal_use_cases,
            "message": f"No leads found to score for offer '{offer_name}'.",
        }

    # Convert leads to dictionaries
    leads_dict = [
        {
            "id": lead.id,
            "name": lead.name,
            "role": lead.role,
            "company": lead.company,
            "industry": lead.industry,
            "location": lead.location,
            "linkedin_bio": lead.linkedin_bio,
        }
        for lead in all_leads
    ]

    # Offer details
    offer_dict = {
        "name": offer.name,
        "value_props": offer.value_props or [],
        "ideal_use_cases": offer.ideal_use_cases or [],
    }

    # Run bulk scoring
    scoring = Scoring()
    scoring_results = scoring.final_score_bulk(leads_dict, offer_dict)

    # Save results
    scored_count = 0
    for i, (intent, total_score, reasoning) in enumerate(scoring_results):
        scored_lead = Result(
            lead_id=leads_dict[i]["id"],
            offer_id=offer.id,
            intent=intent,
            score=total_score,
            reasoning=reasoning,
        )
        db.add(scored_lead)
        scored_count += 1

    db.commit()

    return {
        "name": offer.name,
        "value_props": offer.value_props,
        "ideal_use_cases": offer.ideal_use_cases,
        "message": f"Scored {scored_count} leads for offer '{offer_name}'. Previous results cleared.",
    }


@router.get("/results", response_model=List[ResultResponse])
async def get_results(offer_name: str, db: Session = Depends(get_db)):
    """
    Fetch all scored results for a given offer.
    """
    offer = db.query(Offer).filter(Offer.name == offer_name).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    results = db.query(Result).filter(Result.offer_id == offer.id).all()

    return [
        ResultResponse(
            name=r.lead.name,
            role=r.lead.role,
            company=r.lead.company,
            intent=r.intent,
            score=r.score,
            reasoning=r.reasoning,
        )
        for r in results
    ]


@router.get("/download")
async def download_csv(offer_name: str, db: Session = Depends(get_db)):
    """
    Download results for a given offer as a CSV file.
    - CSV includes: [name, role, company, industry, location, intent, score, reasoning]
    """
    offer = db.query(Offer).filter(Offer.name == offer_name).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    results = db.query(Result).filter(Result.offer_id == offer.id).all()
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this offer")

    # Write results to in-memory CSV
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        ["name", "role", "company", "industry", "location", "intent", "score", "reasoning"]
    )

    for r in results:
        writer.writerow(
            [
                r.lead.name,
                r.lead.role,
                r.lead.company,
                r.lead.industry,
                r.lead.location,
                r.intent,
                r.score,
                r.reasoning,
            ]
        )

    output = stream.getvalue()
    stream.close()

    return StreamingResponse(
        io.StringIO(output),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={offer_name}_results.csv"},
    )
