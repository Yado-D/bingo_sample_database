from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, oauth2, schemas

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
def fetch_current_user_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # basic user fields
    user_obj = {
        "id": current_user.id,
        "name": getattr(current_user, "first_name", None) or getattr(current_user, "name", None),
        "phone": getattr(current_user, "phone", None),
        "role": getattr(current_user.role, "value", str(current_user.role)),
        "city": getattr(current_user, "city", None),
        "region": getattr(current_user, "region", None),
    }

    # wallet balance
    wallet_balance = float(getattr(current_user, "wallet_balance", 0.0) or 0.0)

    # total sent and received from package transactions
    total_sent = db.query(func.coalesce(func.sum(models.PackageTransaction.package_amount), 0)).filter(models.PackageTransaction.sender_id == current_user.id).scalar() or 0.0
    total_received = db.query(func.coalesce(func.sum(models.PackageTransaction.package_amount), 0)).filter(models.PackageTransaction.receiver_id == current_user.id).scalar() or 0.0

    return {
        "user": user_obj,
        "wallet_balance": float(wallet_balance),
        "total_sent": float(total_sent),
        "total_received": float(total_received),
    }
