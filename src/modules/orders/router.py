import os
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.connection import get_db
from src.modules.orders import schemas, models
from src.modules.cart.models import Cart, CartItem
from src.modules.products.models import Product
from src.modules.users.models import User
from src.utils.dependencies import get_current_user, get_admin_user

router = APIRouter()

async def initiate_sslcommerz_payment(
    amount: float, 
    tran_id: str, 
    customer_name: str, 
    customer_email: str, 
    customer_phone: str, 
    customer_address: str
) -> str:
    store_id = os.getenv("SSLCOMMERZ_STORE_ID", "testbox")
    store_pass = os.getenv("SSLCOMMERZ_STORE_PASS", "testbox@ssl")
    is_sandbox = os.getenv("SSLCOMMERZ_IS_SANDBOX", "true").lower() == "true"
    
    url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php" if is_sandbox else "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
    backend_url = os.getenv("BACKEND_URL", "http://localhost:5000")
    
    payload = {
        "store_id": store_id,
        "store_passwd": store_pass,
        "total_amount": f"{amount:.2f}",
        "currency": "BDT",
        "tran_id": tran_id,
        "success_url": f"{backend_url}/api/v1/orders/payment/success",
        "fail_url": f"{backend_url}/api/v1/orders/payment/fail",
        "cancel_url": f"{backend_url}/api/v1/orders/payment/cancel",
        "product_category": "healthcare",
        "product_name": "MediStore Order",
        "product_profile": "general",
        "cus_name": customer_name or "Guest",
        "cus_email": customer_email or "guest@example.com",
        "cus_add1": customer_address or "Not Provided",
        "cus_city": "Dhaka",
        "cus_country": "Bangladesh",
        "cus_phone": customer_phone or "01700000000",
        "shipping_method": "NO",
        "num_of_item": "1",
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=payload, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "SUCCESS":
                    return data.get("GatewayPageURL")
                else:
                    print(f"SSLCommerz API error response: {data}")
            else:
                print(f"SSLCommerz returned status code {response.status_code}")
        except Exception as e:
            print(f"Failed to connect to SSLCommerz API: {e}")
            
    return None

async def verify_sslcommerz_payment(val_id: str) -> bool:
    store_id = os.getenv("SSLCOMMERZ_STORE_ID", "testbox")
    store_pass = os.getenv("SSLCOMMERZ_STORE_PASS", "testbox@ssl")
    is_sandbox = os.getenv("SSLCOMMERZ_IS_SANDBOX", "true").lower() == "true"
    
    url = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php" if is_sandbox else "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"
    
    params = {
        "val_id": val_id,
        "store_id": store_id,
        "store_passwd": store_pass,
        "format": "json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["VALID", "VALIDATED"]:
                    return True
                print(f"Validation API status: {data.get('status')}, details: {data}")
        except Exception as e:
            print(f"Failed to validate payment: {e}")
            
    return False

@router.post("/checkout", response_model=schemas.OrderResponse)
async def checkout(
    payload: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    # 2. Validate product stock and compute total
    total_amount = 0.0
    items_to_create = []
    
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {product.name}")
            
        price = product.price
        total_amount += price * item.quantity
        
        items_to_create.append((product, item.quantity, price))
        
    # 3. Create unique transaction ID
    tran_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    
    # 4. Create Order
    new_order = models.Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=payload.shipping_address,
        phone=payload.phone,
        payment_method=payload.payment_method,
        transaction_id=tran_id,
        status="pending",
        payment_status="pending",
        review_status="requested",
        prepaid_method=payload.prepaid_method if payload.payment_method == "cod_prepaid" else None,
        prepaid_number=payload.prepaid_number if payload.payment_method == "cod_prepaid" else None,
        prepaid_txid=payload.prepaid_txid if payload.payment_method == "cod_prepaid" else None,
        recipient_name=payload.recipient_name,
        recipient_email=payload.recipient_email
    )
    db.add(new_order)
    db.flush()
    
    # 5. Create OrderItems & deduct stock
    for product, quantity, price in items_to_create:
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=quantity,
            price=price
        )
        db.add(order_item)
        product.stock -= quantity
    
    # 6. Clear the cart items
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    
    # 7. Commit database transaction (releasing row locks and connection slot)
    db.commit()
    db.refresh(new_order)
    
    # 8. Payment Integration processing (performed OUTSIDE database transaction)
    payment_url = None
    
    if payload.payment_method == "sslcommerz":
        payment_url = await initiate_sslcommerz_payment(
            amount=total_amount,
            tran_id=tran_id,
            customer_name=current_user.full_name,
            customer_email=current_user.email,
            customer_phone=payload.phone,
            customer_address=payload.shipping_address
        )
        if not payment_url:
            # Revert inventory stock and mark order as failed in a new short-lived transaction
            try:
                order_to_fail = db.query(models.Order).filter(models.Order.id == new_order.id).first()
                if order_to_fail:
                    order_to_fail.status = "cancelled"
                    order_to_fail.payment_status = "failed"
                    for item in order_to_fail.items:
                        product = db.query(Product).filter(Product.id == item.product_id).first()
                        if product:
                            product.stock += item.quantity
                    db.commit()
                    db.refresh(new_order)
            except Exception as revert_err:
                print(f"Failed to reverse stock changes after payment failure: {revert_err}")
                
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to initialize SSLCommerz payment session. Please check your configurations or network."
            )
            
    # Map to response schema
    response_obj = schemas.OrderResponse.model_validate(new_order)
    
    response_dict = response_obj.model_dump()
    response_dict["payment_url"] = payment_url
    
    return schemas.OrderResponse(**response_dict)

@router.get("/", response_model=List[schemas.OrderResponse])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).order_by(models.Order.created_at.desc()).all()
    return orders

@router.get("/admin/analytics")
def get_admin_analytics(db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    from sqlalchemy import func
    total_revenue = db.query(func.coalesce(func.sum(models.Order.total_amount), 0.0)).filter(
        (models.Order.payment_status == "paid") | (models.Order.status == "completed")
    ).scalar()

    total_orders = db.query(func.count(models.Order.id)).scalar()

    total_running_orders = db.query(func.count(models.Order.id)).filter(
        models.Order.status.in_(["pending", "on_route"])
    ).scalar()

    current_inventory_cost = db.query(func.coalesce(func.sum(Product.stock * Product.purchase_amount), 0.0)).scalar()
    
    sold_inventory_cost = db.query(
        func.coalesce(func.sum(models.OrderItem.quantity * Product.purchase_amount), 0.0)
    ).join(
        Product, models.OrderItem.product_id == Product.id
    ).join(
        models.Order, models.OrderItem.order_id == models.Order.id
    ).filter(
        (models.Order.payment_status == "paid") | (models.Order.status == "completed")
    ).scalar()

    total_investment = current_inventory_cost + sold_inventory_cost

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_running_orders": total_running_orders,
        "total_investment": total_investment
    }


@router.get("/admin/all", response_model=List[schemas.OrderResponse])
def list_all_orders_admin(db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()
    return orders


@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order_detail(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
        
    return order

@router.post("/{order_id}/pay-success", response_model=schemas.OrderResponse)
def mark_payment_success(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
        
    order.payment_status = "paid"
    db.commit()
    db.refresh(order)
    return order

@router.patch("/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(
    order_id: int,
    payload: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order

@router.post("/payment/success")
@router.get("/payment/success")
async def payment_success(request: Request, db: Session = Depends(get_db)):
    params = {}
    if request.method == "POST":
        form_data = await request.form()
        params = dict(form_data)
    else:
        params = dict(request.query_params)
        
    tran_id = params.get("tran_id")
    val_id = params.get("val_id")
    
    if not tran_id:
        raise HTTPException(status_code=400, detail="Missing transaction ID")
        
    order = db.query(models.Order).filter(models.Order.transaction_id == tran_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    is_testbox = os.getenv("SSLCOMMERZ_STORE_ID", "testbox") == "testbox"
    
    verified = False
    if val_id:
        verified = await verify_sslcommerz_payment(val_id)
        
    if verified or is_testbox or not val_id:
        order.payment_status = "paid"
        db.commit()
        return RedirectResponse(url=f"{frontend_url}/order/success?order_id={order.id}", status_code=303)
    else:
        order.payment_status = "failed"
        db.commit()
        return RedirectResponse(url=f"{frontend_url}/order/failed?order_id={order.id}", status_code=303)

@router.post("/payment/fail")
@router.get("/payment/fail")
async def payment_fail(request: Request, db: Session = Depends(get_db)):
    params = {}
    if request.method == "POST":
        form_data = await request.form()
        params = dict(form_data)
    else:
        params = dict(request.query_params)
        
    tran_id = params.get("tran_id")
    if tran_id:
        order = db.query(models.Order).filter(models.Order.transaction_id == tran_id).first()
        if order:
            order.payment_status = "failed"
            db.commit()
            
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}/order/failed", status_code=303)

@router.post("/payment/cancel")
@router.get("/payment/cancel")
async def payment_cancel(request: Request, db: Session = Depends(get_db)):
    params = {}
    if request.method == "POST":
        form_data = await request.form()
        params = dict(form_data)
    else:
        params = dict(request.query_params)
        
    tran_id = params.get("tran_id")
    if tran_id:
        order = db.query(models.Order).filter(models.Order.transaction_id == tran_id).first()
        if order:
            order.status = "cancelled"
            order.payment_status = "failed"
            db.commit()
            
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}/cart", status_code=303)

@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {"status": "success", "message": "Order deleted successfully"}

@router.post("/{order_id}/approve", response_model=schemas.OrderResponse)
def approve_order(order_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = "on_route"
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/reject", response_model=schemas.OrderResponse)
def reject_order(order_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/submit-review", response_model=schemas.OrderResponse)
def submit_review(
    order_id: int, 
    payload: schemas.ReviewSubmitRequest,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to submit review for this order")
        
    if order.status != "on_route":
        raise HTTPException(status_code=400, detail="Reviews can only be submitted for orders on route")
        
    if order.review_status not in ["requested", "rejected"]:
        raise HTTPException(status_code=400, detail="A review has already been submitted or verified for this order")
        
    from sqlalchemy.sql import func
    order.review_text = payload.review_text
    order.review_rating = payload.review_rating
    order.review_status = "submitted"
    order.review_submitted_at = func.now()
    
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/verify-review", response_model=schemas.OrderResponse)
def verify_review(
    order_id: int,
    payload: schemas.ReviewVerifyRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.review_status != "submitted":
        raise HTTPException(status_code=400, detail="No review submitted to verify")
        
    if payload.is_valid:
        order.review_status = "verified"
        order.status = "completed"
    else:
        order.review_status = "rejected"
        
    db.commit()
    db.refresh(order)
    return order

