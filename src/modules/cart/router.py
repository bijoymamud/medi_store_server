from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.modules.cart import schemas, models
from src.modules.products.models import Product
from src.modules.users.models import User
from src.utils.dependencies import get_current_user

router = APIRouter()

def get_or_create_cart(db: Session, user_id: int) -> models.Cart:
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        cart = models.Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def format_cart_response(cart: models.Cart, db: Session) -> schemas.CartResponse:
    items_response = []
    total_price = 0.0
    
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            subtotal = product.price * item.quantity
            total_price += subtotal
            items_response.append(schemas.CartItemResponse(
                id=item.id,
                product_id=product.id,
                product_name=product.name,
                product_price=product.price,
                product_image=product.image_url,
                quantity=item.quantity,
                subtotal=subtotal
            ))
            
    return schemas.CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=items_response,
        total_price=total_price
    )

@router.get("/", response_model=schemas.CartResponse)
def get_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, current_user.id)
    return format_cart_response(cart, db)

@router.post("/items/", response_model=schemas.CartResponse)
def add_to_cart(
    payload: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    cart = get_or_create_cart(db, current_user.id)
    
    existing_item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.product_id == payload.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += payload.quantity
    else:
        new_item = models.CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            quantity=payload.quantity
        )
        db.add(new_item)
        
    db.commit()
    db.refresh(cart)
    return format_cart_response(cart, db)

@router.put("/items/{item_id}", response_model=schemas.CartResponse)
def update_cart_item(
    item_id: int,
    payload: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = get_or_create_cart(db, current_user.id)
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.cart_id == cart.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
        
    if payload.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = payload.quantity
        
    db.commit()
    db.refresh(cart)
    return format_cart_response(cart, db)

@router.delete("/items/{item_id}", response_model=schemas.CartResponse)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = get_or_create_cart(db, current_user.id)
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.cart_id == cart.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
        
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return format_cart_response(cart, db)

@router.delete("/")
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if cart:
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        db.commit()
    return {"message": "Cart cleared successfully"}
