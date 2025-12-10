from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app import models, oauth2
from app.database import get_db
from app import schemas

router = APIRouter(prefix="/api/user", tags=["API User"])


@router.get("/profile", response_model=schemas.UserProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Split name into first/last
    name = (current_user.name or "").strip()
    parts = name.split(None, 1) if name else [None, None]
    first_name = parts[0] if parts and parts[0] else None
    last_name = parts[1] if len(parts) > 1 else None

    user_id = current_user.id

    # count of game transactions for this user
    gt_count = (
        db.query(func.count(models.GameTransaction.id))
        .filter(models.GameTransaction.owner_id == user_id)
        .scalar()
    ) or 0

    # package transactions where sender or receiver is the user
    pt_count = (
        db.query(func.count(models.PackageTransaction.id))
        .filter((models.PackageTransaction.sender_id == user_id) | (models.PackageTransaction.receiver_id == user_id))
        .scalar()
    ) or 0

    total_transactions = int(gt_count) + int(pt_count)

    # total wins: count where dedacted_amount < 0
    wins_count = (
        db.query(func.count(models.GameTransaction.id))
        .filter(models.GameTransaction.owner_id == user_id)
        .filter(models.GameTransaction.dedacted_amount < 0)
        .scalar()
    ) or 0

    # total winnings: sum of -dedacted_amount where dedacted_amount < 0
    total_winnings = (
        db.query(func.coalesce(func.sum(-models.GameTransaction.dedacted_amount), 0))
        .filter(models.GameTransaction.owner_id == user_id)
        .filter(models.GameTransaction.dedacted_amount < 0)
        .scalar()
    ) or 0

    return {
        "first_name": first_name,
        "last_name": last_name,
        "wallet_balance": float(getattr(current_user, "wallet_balance", 0.0) or 0.0),
        "total_winnings": float(total_winnings),
        "total_wins_count": int(wins_count),
        "total_transactions": int(total_transactions),
    }



@router.get("/transactions", response_model=List[schemas.TransactionOut])
def get_transactions(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if page < 1:
        page = 1
    if limit < 1:
        limit = 10

    offset = (page - 1) * limit

    try:
        txs = (
            db.query(models.GameTransaction)
            .filter(models.GameTransaction.owner_id == current_user.id)
            .order_by(models.GameTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for t in txs:
            result.append(
                {
                    "date": t.created_at,
                    "game_pattern": t.game_type,
                    "bet_amount": t.bet_amount,
                    "status": "completed",
                }
            )

        return result
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch transactions",
        )
