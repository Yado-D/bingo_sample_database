from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, oauth2, helper
from app.database import get_db
from app.schemas import MultipleBingoCardsCreate
from .. import schemas

router = APIRouter(prefix="/cards", tags=["Bingo Cards"])


@router.post("/")
def get_bingo_cards_byId(
    bingo_card: schemas.BingoCardFetch, db: Session = Depends(get_db)
):

    bingo_cards = (
        db.query(models.BingoCard)
        .filter((models.BingoCard.id == bingo_card.bingo_card_code))
        .first()
    )

    if not bingo_cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bingo card not found",
        )

    return bingo_cards


# @router.post("/bingo_cards/")
# def create_bingo_cards(
#     bingo_cards: MultipleBingoCardsCreate,
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user),
# ):
#     id = bingo_cards.id
#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
#         )
#     user = db.query(models.User).filter(models.User.id == id).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"User with id {id} not found",
#         )
#     card = db.query(models.BingoCard).filter(models.BingoCard.owner_id == id).first()
#     if card:
#         db.delete(card)
#         db.commit()

#     created_cards = []
#     for card in bingo_cards.cards:
#         card_dict = {
#             "B": card.B,
#             "I": card.I,
#             "N": card.N,
#             "G": card.G,
#             "O": card.O,
#             "cardNumber": card.cardNumber,
#         }
#         created_cards.append(card_dict)

#     card_dict = {
#         "cards": created_cards,
#     }
#     card_id = helper.generate_unique_code(db)
#     db_card = models.BingoCard(owner_id=id, card_data=card_dict, id=card_id)
#     user = db.query(models.User).filter(models.User.id == id).first()

#     db.add(db_card)
#     db.commit()
#     db.query(models.User).filter(models.User.id == id).update(
#         {
#             "bingo_card_code": card_id,
#         }
#     )
#     db.commit()

#     db.refresh(db_card)

#     return created_cards


@router.post("/bingo_cards/")
def create_bingo_cards(
    bingo_cards: MultipleBingoCardsCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    id = bingo_cards.id
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found",
        )
    # Check if bingo card already exists
    card = db.query(models.BingoCard).filter(models.BingoCard.owner_id == id).first()

    # Build the card payload from the request
    created_cards = []
    for c in bingo_cards.cards:
        card_dict = {
            "B": c.B,
            "I": c.I,
            "N": c.N,
            "G": c.G,
            "O": c.O,
            "cardNumber": c.cardNumber,
        }
        created_cards.append(card_dict)

    new_card_data = {"cards": created_cards}
    card_id = helper.generate_unique_code(db)

    # If a card exists, update the ORM object and explicitly add/flush
    if card:
        card.card_data = new_card_data
        db.add(card)
        db.flush()
    else:
        db_card = models.BingoCard(owner_id=id, card_data=new_card_data, id=card_id)
        db.add(db_card)
        db.flush()
        card = db_card

    # Update the user's bingo_card_code using the ORM object (safer than query.update)
    user.bingo_card_code = card.id
    db.add(user)

    # Commit all changes and refresh objects so the session reflects DB state
    db.commit()
    db.refresh(card)
    db.refresh(user)

    return created_cards


# @router.post("/store")
# def store_data(
#     payload: schemas.IntList,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user),
# ):

#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     existing = (
#         db.query(models.StoredData)
#         .filter(models.StoredData.user_id == current_user.id)
#         .first()
#     )

#     if existing:
#         existing.data = payload.data
#         db.commit()
#         db.refresh(existing)
#         return {"message": "Data updated", "data": existing.data}
#     else:
#         new_entry = models.StoredData(data=payload.data, user_id=current_user.id)
#         db.add(new_entry)
#         db.commit()
#         db.refresh(new_entry)
#         return {"message": "Data created", "data": new_entry.data}


# @router.get("/storage")
# def get_data(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user),
# ):
#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     existing = (
#         db.query(models.StoredData)
#         .filter(models.StoredData.user_id == current_user.id)
#         .first()
#     )
#     if not existing:
#         raise HTTPException(status_code=404, detail="No data found")

#     return {"stored_data": existing.data}
