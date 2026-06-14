from fastapi import APIRouter, Depends
from src.utils.dependencies import get_current_user
from src.modules.users.models import User

router = APIRouter()

@router.get("/profile/")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "address": current_user.address,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
    }
