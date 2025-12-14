**Final, Consolidated API Requirement Specification**.

# Bingo Game System - API Requirement Specification (vFinal)

## 1. Authentication Module

### 1.1 Sign In

- **Endpoint:** `POST /auth/signin`
- **Access:** Public (All Roles)
- **Description:** Authenticates users. Returns a token and user profile.
- **Special Logic:**
  - If Role is **OWNER**, `wallet_balance` returns the string `"UNLIMITED"`.
  - For others, `wallet_balance` returns a `float`.

**Request Body:**

```json
{
  "phone_number": "+251911234567",
  "password": "securePassword123"
}
```

**Response (Owner Example):**

```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1Ni...",
    "user": {
      "id": 1,
      "first_name": "Abebe",
      "last_name": "Kebede",
      "role": "OWNER",
      "wallet_balance": "UNLIMITED",
      "city": "Addis Ababa",
      "region": "Bole"
    }
  }
}
```

### 1.2 Change Password

- **Endpoint:** `POST /auth/change-password`
- **Access:** Authenticated Users
- **Logic:** Verifies old password before updating.

**Request Body:**

```json
{
  "old_password": "currentPassword123",
  "new_password": "newSecurePassword456",
  "confirm_password": "newSecurePassword456"
}
```

---

## 2. User Management Module (Prefix: `/api/management`)

### 2.1 Create User

- **Endpoint:** `POST /api/management/users/create`
- **Access:** Owner, Manager, Superagent (Hierarchy Enforced)
- **Logic:**
  - **Owner** creates Manager, Superagent, Jester.
  - **Manager** creates Superagent, Jester.
  - **Superagent** creates Jester.

**Request Body:**

```json
{
  "first_name": "Dawit",
  "last_name": "Mekonnen",
  "phone_number": "+251922334455",
  "city": "Addis Ababa",
  "region": "Bole",
  "password": "initialPassword123",
  "role": "JESTER"
}
```

### 2.2 List Users

- **Endpoint:** `GET /api/management/users`
- **Access:** Owner (All), Manager/Superagent (Subordinates Only)
- **Query Params:** `?role=JESTER` (Optional)

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": 505,
      "first_name": "Dawit",
      "last_name": "Mekonnen",
      "role": "JESTER",
      "wallet_balance": 200.0,
      "superior_id": 101,
      "status": "active"
    }
  ]
}
```

### 2.3 Get Current Profile (Me)

- **Endpoint:** `GET /users/me`
- **Access:** Authenticated User
- **Logic:** `total_sent` and `total_received` are calculated dynamically from the `transactions` table.

**Response:**

```json
{
  "user": {
    "id": 505,
    "first_name": "Dawit",
    "phone_number": "+251922334455",
    "role": "JESTER",
    "city": "Adama",
    "region": "Nazret"
  },
  "wallet_balance": 200.0,
  "total_sent": 0.0,
  "total_received": 5000.0
}
```

### 2.4 Update Profile

- **Endpoint:** `PUT /api/management/users/profile`
- **Access:** Authenticated User (Own Profile)

**Request Body:**

```json
{
  "first_name": "Dawit",
  "city": "Adama"
}
```

---

## 3. Financial Module (Prefix: `/transactions`)

### 3.1 Send Package (Credit Transfer)

- **Endpoint:** `POST /transactions/send-package`
- **Access:** Owner, Manager, Superagent
- **Logic:**
  - **Owner:** Bypasses balance check (Unlimited).
  - **Manager/Superagent:** Checks if `wallet_balance >= amount`.
  - **Action:** Atomic transfer (Deduct Sender -> Add Receiver).

**Request Body:**

```json
{
  "receiver_id": 505,
  "amount": 5000.0
}
```

### 3.2 Request Package

- **Endpoint:** `POST /transactions/request-package`
- **Access:** Jester Only

**Request Body:**

```json
{
  "amount": 2000.0,
  "note": "For night shift"
}
```

### 3.3 View Transactions

- **Endpoint:** `GET /transactions`
- **Access:** All Roles (Filtered by Hierarchy/Ownership)
- **Query Params:** `?type=package` or `?type=game`

**Response:**

```json
[
  {
    "id": 987,
    "transaction_type": "PACKAGE",
    "sender_id": 101,
    "receiver_id": 505,
    "amount": 5000.0,
    "created_at": "2023-10-27T10:00:00Z",
    "status": "COMPLETED"
  }
]
```

### 3.4 Revert Package

- **Endpoint:** `POST /transactions/revert`
- **Access:** Sender (Owner, Manager, Superagent)
- **Logic:**
  1.  Verifies Caller is the Sender.
  2.  Checks if Receiver has enough funds to return.
  3.  Reverses the transfer and marks status `REVERTED`.

**Request Body:**

```json
{
  "transaction_id": 987
}
```

---

## 4. Game Operations Module (Prefix: `/game`)

### 4.1 End Game (Settlement)

- **Endpoint:** `POST /game/end`
- **Access:** Jester Only
- **Logic:**
  1.  **Deduction:** `wallet_balance = wallet_balance - win_amount`.
  2.  **Recording:** Saves the full game details (Pot, Cut, Pattern, etc.) to `GameTransaction`.
  3.  **Timestamp:** Uses the provided `date`/`time` or server time if preferred.

**Request Body:**

```json
{
  "total_pot": 5000.0,
  "cut": 1000.0,
  "winning_pattern": "FULL_HOUSE",
  "win_amount": 4000.0,
  "bet_amount": 50.0,
  "date": "2023-10-27",
  "time": "14:30:00",
  "jester_name": "Dawit"
}
```

_(Note: `win_amount` is the final payout amount that is deducted from Jester's wallet)_

**Response:**

```json
{
  "status": "success",
  "data": {
    "new_wallet_balance": 4800.0,
    "payout_processed": 4000.0
  }
}
```

### 4.2 Jester Game History

- **Endpoint:** `GET /game/my-transactions`
- **Access:** Jester Only
- **Description:** Returns list of games managed by this Jester.

**Response:**

```json
[
  {
    "id": 555,
    "bet_amount": 50.0,
    "winning_pattern": "FULL_HOUSE",
    "win_amount": 4000.0,
    "jester_remaining_balance": 4800.0,
    "tx_date": "2023-10-27",
    "tx_time": "14:30:00"
  }
]
```

---

## 5. Error Handling Codes

- **200:** Success
- **201:** Created
- **400:** Bad Request (e.g., Insufficient Funds, Invalid Password)
- **401:** Unauthorized (Invalid Token)
- **403:** Forbidden (Hierarchy Violation)
- **404:** Not Found
- **500:** Server Error
