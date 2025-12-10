from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app import database
from .. import models, utils, oauth2, schemas


router = APIRouter(tags=["Authentication"])


# New API: /auth/signin (requirements)
@router.post("/auth/signin", status_code=status.HTTP_200_OK, response_model=schemas.SignInResponse)
def auth_signin(
    credentials: schemas.SignInRequest,
    db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(models.User.phone == credentials.phone_number).first()

    if not user or not utils.verify_password(credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = oauth2.create_access_token(data={"user_id": user.id, "role": user.role.value})

    # Determine balance field: Owner has UNLIMITED
    if hasattr(user, "role") and user.role.value == "OWNER":
        balance_field = "UNLIMITED"
    else:
        # only use wallet_balance
        balance_field = float(getattr(user, "wallet_balance", 0.0) or 0.0)

    user_out = {
        "id": user.id,
        "first_name": getattr(user, "first_name", None) or getattr(user, "name", None),
        "last_name": getattr(user, "last_name", None),
        "role": user.role.value.title(),
        "balance": balance_field,
    }

    return {
        "status": "success",
        "data": {"token": access_token, "user": user_out},
    }



@router.post("/auth/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    # Ensure authenticated
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Verify old password
    if not utils.verify_password(payload.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

    # Verify new password confirmation
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password and confirm password do not match")

    # Hash and update
    hashed = utils.hash_password(payload.new_password)
    db.query(models.User).filter(models.User.id == current_user.id).update({"password": hashed})
    db.commit()

    return {"status": "success", "message": "Password changed successfully"}
