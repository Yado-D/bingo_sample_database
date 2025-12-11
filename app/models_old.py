from enum import Enum
from sqlalchemy import JSON, Column, Integer, String, Enum as SAEnum
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum
from sqlalchemy import Float


class Role(enum.Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    SUPERAGENT = "SUPERAGENT"
    JESTER = "JESTER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # New explicit name fields
    first_name = Column(String, index=True, nullable=True)
    last_name = Column(String, index=True, nullable=True)
    # Keep legacy phone column but add new standardized name
    phone = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, index=True, nullable=False)
    gender = Column(String, index=True, nullable=True)
    city = Column(String, index=True, nullable=True)
    region = Column(String, index=True, nullable=True)
    # Role now uses the explicit Role enum values
    role = Column(SAEnum(Role), index=True, nullable=False)
    # Wallet balance (current available for gameplay)
    wallet_balance = Column(Float, index=True, nullable=False, default=0.0)
    # NOTE: `remaining_balance` and `total_balance` removed in favor of `wallet_balance`
    profile_picture = Column(String, nullable=True)
    # Superior id - who manages/created this user
    superior_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # legacy created_by / parent id kept for compatibility
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    bingo_card_code = Column(
        String(6), ForeignKey("bingo_cards.id", ondelete="CASCADE"), nullable=True
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class GameTransaction(Base):
    __tablename__ = "game_transactions"

    id = Column(Integer, primary_key=True, index=True)
    bet_amount = Column(Float, index=True)
    # replaced `game_type` with `winning_pattern` to record how the game was won
    winning_pattern = Column(String, index=True, nullable=True)
    number_of_cards = Column(Integer, index=True)
    cut_amount = Column(Float, index=True)
    winner_payout = Column(Float, index=True)
    # total pot for this game (snapshot)
    total_pot = Column(Float, index=True, nullable=True)
    # amount deducted or added for this transaction (wins as negative values)
    dedacted_amount = Column(Float, index=True, nullable=True)
    # jester/actor who caused this transaction (the player)
    # `owner_id`/`owner_name` removed in favor of `jester_id`/`jester_name`
    # jester specific fields
    jester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    jester_name = Column(String, index=True, nullable=True)
    # store the user's remaining balance after the transaction
    jester_remaining_balance = Column(Float, index=True, nullable=True)
    # optional date/time fields provided by frontend
    tx_date = Column(String, index=True, nullable=True)
    tx_time = Column(String, index=True, nullable=True)
    # optional snapshot of total/wallet balance after transaction
    total_balance = Column(Float, index=True, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class PackageTransaction(Base):
    __tablename__ = "package_transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    receiver_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    receiver_name = Column(String, index=True)
    sender_name = Column(String, index=True)
    package_amount = Column(Float, index=True)
    status = Column(String, index=True, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class BingoCard(Base):
    __tablename__ = "bingo_cards"
    id = Column(String(6), primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_data = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class StoredData(Base):
    __tablename__ = "stored_data"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bet_amount_per_card = Column(Float, nullable=False)
    total_bet = Column(Float, nullable=False)
    selected_cards = Column(JSON, nullable=False)
    status = Column(String, index=True, nullable=False)
    total_pot = Column(Float, nullable=True)
    house_cut = Column(Float, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class CreditRequest(Base):
    __tablename__ = "credit_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    superior_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, index=True, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
