from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import uuid

from src.database.connection import get_db
from src.modules.products.models import Product
from src.modules.categories.models import Category
from src.modules.products import schemas
from src.utils.dependencies import get_current_user, get_admin_user
from src.modules.users.models import User

router = APIRouter()

UPLOAD_DIR = "uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=schemas.AdminProductResponse)
def create_product(
    name: str = Form(...),
    product_code: Optional[str] = Form(None),
    category_id: int = Form(...),
    price: float = Form(...),
    purchase_amount: float = Form(0.0),
    offer: int = Form(0),
    stock: int = Form(0),
    short_description: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    # Check category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    image_url = None
    if image:
        from src.utils.storage import upload_file
        image_url = upload_file(image, "products")

    new_product = Product(
        name=name,
        product_code=product_code,
        category_id=category_id,
        price=price,
        purchase_amount=purchase_amount,
        offer=offer,
        stock=stock,
        short_description=short_description,
        description=description,
        is_active=is_active,
        image_url=image_url
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.post("/json/", response_model=schemas.AdminProductResponse)
def create_product_json(
    payload: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    category = db.query(Category).filter(Category.id == payload.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    new_product = Product(
        name=payload.name,
        product_code=payload.product_code,
        category_id=payload.category_id,
        price=payload.price,
        purchase_amount=payload.purchase_amount,
        offer=payload.offer,
        stock=payload.stock,
        short_description=payload.short_description,
        description=payload.description,
        is_active=payload.is_active,
        image_url=payload.image_url,
        features=payload.features,
        specs=payload.specs
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

from fastapi import Query

@router.get("/all_products/", response_model=schemas.PaginatedProductResponse)
def get_all_products(
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(8, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if sort == "latest":
        query = query.order_by(Product.created_at.desc())

    from sqlalchemy import func
    max_price_overall = db.query(func.max(Product.price)).filter(Product.is_active == True).scalar() or 0

    total_count = query.count()
    products = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "max_price_overall": max_price_overall,
        "products": products
    }

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/admin/all", response_model=List[schemas.AdminProductResponse])
def get_all_products_admin(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    return db.query(Product).order_by(Product.created_at.desc()).all()

@router.get("/admin/{product_id}", response_model=schemas.AdminProductResponse)
def get_product_admin(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.AdminProductResponse)
def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    price: Optional[float] = Form(None),
    purchase_amount: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    product_code: Optional[str] = Form(None),
    short_description: Optional[str] = Form(None),
    offer: Optional[int] = Form(None),
    features: Optional[str] = Form(None),
    specs: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if category_id is not None:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        product.category_id = category_id

    if name is not None:
        product.name = name
    if price is not None:
        product.price = price
    if purchase_amount is not None:
        product.purchase_amount = purchase_amount
    if stock is not None:
        product.stock = stock
    if description is not None:
        product.description = description
    if is_active is not None:
        product.is_active = is_active
    if product_code is not None:
        product.product_code = product_code or None
    if short_description is not None:
        product.short_description = short_description or None
    if offer is not None:
        product.offer = offer

    if features is not None:
        import json
        try:
            product.features = json.loads(features) if features else []
        except Exception:
            pass

    if specs is not None:
        import json
        try:
            product.specs = json.loads(specs) if specs else {}
        except Exception:
            pass

    if image_url is not None:
        product.image_url = image_url or None
        
    if image:
        from src.utils.storage import upload_file
        product.image_url = upload_file(image, "products")

    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
