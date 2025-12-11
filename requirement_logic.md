Here is the System Requirement Specification (SRS) for the Bingo Game System, designed according to your specific role hierarchy and terminology constraints.

***

# Software Requirement Specification: Bingo Game Management System

## 1. Introduction
This document outlines the functional and non-functional requirements for a hierarchical Bingo Game System. The system manages game operations, credit distribution (packages), user hierarchy management, and financial reporting.

### 1.1 Definitions
*   **Jester:** Formerly referred to as "User" or "End-User." This role operates the game floor, sells cards, and verifies wins.
*   **Package:** A unit of monetary credit or balance transferred from a superior role to a subordinate to facilitate gameplay.
*   **Cartela:** A bingo card.
*   **Cut:** The house commission or tax deducted from the winning pot before distribution.

---

## 2. User Roles and Hierarchy
The system supports four distinct roles with cascading permissions.

1.  **Owner:** (Super Admin) - Has full system access and visibility.
2.  **Manager:** - Branch-level administrator.
3.  **Superagent:** - Mid-level agent.
4.  **Jester:** - The frontline game operator (formerly "User").

---

## 3. Functional Requirements

### 3.1 Role: Jester (Game Operator)
The Jester is responsible for the immediate execution of bingo games and sales.

**3.1.1 Game Operations**
*   **Start/Pause Game:** The system shall allow the Jester to start the random number generation and pause the game immediately when a player shouts "Bingo."
*   **Win Verification:** The system shall provide a tool for the Jester to input a card number or pattern to verify if the player’s claim is a valid win based on the current game’s logic.
*   **End Game:** The system shall allow the Jester to finalize the game once a winner is verified.

**3.1.2 Sales & Betting**
*   **Sell Cartelas:** The system shall allow the Jester to input the number of cartelas (cards) a player wishes to buy and assign the bet amount per cartela.
*   **Package Requests:** The system shall allow the Jester to send a formal request for a "Package" (credits) to their immediate superior (Superagent or Manager).

**3.1.3 Financial Logic**
*   **Cut/Game Type Setting:** Before or during the game, the Jester must be able to select the "Cut" percentage or Game Type configuration.
*   **Balance Deduction:** Upon confirming a "Game Over/Win," the system shall automatically calculate the payout.
    *   *Logic:* `Jester Wallet Deduction = Winner Amount - House Cut`.
    *   The remaining amount (The Cut) stays in the system profit, while the payout is deducted from the Jester's package balance.

---

### 3.2 Roles: Manager, Superagent, Owner (Common Features)
These features are shared across the administrative tiers.

**3.2.1 Dashboard & Visibility**
*   **User List:** The system shall display a list of all users (Jesters/Superagents) registered under their specific branch/hierarchy.
*   **Financial Stats:**
    *   View current Remaining Balance.
    *   View Total Packages Spent/Sent.
    *   View Total Transactions (Total money gained or lost/net cash flow).

**3.2.2 Profile Management**
*   **Edit Profile:** The user shall be able to edit their own First Name, Last Name, Phone Number, Gender, City, and Region.

---

### 3.3 Role: Owner (Super Admin)
The Owner has global rights and specific oversight capabilities.

**3.3.1 Global Visibility**
*   **Total Hierarchy View:** The Owner shall view *all* users (Managers, Superagents, Jesters) regardless of which branch they belong to.
*   **Transaction Auditing:**
    *   **Agent/Admin View:** View all transfers and activities performed by Superagents and Managers.
    *   **Jester View:** View specific "Package Transactions" (credits received) and "Game Transactions" (gameplay profit/loss) for any Jester.

**3.3.2 Credit Distribution (Packages)**
*   **Send Package:** The system shall allow the Owner to search for any specific agent (Manager, Superagent, or Jester) from the database.
*   **Input:** The Owner shall input the package amount (e.g., 5000) and execute the transfer to credit that user’s balance.

**3.3.3 Account Creation**
*   **Create Roles:** The Owner can register new accounts for **Managers, Superagents, and Jesters**.
*   **Required Fields:** First Name, Last Name, Phone Number, City, Region, Password.

---

### 3.4 Role: Manager
**3.4.1 Hierarchy Management**
*   **Create Roles:** The Manager shall be able to register new accounts for **Superagents and Jesters**. (Note: Managers cannot create Owners).
*   **Required Fields:** First Name, Last Name, Phone Number, City, Region, Password.

**3.4.2 Transaction Monitoring**
*   The Manager can view package and game transactions for all Superagents and Jesters under their management.

---

### 3.5 Role: Superagent
**3.5.1 Hierarchy Management**
*   **Create Roles:** The Superagent shall *only* be able to register new accounts for **Jesters**.
*   **Required Fields:** First Name, Last Name, Phone Number, City, Region, Password.

**3.5.2 Transaction Monitoring**
*   The Superagent can view package and game transactions for Jesters under their supervision.

---

## 4. Data Requirements

### 4.1 User Profile Data Model
The database must store the following for every role:
*   First Name
*   Last Name
*   Phone Number
*   Gender
*   City
*   Region
*   Password (Encrypted)
*   Role Type (Owner, Manager, Superagent, Jester)
*   Current Wallet Balance
*   Superior ID (Who created/manages them)

### 4.2 Transaction Logs
The system must log two distinct types of financial movements:
1.  **Package Transaction:** Date, Sender, Receiver, Amount.
2.  **Game Transaction:** Date, Jester ID, Total Bets, Cut Amount, Winner Payout, Net Profit/Loss.

---

## 5. System Logic Summary (Role Matrix)

| Feature | Owner | Manager | Superagent | Jester |
| :--- | :---: | :---: | :---: | :---: |
| **Start/End Game** | No | No | No | **Yes** |
| **Request Package** | No | No | No | **Yes** |
| **Send Package** | **Yes (To All)** | Yes (To Subordinates) | Yes (To Subordinates) | No |
| **Add Manager** | **Yes** | No | No | No |
| **Add Superagent** | **Yes** | **Yes** | No | No |
| **Add Jester** | **Yes** | **Yes** | **Yes** | No |
| **View Global Users**| **Yes** | No (Branch only) | No (Branch only) | No |
| **View Game Trans.** | **Yes** | Yes (Downstream) | Yes (Downstream) | Own only |

