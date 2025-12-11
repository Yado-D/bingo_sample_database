from fastapi import File, UploadFile
from pydantic import BaseModel
from typing import List, Optional, Any, Dict, Union
from pydantic import EmailStr, Field
from datetime import datetime
import enum
from app.models import Role


class IntList(BaseModel):
    data: List[int]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    id: int
    phone: Optional[str] = None
    region: Optional[str] = None
    profile_picture: Optional[str] = None
    parent_id: Optional[int] = None
    name: Optional[str] = None
    city: Optional[str] = None
    remaining_balance: Optional[float] = None
    role: Optional[str] = None
    password: Optional[str] = None
    created_by: Optional[int] = None


class BingoCardFetch(BaseModel):
    bingo_card_code: str


class BingoCardCreate(BaseModel):
    B: List[int]
    I: List[int]
    N: List[int]
    G: List[int]
    O: List[int]
    cardNumber: List[int]


class MultipleBingoCardsCreate(BaseModel):
    cards: List[BingoCardCreate]
    id: int


class UserLogin(BaseModel):
    phone: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class GameTransactionModel(BaseModel):
    bet_amount: int
    winning_pattern: Optional[str] = None
    number_of_cards: int
    dedacted_amount: int


class PackageTransactionModel(BaseModel):
    package_amount: float


class BingoCardOut(BaseModel):
    id: int
    owner_id: Optional[int]
    card_data: Any
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    phone: str
    region: Optional[str] = None
    wallet_balance: Optional[float] = None
    profile_picture: Optional[str] = None
    parent_id: Optional[int] = None
    id: int
    name: Optional[str] = None
    city: Optional[str] = None
    role: str
    # total_balance removed; use `wallet_balance` as canonical field
    created_by: Optional[int] = None
    created_at: datetime
    bingo_card_code: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenData(BaseModel):
    id: Optional[int] = None


class UserCreate(BaseModel):
    phone: str
    wallet_balance: Optional[float] = 0.0
    name: Optional[str] = None
    role: Role
    city: Optional[str] = None
    region: Optional[str] = None
    password: str
    profile_picture: Optional[str] = None
    parent_id: Optional[int] = None


class UserProfileResponse(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    wallet_balance: float = 0.0
    total_winnings: float = 0.0
    total_wins_count: int = 0
    total_transactions: int = 0

    class Config:
        from_attributes = True


class TransactionOut(BaseModel):
    date: datetime
    game_pattern: Optional[str] = None
    bet_amount: Optional[int] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class GameStartRequest(BaseModel):
    selected_card_numbers: List[int]
    bet_amount_per_card: float


class GameStartResponse(BaseModel):
    game_session_id: int
    new_balance: float

    class Config:
        from_attributes = True


class GameResultStatus(str, enum.Enum):
    WIN = "WIN"
    LOSE = "LOSE"


class GameResultRequest(BaseModel):
    game_session_id: int
    status: GameResultStatus
    win_amount: float = 0.0
    winning_pattern: Optional[str] = None


class EndGameRequest(BaseModel):
    total_pot: float
    cut: float
    winning_pattern: str
    win_amount: float
    bet_amount: float
    date: str
    time: str
    jester_name: str

    class Config:
        from_attributes = True


class GameResultResponse(BaseModel):
    new_balance: float

    class Config:
        from_attributes = True


class CreateMemberSchema(BaseModel):
    phone: str
    password: str
    name: Optional[str] = None
    role: Role
    city: Optional[str] = None
    region: Optional[str] = None

    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    recipient_id: int
    amount: float


class TransferResponse(BaseModel):
    sender_balance: float
    recipient_balance: float

    class Config:
        from_attributes = True


class CreditAction(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ActionSchema(BaseModel):
    action: CreditAction

    class Config:
        from_attributes = True


class RevokeRequest(BaseModel):
    transaction_id: int

    class Config:
        from_attributes = True


class SignInRequest(BaseModel):
    phone_number: str
    password: str


class SignInUserOut(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    balance: Union[float, str]


class SignInData(BaseModel):
    token: str
    user: SignInUserOut


class SignInResponse(BaseModel):
    status: str
    data: SignInData


class CreateUserRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    city: Optional[str] = None
    region: Optional[str] = None
    password: str
    role: str


class CreateUserResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


class SendPackageRequest(BaseModel):
    receiver_id: int
    amount: float


class SendPackageResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


class GameEndRequest(BaseModel):
    game_id: str
    winner_cartela_id: str


class GameEndResponseData(BaseModel):
    total_pot: float
    house_cut: float
    winner_payout: float
    jester_balance_deducted: float
    jester_remaining_balance: float


class GameEndResponse(BaseModel):
    status: str
    message: str
    data: GameEndResponseData


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    class Config:
        from_attributes = True
