from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, oauth2, schemas
from app import database
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/send-package", status_code=status.HTTP_200_OK)
def send_package(
    payload: schemas.SendPackageRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    receiver = db.query(models.User).filter(models.User.id == payload.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found")

    # Owner can send without balance checks
    if current_user.role.value != "OWNER":
        sender_balance = float(getattr(current_user, "wallet_balance", 0.0) or 0.0)
        if sender_balance < payload.amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

        new_sender_balance = sender_balance - payload.amount
        db.query(models.User).filter(models.User.id == current_user.id).update({"wallet_balance": new_sender_balance})
    else:
        new_sender_balance = "UNLIMITED"

    receiver_balance = float(getattr(receiver, "wallet_balance", 0.0) or 0.0)
    new_receiver_balance = receiver_balance + payload.amount
    db.query(models.User).filter(models.User.id == receiver.id).update({"wallet_balance": new_receiver_balance})

    db.commit()

    new_tx = models.PackageTransaction(
        receiver_id=receiver.id,
        sender_id=current_user.id,
        receiver_name=(getattr(receiver, "first_name", None) or getattr(receiver, "name", None)),
        sender_name=(getattr(current_user, "first_name", None) or getattr(current_user, "name", None)),
        package_amount=payload.amount,
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)

    return {
        "status": "success",
        "message": "Package sent successfully",
        "data": {
            "transaction_id": f"TXN-{new_tx.id}",
            "transaction_id_num": new_tx.id,
            "sender_new_balance": new_sender_balance,
            "receiver_new_balance": new_receiver_balance,
        },
    }


@router.post("/request-package", status_code=status.HTTP_200_OK)
def request_package(
    payload: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if current_user.role.value != "JESTER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Jester can request packages")

    new_req = models.CreditRequest(
        user_id=current_user.id,
        superior_id=getattr(current_user, "superior_id", None),
        amount=payload.get("amount", 0.0),
        status="PENDING",
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    return {"status": "success", "message": "Request created", "data": {"request_id": new_req.id}}


@router.get("", status_code=status.HTTP_200_OK)
def list_transactions(
    type: str = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Owner sees all
    if current_user.role.value == "OWNER":
        if type == "package":
            txs = db.query(models.PackageTransaction).all()
        elif type == "game":
            try:
                txs = db.query(models.GameTransaction).all()
            except ProgrammingError:
                # clear the failed transaction so we can run a fallback raw query
                try:
                    db.rollback()
                except Exception:
                    pass
                rows = db.execute(text(
                    "SELECT id, bet_amount, winning_pattern, number_of_cards, created_at FROM game_transactions"
                )).fetchall()
                txs = [dict(row._mapping) for row in rows]
        else:
            try:
                game_rows = db.query(models.GameTransaction).all()
            except ProgrammingError:
                try:
                    db.rollback()
                except Exception:
                    pass
                rows = db.execute(text(
                    "SELECT id, bet_amount, winning_pattern, number_of_cards, created_at FROM game_transactions"
                )).fetchall()
                game_rows = [dict(row._mapping) for row in rows]
            txs = db.query(models.PackageTransaction).all() + game_rows
        return {"status": "success", "data": txs}

    # Manager/Superagent see downstream
    if current_user.role.value in ("MANAGER", "SUPERAGENT"):
        subs = [u.id for u in db.query(models.User).filter(models.User.superior_id == current_user.id).all()]
        txs = db.query(models.PackageTransaction).filter(
            (models.PackageTransaction.receiver_id.in_(subs)) | (models.PackageTransaction.sender_id.in_(subs))
        ).all()
        return {"status": "success", "data": txs}

    # Jester sees own
    txs = db.query(models.PackageTransaction).filter(
        (models.PackageTransaction.receiver_id == current_user.id) | (models.PackageTransaction.sender_id == current_user.id)
    ).all()
    return {"status": "success", "data": txs}


@router.post("/revert", status_code=status.HTTP_200_OK)
def revert_transaction(
    payload: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """Revert a package transaction. Payload expects {"transaction_id": <id>}"""
    tx_id = payload.get("transaction_id")
    if not tx_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="transaction_id is required")

    # Accept either numeric id or string form 'TXN-<id>'
    parsed_id = None
    try:
        if isinstance(tx_id, str):
            if tx_id.startswith("TXN-"):
                parsed_id = int(tx_id.split("-", 1)[1])
            else:
                parsed_id = int(tx_id)
        else:
            parsed_id = int(tx_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="transaction_id must be an integer or 'TXN-<id>' string")

    tx = db.query(models.PackageTransaction).filter(models.PackageTransaction.id == parsed_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Allow either the original sender to revert, or an OWNER (superuser)
    is_owner = getattr(current_user.role, "value", str(current_user.role)).upper() == "OWNER"
    if not (tx.sender_id == current_user.id or is_owner):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sender or OWNER can revert this transaction")

    amount = float(tx.package_amount or 0.0)

    try:
        from sqlalchemy.exc import InvalidRequestError

        try:
            txn = db.begin()
        except InvalidRequestError:
            txn = db.begin_nested()

        with txn:
            # If OWNER is reverting, move funds from receiver -> OWNER (current_user)
            if is_owner and tx.sender_id != current_user.id:
                receiver = db.query(models.User).filter(models.User.id == tx.receiver_id).with_for_update().one()
                owner = db.query(models.User).filter(models.User.id == current_user.id).with_for_update().one()

                recv_balance = float(getattr(receiver, "wallet_balance", 0.0) or 0.0)
                if recv_balance < amount:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receiver has insufficient funds to revert")

                # subtract from receiver
                # subtract from receiver's wallet_balance
                receiver.wallet_balance = recv_balance - amount

                # add to owner
                owner_balance = float(getattr(owner, "wallet_balance", 0.0) or 0.0)
                owner.wallet_balance = owner_balance + amount

                db.add(receiver)
                db.add(owner)

            else:
                # Sender-initiated revert: transfer from receiver back to sender
                sender = db.query(models.User).filter(models.User.id == tx.sender_id).with_for_update().one()
                receiver = db.query(models.User).filter(models.User.id == tx.receiver_id).with_for_update().one()

                recv_balance = float(getattr(receiver, "wallet_balance", 0.0) or 0.0)
                if recv_balance < amount:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receiver has insufficient funds to revert")

                # perform reversal
                receiver.wallet_balance = recv_balance - amount

                sender_balance = float(getattr(sender, "wallet_balance", 0.0) or 0.0)
                sender.wallet_balance = sender_balance + amount

                db.add(sender)
                db.add(receiver)

            # mark original transaction as REVERTED
            tx.status = "REVERTED"
            db.add(tx)

        # Ensure changes are committed to the database and refreshed
        try:
            db.commit()
        except Exception:
            # If commit fails, attempt rollback and re-raise
            try:
                db.rollback()
            except Exception:
                pass
            raise

        # Refresh objects so the returned response reflects current DB state
        try:
            db.refresh(tx)
            if is_owner and tx.sender_id != current_user.id:
                db.refresh(owner)
                db.refresh(receiver)
            else:
                db.refresh(sender)
                db.refresh(receiver)
        except Exception:
            # ignore refresh errors but changes should be persisted
            pass

        return {"status": "success", "message": "Transaction reverted", "data": {"transaction_id": f"TXN-{tx.id}", "transaction_id_num": tx.id}}
    except HTTPException:
        raise
    except Exception as e:
        # ensure session is clean
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not revert transaction: {e}")
