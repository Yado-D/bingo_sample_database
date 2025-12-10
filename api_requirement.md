Here is the comprehensive Backend API Documentation designed for the Bingo Game System.

### **Base Configuration**

- **Base URL:** `/api/v1`
- **Authentication:** Bearer Token (JWT) in Headers (`Authorization: Bearer <token>`)
- **Data Format:** JSON

---

### **1. Authentication Module**

#### **1.1 Sign In**

- **Access:** All Roles (Owner, Manager, Superagent, Jester)
- **Endpoint:** `POST /auth/signin`
- **Description:** Authenticates the user. The backend determines the role and permissions.

**Request Body:**

```json
{
  "phone_number": "+251911234567",
  "password": "securePassword123"
}
```

**Response (Success - 200 OK):**

```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR...",
    "user": {
      "id": 101,
      "first_name": "Abebe",
      "last_name": "Kebede",
      "role": "Owner",
      "balance": "UNLIMITED"
    }
  }
}
```

#### **1.2 Change Password**

- **Access:** All Roles (Owner, Manager, Superagent, Jester)
- **Endpoint:** `POST /auth/change-password`
- **Description:** Allows a logged-in user to update their password.
- **Security:** Requires the user to provide their _current_ password for verification before setting a new one.

**Request Body:**

```json
{
  "old_password": "currentPassword123",
  "new_password": "newSecurePassword456",
  "confirm_password": "newSecurePassword456"
}
```

**Response (Success - 200 OK):**

```json
{
  "status": "success",
  "message": "Password updated successfully."
}
```

**Response (Error - 400 Bad Request):**

- If `old_password` is incorrect.
- If `new_password` does not match `confirm_password`.

_Note: If the role is Jester, Manager, or Superagent, `balance` returns the actual numeric float value._

---

### **2. User Management Module**

#### **2.1 Create New User**

- **Access:** Owner, Manager, Superagent (Restricted by hierarchy)
- **Endpoint:** `POST /users/create`
- **Logic:**
  - **Owner:** Can create Manager, Superagent, Jester.
  - **Manager:** Can create Superagent, Jester.
  - **Superagent:** Can create Jester only.

**Request Body:**

```json
{
  "first_name": "Dawit",
  "last_name": "Mekonnen",
  "phone_number": "+251922334455",
  "city": "Addis Ababa",
  "region": "Bole",
  "password": "initialPassword123",
  "role": "Jester"
}
```

**Response (Success - 201 Created):**

```json
{
  "status": "success",
  "message": "Jester account created successfully.",
  "data": {
    "user_id": 505,
    "created_by": 101
  }
}
```

#### **2.2 Get Users List**

- **Access:** Owner (All), Manager/Superagent (Subordinates only)
- **Endpoint:** `GET /users`
- **Query Params:** `?role=Jester` (Optional filter)

**Response (Success - 200 OK):**

```json
{
  "status": "success",
  "data": [
    {
      "id": 505,
      "name": "Dawit Mekonnen",
      "role": "Jester",
      "balance": 200.0,
      "superior_id": 101,
      "status": "active"
    }
  ]
}
```

#### **2.3 Update Profile**

- **Access:** All Roles (Own profile only)
- **Endpoint:** `PUT /users/profile`

**Request Body:**

```json
{
  "first_name": "NewName",
  "last_name": "NewLast",
  "city": "NewCity",
  "region": "NewRegion"
}
```

---

### **3. Financial Module (Packages)**

#### **3.1 Send Package (Credit Transfer)**

- **Access:** Owner, Manager, Superagent
- **Endpoint:** `POST /transactions/send-package`
- **Logic:**
  - **Owner:** Logic ignores sender balance (Unlimited). Adds amount to receiver.
  - **Manager/Superagent:** Checks sender balance > Deducts Amount > Adds to receiver.

**Request Body:**

```json
{
  "receiver_id": 505,
  "amount": 5000.0
}
```

**Response (Success - 200 OK):**

```json
{
  "status": "success",
  "message": "Package sent successfully",
  "data": {
    "transaction_id": "TXN-998877",
    "sender_new_balance": "UNLIMITED",
    "receiver_new_balance": 5200.0
  }
}
```

#### **3.2 Request Package**

- **Access:** Jester only
- **Endpoint:** `POST /transactions/request-package`

**Request Body:**

```json
{
  "amount": 2000.0,
  "note": "Running low for night shift"
}
```

#### **3.3 View Transactions**

- **Access:**
  - Owner (See All: Game Trans & Package Trans)
  - Manager/Superagent (See Subordinates)
  - Jester (See Own)
- **Endpoint:** `GET /transactions`
- **Query Params:** `?type=package` or `?type=game`

**Response (Success - 200 OK):**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "type": "package",
      "sender": "Owner Admin",
      "receiver": "Jester Dawit",
      "amount": 5000.0,
      "date": "2023-10-27T10:00:00Z"
    }
  ]
}
```

#### **3.4 Revert Sent Package**

- **Access:** Owner, Manager, Superagent
- **Endpoint:** `POST /transactions/revert`
- **Description:** Allows a sender to take back a package sent by mistake.
- **Logic:**
  1.  **Validation:** The `current_user` must be the **Sender** of the original transaction (or an Owner with override permissions).
  2.  **Balance Check:** The system checks if the **Receiver** currently has enough balance to return the amount.
      - _If yes:_ Deduct amount from Receiver -> Add back to Sender.
      - _If no:_ Return `400 Bad Request` (Receiver already spent the money).
  3.  **Status Update:** Mark the original transaction status as `REVERTED`.

**Request Body:**

```json
{
  "transaction_id": "TXN-998877"
}
```

**Response (Success - 200 OK):**

```json
{
  "status": "success",
  "message": "Transaction reverted successfully.",
  "data": {
    "reverted_amount": 5000.0,
    "sender_new_balance": 15000.0,
    "receiver_new_balance": 200.0,
    "status": "REVERTED"
  }
}
```

---

### **4. Game Operations Module**

#### **4.1 End Game (Payout)**

- **Access:** Jester
- **Endpoint:** `POST /game/end`
- **Logic:**
  - Calculates the payout.
  - **Formula:** `Payout = Total Pot - Cut`.
  - Deducts the Payout amount from the Jester's wallet balance.

**Request Body:**

```json
{
  "game_id": "GAME-777",
  "winner_cartela_id": "CARD-05"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Game Over. Accounts updated.",
  "data": {
    "total_pot": 500.0,
    "house_cut": 100.0,
    "winner_payout": 400.0,
    "jester_balance_deducted": 400.0,
    "jester_remaining_balance": 4800.0
  }
}
```

---

### **5. Error Handling Codes**

The API will return standard HTTP status codes:

- `200` - OK
- `400` - Bad Request (e.g., Insufficient balance for Manager/Superagent).
- `401` - Unauthorized (Invalid Token).
- `403` - Forbidden (e.g., Jester trying to create a User).
- `404` - User or Resource Not Found.
- `500` - Internal Server Error.
