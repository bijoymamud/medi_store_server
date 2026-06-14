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

@router.post("/", response_model=schemas.ProductResponse)
def create_product(
    name: str = Form(...),
    category_id: int = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
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
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/uploads/products/{file_name}"

    new_product = Product(
        name=name,
        category_id=category_id,
        price=price,
        stock=stock,
        description=description,
        is_active=is_active,
        image_url=image_url
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    db.refresh(new_product)
    return new_product

@router.post("/json/", response_model=schemas.ProductResponse)
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
        category_id=payload.category_id,
        price=payload.price,
        stock=payload.stock,
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

@router.get("/all_products/", response_model=List[schemas.ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    # Used by frontend
    return db.query(Product).all()

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
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
    if stock is not None:
        product.stock = stock
    if description is not None:
        product.description = description
    if is_active is not None:
        product.is_active = is_active
        
    if image:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        product.image_url = f"/uploads/products/{file_name}"

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
