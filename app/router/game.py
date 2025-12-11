from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app import schemas, oauth2
from fastapi import Depends

router = APIRouter(prefix="/api/game", tags=["Game"])


@router.get("/cards")
def get_game_cards(db: Session = Depends(get_db)):
    """Return all bingo cards across all BingoCard entries.

    Response format:
      {"cards": [ {"cardNumber": [...], "B": [...], "I": [...], "N": [...], "G": [...], "O": [...]}, ... ]}

    On error returns 500 Internal Server Error.
    """
    try:
        bingo_cards = db.query(models.BingoCard).all()
        cards_list = []
        for bc in bingo_cards:
            data = bc.card_data or {}
            if isinstance(data, dict):
                items = data.get("cards")
                if isinstance(items, list):
                    cards_list.extend(items)

        return {"cards": cards_list}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")







@router.get("/my-transactions")
def my_game_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Jester only
    try:
        role = getattr(current_user.role, "value", str(current_user.role)).upper()
    except Exception:
        role = str(getattr(current_user, "role", "")).upper()

    if role != "JESTER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Jester can access this endpoint")

    txs = db.query(models.GameTransaction).filter(models.GameTransaction.jester_id == current_user.id).order_by(models.GameTransaction.created_at.desc()).all()

    result = []
    for t in txs:
        # compute total_pot and cut from stored fields; ensure numeric types
        total_pot = float(getattr(t, "total_pot", 0.0) or 0.0)
        cut = float(getattr(t, "cut_amount", 0.0) or 0.0)
        bet = float(getattr(t, "bet_amount", 0.0) or 0.0)
        # number_of_cards computed as total_pot / bet_amount when possible, otherwise fall back to stored value
        if bet > 0:
            try:
                number_of_cards = int(total_pot / bet)
            except Exception:
                number_of_cards = int(getattr(t, "number_of_cards", 0) or 0)
        else:
            number_of_cards = int(getattr(t, "number_of_cards", 0) or 0)

        result.append({
            "id": t.id,
            "date": t.tx_date or t.created_at,
            "time": t.tx_time,
            "game_pattern": getattr(t, "winning_pattern", None),
            "bet_amount": bet,
            "win_amount": float(getattr(t, "winner_payout", 0.0) or 0.0),
            "jester_name": t.jester_name,
            "total_pot": total_pot,
            "cut": cut,
            "number_of_cards": number_of_cards,
        })

    return {"status": "success", "data": result}




