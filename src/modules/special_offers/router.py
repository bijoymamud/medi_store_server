from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.connection import get_db
from src.modules.special_offers.models import SpecialOffer
from src.modules.special_offers import schemas
from src.utils.dependencies import get_admin_user
from src.modules.users.models import User
from src.utils.storage import upload_file

router = APIRouter()

@router.post("/", response_model=schemas.SpecialOfferResponse)
def create_special_offer(
    product_name: str = Form(...),
    selling_prize: float = Form(...),
    discount_prize: Optional[float] = Form(None),
    discount_amount: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product_image = None
    if image:
        product_image = upload_file(image, "special_offers")

    new_offer = SpecialOffer(
        product_name=product_name,
        selling_prize=selling_prize,
        discount_prize=discount_prize,
        discount_amount=discount_amount,
        product_image=product_image
    )
    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)
    return new_offer

@router.get("/", response_model=List[schemas.SpecialOfferResponse])
def get_special_offers(db: Session = Depends(get_db)):
    return db.query(SpecialOffer).order_by(SpecialOffer.created_at.desc()).all()

@router.put("/{offer_id}", response_model=schemas.SpecialOfferResponse)
def update_special_offer(
    offer_id: int,
    product_name: Optional[str] = Form(None),
    selling_prize: Optional[float] = Form(None),
    discount_prize: Optional[float] = Form(None),
    discount_amount: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    offer = db.query(SpecialOffer).filter(SpecialOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Special Offer not found")
        
    if product_name is not None:
        offer.product_name = product_name
    if selling_prize is not None:
        offer.selling_prize = selling_prize
    if discount_prize is not None:
        offer.discount_prize = discount_prize
    if discount_amount is not None:
        offer.discount_amount = discount_amount
    if image is not None and image.filename:
        offer.product_image = upload_file(image, "special_offers")
        
    db.commit()
    db.refresh(offer)
    return offer

@router.delete("/{offer_id}")
def delete_special_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    offer = db.query(SpecialOffer).filter(SpecialOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Special Offer not found")
        
    db.delete(offer)
    db.commit()
    return {"status": "success", "message": "Special Offer deleted successfully"}