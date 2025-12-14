from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app import models, oauth2
from app.database import get_db
from app import schemas, utils
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError


router = APIRouter(prefix="/api/management", tags=["Management"])


# New endpoints to match API requirement under /users
@router.post("/users/create", status_code=201)
def users_create(
    payload: schemas.CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Role of current user
    cur_role = current_user.role.value

    # Hierarchy rules
    allowed = {
        "OWNER": {"MANAGER", "SUPERAGENT", "JESTER"},
        "MANAGER": {"SUPERAGENT", "JESTER"},
        "SUPERAGENT": {"JESTER"},
    }

    if payload.role not in allowed.get(cur_role, set()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create this role")

    # duplicate phone check
    if db.query(models.User).filter(models.User.phone == payload.phone_number).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered")

    hashed = utils.hash_password(payload.password)

    new_user = models.User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone_number,
        phone_number=payload.phone_number,
        password=hashed,
        city=payload.city,
        region=payload.region,
        role=models.Role[payload.role],
        wallet_balance=0.0,
        superior_id=current_user.id,
        created_by=current_user.id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"status": "success", "message": f"{payload.role} account created successfully.", "data": {"user_id": new_user.id, "created_by": current_user.id}}


@router.get("/users", status_code=200)
def users_list(role: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    cur_role = current_user.role.value
    query = db.query(models.User)
    if role:
        # role filter expects uppercase
        query = query.filter(models.User.role == models.Role[role])

    if cur_role == "OWNER":
        users = query.all()
    elif cur_role in ("MANAGER", "SUPERAGENT"):
        users = query.filter(models.User.superior_id == current_user.id).all()
    else:
        # Jester only own
        users = query.filter(models.User.id == current_user.id).all()

    data = []
    for u in users:
        # include latest package transaction sender/receiver names as extra
        try:
            last_tx = (
                db.query(models.PackageTransaction)
                .filter(
                    (models.PackageTransaction.receiver_id == u.id) | (models.PackageTransaction.sender_id == u.id)
                )
                .order_by(models.PackageTransaction.created_at.desc())
                .first()
            )
        except Exception:
            last_tx = None

        extra = {
            "sender_name": getattr(last_tx, "sender_name", None) if last_tx else None,
            "receiver_name": getattr(last_tx, "receiver_name", None) if last_tx else None,
        }

        data.append({
            "id": u.id,
            "name": f"{getattr(u,'first_name',None) or getattr(u,'name',None)} {getattr(u,'last_name',None) or ''}".strip(),
            "role": u.role.value.title(),
            "balance": float(getattr(u, 'wallet_balance', 0.0) or 0.0),
            "superior_id": getattr(u, 'superior_id', None),
            "status": "active",
            "extra": extra,
        })

    return {"status": "success", "data": data}


@router.put("/users/profile", status_code=200)
def update_profile(payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # update allowed fields
    allowed_fields = {"first_name", "last_name", "city", "region"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields to update")

    db.query(models.User).filter(models.User.id == current_user.id).update(update_data)
    db.commit()

    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    return {"status": "success", "data": {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "city": user.city, "region": user.region}}


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    role = None
    try:
        role = current_user.role.value
    except Exception:
        role = getattr(current_user, "role", None)

    # Determine user scope
    if role == "OWNER":
        # all users
        user_query = db.query(models.User.id)
    elif role in ("MANAGER", "SUPERAGENT"):
        # direct children created by this user
        user_query = db.query(models.User.id).filter(models.User.created_by == current_user.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    user_ids = [u[0] for u in user_query.all()]

    # If owner and no users exist, return zeros
    if role == "OWNER" and not user_ids:
        # include 0 results
        wallet_summary = {
            "total_wallet_balance": 0.0,
            "user_count": 0,
        }
        network_stats = {
            "total_transactions": 0,
            "total_wins_count": 0,
            "total_wins_amount": 0.0,
        }
        return {"wallet_summary": wallet_summary, "network_stats": network_stats}

    # For scope queries, include current_user as well for managers/superagents
    if role in ("MANAGER", "SUPERAGENT"):
        user_ids.append(current_user.id)

    # Compute wallet summary
    wallet_q = (
        db.query(
            func.coalesce(func.sum(models.User.wallet_balance), 0),
            func.count(models.User.id),
        )
        .filter(models.User.id.in_(user_ids))
        .first()
    )

    total_wallet_balance = float(wallet_q[0] or 0.0)
    user_count = int(wallet_q[1] or 0)

    # Compute transaction stats
    gt_total = (
        db.query(func.count(models.GameTransaction.id))
        .filter(models.GameTransaction.jester_id.in_(user_ids))
        .scalar()
    ) or 0

    pt_total = (
        db.query(func.count(models.PackageTransaction.id))
        .filter(or_(models.PackageTransaction.sender_id.in_(user_ids), models.PackageTransaction.receiver_id.in_(user_ids)))
        .scalar()
    ) or 0

    total_transactions = int(gt_total) + int(pt_total)

    wins_count = (
        db.query(func.count(models.GameTransaction.id))
        .filter(models.GameTransaction.jester_id.in_(user_ids))
        .filter(models.GameTransaction.winner_payout > 0)
        .scalar()
    ) or 0

    wins_amount = (
        db.query(func.coalesce(func.sum(models.GameTransaction.winner_payout), 0))
        .filter(models.GameTransaction.jester_id.in_(user_ids))
        .filter(models.GameTransaction.winner_payout > 0)
        .scalar()
    ) or 0

    wallet_summary = {
        "total_wallet_balance": total_wallet_balance,
        "user_count": user_count,
    }

    network_stats = {
        "total_transactions": int(total_transactions),
        "total_wins_count": int(wins_count),
        "total_wins_amount": float(wins_amount),
    }

    return {"wallet_summary": wallet_summary, "network_stats": network_stats}


@router.post("/create-member")
def create_member(
    payload: schemas.CreateMemberSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Current user's role value (normalized)
    try:
        current_role = (current_user.role.value or "").strip().lower()
    except Exception:
        current_role = str(getattr(current_user, "role", "")).strip().lower()

    # Normalize requested role; accept enum or string. Treat 'user' as alias for 'jester'.
    requested_raw = payload.role.value if hasattr(payload.role, "value") else str(payload.role)
    requested_norm = (requested_raw or "").strip().lower()
    # allow both 'user' and 'jester' as synonyms mapping to the same internal role
    if requested_norm == "user":
        requested_norm = "jester"

    # Allowed roles mapping (keys/values are normalized lowercase role names)
    # Use the canonical internal name 'jester' (enum member JESTER) rather than 'user'.
    allowed_map = {
        "owner": {"owner", "manager", "superagent", "jester"},
        "manager": {"superagent", "jester"},
        "superagent": {"jester"},
    }

    allowed = allowed_map.get(current_role, set())
    if requested_norm not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to create this role")

    # Resolve the role to assign into the models.Role enum.
    # Try member name first (case-insensitive), then try value match.
    role_to_assign = None
    try:
        # Try as a member name (e.g. 'JESTER' or 'jester')
        role_to_assign = models.Role[requested_norm.upper()]
    except Exception:
        try:
            # Try by exact value (e.g. models.Role('JESTER'))
            role_to_assign = models.Role(requested_raw)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role specified")

    # Check duplicate phone
    existing = db.query(models.User).filter(models.User.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered")

    # Hash password
    hashed = utils.hash_password(payload.password)

    new_user = models.User(
        first_name=payload.name,
        phone=payload.phone,
        password=hashed,
        role=role_to_assign,
        city=payload.city,
        region=payload.region,
        wallet_balance=0.0,
        created_by=current_user.id,
        parent_id=current_user.id if current_role in ("manager", "superagent") else None,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        # rollback and expose the error detail to help debugging
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not create user: {e}")

    return {"user_id": new_user.id, "phone": new_user.phone, "role": new_user.role.value}


# `transfer_credit` endpoint removed — consolidated to `/transactions/send-package`.
# Use `/transactions/send-package` for package transfers (owner bypass, manager/superagent atomic transfer).


# `package/revoke` endpoint removed — use `/transactions/revert` for reverting package transactions.



@router.put("/credit-requests/{request_id}/action")
def credit_request_action(
    request_id: int,
    payload: schemas.ActionSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Load credit request
    cr = db.query(models.CreditRequest).filter(models.CreditRequest.id == request_id).first()
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit request not found")

    # Ensure current_user is the superior
    if cr.superior_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to act on this request")

    # Only allow action if request is pending
    if cr.status not in ("PENDING", "REQUESTED", None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already processed")

    # If REJECT simply update status
    try:
        if payload.action == schemas.CreditAction.REJECT:
            cr.status = "REJECTED"
            db.add(cr)
            db.commit()
            db.refresh(cr)
            return {"status": cr.status}

        # For APPROVE, transfer funds
        if payload.action == schemas.CreditAction.APPROVE:
            amount = float(cr.amount)

            # check superior balance
            superior = db.query(models.User).filter(models.User.id == current_user.id).with_for_update().one()
            if float(getattr(superior, 'wallet_balance', 0.0) or 0.0) < amount:
                raise HTTPException(status_code=402, detail="Superior has insufficient balance")

            # fetch recipient and lock
            recipient = db.query(models.User).filter(models.User.id == cr.user_id).with_for_update().one()

            # perform transfer
            superior.wallet_balance = (superior.wallet_balance or 0.0) - amount
            recipient.wallet_balance = (recipient.wallet_balance or 0.0) + amount

            # update request status
            cr.status = "APPROVED"

            # log package transaction
            tx = models.PackageTransaction(
                sender_id=superior.id,
                receiver_id=recipient.id,
                receiver_name=recipient.name,
                sender_name=superior.name,
                package_amount=int(amount) if isinstance(amount, (int, float)) else amount,
            )
            db.add(tx)
            db.add(superior)
            db.add(recipient)
            db.add(cr)

            # commit changes explicitly as requested
            db.commit()
            db.refresh(superior)
            db.refresh(recipient)
            db.refresh(cr)

            return {"status": cr.status, "superior_balance": float(superior.wallet_balance), "recipient_balance": float(recipient.wallet_balance)}

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    except HTTPException:
        # re-raise HTTP errors
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not process action: {e}")
