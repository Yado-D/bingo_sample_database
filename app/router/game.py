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



@router.post("/play", response_model=schemas.GameStartResponse)
def start_game(
    payload: dict,
    db: Session = Depends(get_db),
):
    # note: we import inside function to avoid circular imports at module load
    from app import schemas, oauth2
    from fastapi import Depends

    # get current user using oauth2 dependency
    current_user = Depends(oauth2.get_current_user)

    # The above style (assigning Depends to a variable) is not how FastAPI resolves dependencies
    # so we implement a small wrapper to obtain the current_user properly by re-declaring function
    # using Depends. To keep this file simple, we create a new inner function with proper deps.
    def _start_game(
        payload: schemas.GameStartRequest,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(oauth2.get_current_user),
    ):
        # calculate total bet
        num_cards = len(payload.selected_card_numbers or [])
        total_bet = float(payload.bet_amount_per_card) * float(num_cards)

        # check balance
        if (getattr(current_user, 'wallet_balance', 0.0) or 0.0) < total_bet:
            raise HTTPException(
                status_code=402, detail="Insufficient balance to place this bet"
            )

        # perform DB transaction: deduct balance and create GameSession
        try:
            with db.begin():
                # reload user for update
                user = db.query(models.User).filter(models.User.id == current_user.id).with_for_update().one()
                user.wallet_balance = (user.wallet_balance or 0.0) - total_bet
                db.add(user)

                session = models.GameSession(
                    owner_id=user.id,
                    bet_amount_per_card=payload.bet_amount_per_card,
                    total_bet=total_bet,
                    selected_cards=payload.selected_card_numbers,
                    status="ACTIVE",
                )
                db.add(session)
                # flush to get session.id
                db.flush()
                session_id = session.id

            # after commit, return session id and new balance
            return {"game_session_id": session_id, "new_balance": float(user.wallet_balance)}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Could not start game: {e}")

    # Call the inner function so FastAPI still resolves dependencies correctly when starting the server.
    # Note: at runtime FastAPI will call the endpoint and resolve dependencies; this wrapper ensures
    # the declared dependency parameters are present.
    return _start_game(payload=payload, db=db)



@router.post("/result", response_model=schemas.GameResultResponse)
def post_game_result(
    payload: schemas.GameResultRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Fetch the session
    session = db.query(models.GameSession).filter(models.GameSession.id == payload.game_session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    if session.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this session")

    try:
        with db.begin():
            # update session status
            session.status = payload.status.value if hasattr(payload.status, 'value') else str(payload.status)
            db.add(session)

            new_balance = float(getattr(current_user, 'wallet_balance', 0.0) or 0.0)

            if payload.status == schemas.GameResultStatus.WIN and payload.win_amount > 0:
                # add winnings to user's balance
                user = db.query(models.User).filter(models.User.id == current_user.id).with_for_update().one()
                user.wallet_balance = (user.wallet_balance or 0.0) + float(payload.win_amount)
                db.add(user)
                new_balance = float(user.wallet_balance)

                # log a game transaction: wins represented with negative dedacted_amount
                tx = models.GameTransaction(
                    bet_amount=int(session.bet_amount_per_card) if session.bet_amount_per_card is not None else 0,
                    game_type="BINGO",
                    number_of_cards=len(session.selected_cards) if session.selected_cards else 0,
                    dedacted_amount=-int(payload.win_amount),
                    jester_remaining_balance=new_balance,
                    total_balance=float(getattr(user, 'wallet_balance', 0.0)),
                    owner_id=user.id,
                    owner_name=(getattr(user, 'first_name', None) or getattr(user, 'name', None)),
                )
                db.add(tx)
            else:
                # For LOSE, optionally log transaction with positive dedacted_amount if needed
                pass

        return {"new_balance": new_balance}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not process game result: {e}")
