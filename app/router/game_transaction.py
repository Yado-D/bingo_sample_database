from fastapi import APIRouter, Depends, HTTPException, status
from .. import models, oauth2, schemas
from sqlalchemy.orm import Session
from .. import database, models

router = APIRouter(tags=["Game Transaction"], prefix="/gamet")


# "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJyb2xlIjoibWFuYWdlciIsImV4cCI6MTc0NDE0NDc3Mn0.MRk9JAZPXNKNx_qwvyK7f1yupWO19f5dYY66phSJPwY"
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_game_transaction(
    game_transaction: schemas.GameTransactionModel,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    remain_balance = (
        db.query(models.User)
        .filter(models.User.id == current_user.id)
        .first()
        .wallet_balance
    )

    if remain_balance < game_transaction.dedacted_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You don't have enough balance to place this bet",
        )
    db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
    db_user.wallet_balance = remain_balance - game_transaction.dedacted_amount

    db.commit()
    db.refresh(db_user)
    new_game_transaction = models.GameTransaction(
        jester_remaining_balance=remain_balance - game_transaction.dedacted_amount,
        total_balance=float(getattr(current_user, 'wallet_balance', 0.0)),
        owner_id=current_user.id,
        owner_name=(getattr(current_user, 'first_name', None) or getattr(current_user, 'name', None)),
        **game_transaction.dict(),
    )
    db.add(new_game_transaction)
    db.commit()
    db.refresh(new_game_transaction)

    return {
        "message": "Game Transaction Created Successfully",
        "game_transaction": new_game_transaction,
    }


@router.get("/")
def get_game_transactions(
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"you do not have permission to access this data",
        )

    game_transaction = db.query(models.GameTransaction).all()
    if not game_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No game transaction found",
        )

    return game_transaction


@router.get("/my/{id}")
def get_game_transaction_by_userid(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    game_transaction = db.query(models.GameTransaction).all()
    if not game_transaction:
        raise HTTPException(status_code=404, detail="There is no game transaction yet.")

    if user.role.value == "owner":
        return game_transaction

    game_transactions = (
        db.query(models.GameTransaction)
        .filter(models.GameTransaction.owner_id == id)
        .all()
    )
    if not game_transactions:
        raise HTTPException(
            status_code=404, detail="you don't have a game transaction yet."
        )

    return game_transactions


@router.get("/my-game-transaction")
def get_game_transaction_by_userid(
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(current_user)
    game_transaction = (
        db.query(models.GameTransaction)
        .filter(models.GameTransaction.owner_id == current_user.id)
        .all()
    )
    if not game_transaction:
        raise HTTPException(
            status_code=404, detail="you don't have a game transaction yet."
        )

    return game_transaction
