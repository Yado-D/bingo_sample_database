from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, oauth2
from app import database

router = APIRouter(prefix="/game", tags=["Game End"])


@router.post("/end", status_code=status.HTTP_200_OK)
def end_game(
    payload: schemas.EndGameRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Only Jester can end games
    try:
        role = getattr(current_user.role, "value", str(current_user.role)).upper()
    except Exception:
        role = str(getattr(current_user, "role", "")).upper()

    if role != "JESTER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Jester can end a game")

    # Wallet Update: Deduct the win_amount from Jester's wallet
    current_balance = float(getattr(current_user, "wallet_balance", 0.0) or 0.0)
    win_amount = float(payload.win_amount or 0.0)

    if current_balance < win_amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance to cover the payout")

    new_balance = current_balance - win_amount
    db.query(models.User).filter(models.User.id == current_user.id).update({"wallet_balance": new_balance})

    # Save record: create GameTransaction
    try:
        tx = models.GameTransaction(
            bet_amount=payload.bet_amount,
            total_pot=payload.total_pot,
            cut_amount=payload.cut,
            winning_pattern=payload.winning_pattern,
            winner_payout=payload.win_amount,
            dedacted_amount=payload.win_amount,
            jester_id=current_user.id,
            jester_name=payload.jester_name,
            tx_date=payload.date,
            tx_time=payload.time,
            jester_remaining_balance=new_balance,
            total_balance=new_balance,
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save transaction: {e}")

    return {"status": "success", "new_balance": float(new_balance)}
