from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import random
import string

from src.database.connection import get_db
from src.modules.special_offers.models import SpecialOffer
from src.modules.products.models import Product
from src.modules.categories.models import Category
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
    category_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product_image = None
    if image:
        product_image = upload_file(image, "special_offers")

    parsed_category_id = None
    if category_id is not None and category_id.strip() != "":
        try:
            parsed_category_id = int(category_id)
        except Exception:
            pass

    new_product_id = None
    if parsed_category_id is not None:
        category_exists = db.query(Category).filter(Category.id == parsed_category_id).first()
        if category_exists:
            rand_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            disc_pct = 0
            if discount_amount:
                try:
                    disc_pct = int(float(discount_amount))
                except Exception:
                    pass
            elif selling_prize and discount_prize:
                try:
                    disc_pct = int(round(((selling_prize - discount_prize) / selling_prize) * 100))
                except Exception:
                    pass
            
            prod_img_path = f"/uploads/special_offers/{product_image.split('/')[-1]}" if (product_image and not product_image.startswith("http")) else product_image
            
            new_prod = Product(
                name=product_name,
                product_code=f"OFFER-{rand_code}",
                category_id=parsed_category_id,
                price=selling_prize,
                offer=disc_pct,
                stock=100,
                is_active=True,
                image_url=prod_img_path
            )
            db.add(new_prod)
            db.commit()
            db.refresh(new_prod)
            new_product_id = new_prod.id

    new_offer = SpecialOffer(
        product_name=product_name,
        selling_prize=selling_prize,
        discount_prize=discount_prize,
        discount_amount=discount_amount,
        category_id=parsed_category_id,
        product_id=new_product_id,
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
    category_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    offer = db.query(SpecialOffer).filter(SpecialOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Special Offer not found")

    parsed_category_id = offer.category_id
    if category_id is not None:
        if category_id.strip() == "":
            parsed_category_id = None
        else:
            try:
                parsed_category_id = int(category_id)
            except Exception:
                pass

    if product_name is not None:
        offer.product_name = product_name
    if selling_prize is not None:
        offer.selling_prize = selling_prize
    if discount_prize is not None:
        offer.discount_prize = discount_prize
    if discount_amount is not None:
        offer.discount_amount = discount_amount
        
    offer.category_id = parsed_category_id
    
    if image is not None and image.filename:
        offer.product_image = upload_file(image, "special_offers")

    linked_product = None
    if offer.product_id:
        linked_product = db.query(Product).filter(Product.id == offer.product_id).first()
        
    if parsed_category_id is not None:
        category_exists = db.query(Category).filter(Category.id == parsed_category_id).first()
        if category_exists:
            disc_pct = 0
            if offer.discount_amount:
                try:
                    disc_pct = int(float(offer.discount_amount))
                except Exception:
                    pass
            elif offer.selling_prize and offer.discount_prize:
                try:
                    disc_pct = int(round(((offer.selling_prize - offer.discount_prize) / offer.selling_prize) * 100))
                except Exception:
                    pass

            prod_img_path = f"/uploads/special_offers/{offer.product_image.split('/')[-1]}" if (offer.product_image and not offer.product_image.startswith("http")) else offer.product_image

            if linked_product:
                linked_product.name = offer.product_name
                linked_product.price = offer.selling_prize
                linked_product.category_id = parsed_category_id
                linked_product.offer = disc_pct
                if image is not None and image.filename:
                    linked_product.image_url = prod_img_path
                db.commit()
            else:
                rand_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                new_prod = Product(
                    name=offer.product_name,
                    product_code=f"OFFER-{rand_code}",
                    category_id=parsed_category_id,
                    price=offer.selling_prize,
                    offer=disc_pct,
                    stock=100,
                    is_active=True,
                    image_url=prod_img_path
                )
                db.add(new_prod)
                db.commit()
                db.refresh(new_prod)
                offer.product_id = new_prod.id
    else:
        if linked_product:
            db.delete(linked_product)
            db.commit()
            offer.product_id = None

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
        
    if offer.product_id:
        linked_product = db.query(Product).filter(Product.id == offer.product_id).first()
        if linked_product:
            db.delete(linked_product)
            
    db.delete(offer)
    db.commit()
    return {"status": "success", "message": "Special Offer deleted successfully"}