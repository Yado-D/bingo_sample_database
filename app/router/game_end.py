from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, oauth2
from app import database

router = APIRouter(prefix="/game", tags=["Game End"])


@router.post("/end", status_code=status.HTTP_200_OK, response_model=schemas.GameEndResponse)
def end_game(
    payload: schemas.GameEndRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Only Jester can end games
    if current_user.role.value != "JESTER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Jester can end a game")

    # try to find a matching session
    session = None
    try:
        gid_int = int(payload.game_id.split("-")[-1]) if "-" in payload.game_id else int(payload.game_id)
        session = db.query(models.GameSession).filter(models.GameSession.id == gid_int).first()
    except Exception:
        session = None

    if not session:
        # fallback: latest session for this user
        session = (
            db.query(models.GameSession)
            .filter(models.GameSession.owner_id == current_user.id)
            .order_by(models.GameSession.created_at.desc())
            .first()
        )

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    total_pot = float(session.total_pot or session.total_bet or 0.0)
    house_cut = float(session.house_cut or 0.0)
    winner_payout = total_pot - house_cut

    # Deduct payout from Jester's wallet balance
    current_balance = float(getattr(current_user, "wallet_balance", 0.0) or 0.0)
    if current_balance < winner_payout:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance to pay out winner")

    new_balance = current_balance - winner_payout
    db.query(models.User).filter(models.User.id == current_user.id).update({"wallet_balance": new_balance})

    # Log game transaction
    tx = models.GameTransaction(
        bet_amount=session.bet_amount_per_card,
        game_type="BINGO",
        number_of_cards=len(session.selected_cards) if session.selected_cards else 0,
        cut_amount=house_cut,
        winner_payout=winner_payout,
        jester_id=current_user.id,
        jester_name=(getattr(current_user, "first_name", None) or getattr(current_user, "name", None)),
        # amount deducted from the jester for paying out the winner
        dedacted_amount=winner_payout,
        jester_remaining_balance=new_balance,
        total_balance=new_balance,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return {
        "status": "success",
        "message": "Game Over. Accounts updated.",
        "data": {
            "total_pot": total_pot,
            "house_cut": house_cut,
            "winner_payout": winner_payout,
            "jester_balance_deducted": winner_payout,
            "jester_remaining_balance": new_balance,
        },
    }
