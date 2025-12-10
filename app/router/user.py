from fastapi import APIRouter, Depends, HTTPException, status
from .. import models, oauth2, schemas
from sqlalchemy.orm import Session
from .. import database, models, utils
from typing import List

router = APIRouter(tags=["User"], prefix="/user")


@router.post("/fake", status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate = Depends(),
    db: Session = Depends(database.get_db),
):

    db_user = db.query(models.User).filter(models.User.phone == user.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Hash the password
    hashed_password = utils.hash_password(user.password)
    user.password = hashed_password
    # map any provided remaining_balance in the request to wallet_balance
    user_data = user.dict()
    if 'remaining_balance' in user_data:
        user_data['wallet_balance'] = user_data.pop('remaining_balance')
    # ensure wallet_balance exists
    user_data.setdefault('wallet_balance', 0.0)
    new_user = models.User(**user_data)

    # Save user to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "phone": new_user.phone}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if current_user.role.value == "JESTER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to create a user",
        )

    if current_user.role.value == "SUPERAGENT" and user.role.value != "JESTER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Superagent does not have permission to create a owner, Manager and Superagent",
        )
    if current_user.role.value == "MANAGER" and (
        user.role.value == "MANAGER" or user.role.value == "OWNER"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Manager does not have permission to create a owner or Manager",
        )

    db_user = db.query(models.User).filter(models.User.phone == user.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Hash the password
    hashed_password = utils.hash_password(user.password)
    user.password = hashed_password

    user_data = user.dict()
    if 'remaining_balance' in user_data:
        user_data['wallet_balance'] = user_data.pop('remaining_balance')
    user_data.setdefault('wallet_balance', 0.0)
    new_user = models.User(
        created_by=current_user.id,
        **user_data,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}


@router.get("/", response_model=List[schemas.UserOut])
def get_all_user(
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role.value != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to get all Users",
        )
    users = db.query(models.User).filter(models.User.role == models.Role.JESTER).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Users found",
        )

    return users


@router.get("/all-role-users", response_model=List[schemas.UserOut])
def get_all_role_user(
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role.value != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to get all Users",
        )
    users = db.query(models.User).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Users found",
        )

    return users


@router.get("/me", response_model=schemas.UserOut)
def get_current_user(
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.get("/managers", response_model=List[schemas.UserOut])
def get_all_managers(
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
            detail=f"User does not have permission to get all Managers",
        )

    users = db.query(models.User).filter(models.User.role == models.Role.MANAGER).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Managers found",
        )

    return users


@router.get("/superagents", response_model=List[schemas.UserOut])
def get_all_superagents(
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role.value != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to get all Superagents",
        )

    users = db.query(models.User).filter(models.User.role == models.Role.SUPERAGENT).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Superagents found",
        )

    return users


@router.get("/child", response_model=List[schemas.UserOut])
def get_users_created_by_current_user(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    users = db.query(models.User).filter(models.User.parent_id == current_user.id).all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found created by the current user",
        )

    return users


# @router.get("/child/manager/{id}", response_model=List[schemas.UserOut])
# def get_users_created_by_user_id(
#     id: int,
#     db: Session = Depends(database.get_db),
#     current_user: models.User = Depends(oauth2.get_current_user),
# ):
#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     users = (
#         db.query(models.User)
#         .filter(
#             (models.User.parent_id == id) & (models.User.role == "manager"),
#         )
#         .all()
#     )

#     if not users:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No users found created by user with id {id}",
#         )

#     return users


@router.get("/child/superagent/{id}", response_model=List[schemas.UserOut])
def get_users_created_by_user_id(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found",
        )

    users = (
        db.query(models.User)
        .filter(
            (models.User.role == models.Role.SUPERAGENT),
        )
        .all()
    )

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )

    if user.role.value == "OWNER":
        return users

    all_users = (
        db.query(models.User)
        .filter(
            (models.User.parent_id == id) & (models.User.role == "superagent"),
        )
        .all()
    )

    if not all_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )

    return all_users


@router.get("/child/user/{id}", response_model=List[schemas.UserOut])
def get_users_created_by_user_id(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found",
        )

    all_users = (
        db.query(models.User)
        .filter(
            (models.User.role == models.Role.JESTER),
        )
        .all()
    )

    if not all_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )

    if user.role.value == "OWNER":
        return all_users

    users = (
        db.query(models.User)
        .filter(
            (models.User.parent_id == id) & (models.User.role == models.Role.JESTER),
        )
        .all()
    )

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )

    return users


@router.post("/update/", response_model=schemas.UserOut)
def update_user(
    user: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db.query(models.User).filter(models.User.id == user.id).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields if they are provided (even if value is 0 or empty string)
    if user.phone is not None:
        db_user.phone = user.phone

    if user.region is not None:
        db_user.region = user.region

    if user.city is not None:
        db_user.city = user.city

    if user.name is not None:
        db_user.name = user.name

    if user.role is not None:
        db_user.role = user.role

    if user.parent_id is not None:
        db_user.parent_id = user.parent_id

    if user.created_by is not None:
        db_user.created_by = user.created_by

    if user.remaining_balance is not None:
        # map provided remaining_balance to wallet_balance column
        db_user.wallet_balance = user.remaining_balance

    if user.password:
        db_user.password = utils.hash_password(user.password)

    db.commit()
    db.refresh(db_user)

    return db_user
