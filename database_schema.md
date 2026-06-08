# Database Schema

ChargeHub uses PostgreSQL as its primary data store, accessed asynchronously via SQLAlchemy 2.0. Below is a high-level overview of the core tables and relationships.

## 1. `users` Table
Stores authentication and authorization information for residents and admins.
- `id` (UUID, Primary Key)
- `email` (String, Unique)
- `hashed_password` (String)
- `role` (Enum: `admin`, `resident`) - Defines access level. Admins manage hardware; residents can only start/stop sessions.
- `coin_balance` (Float) - The virtual currency balance of the user used to pay for charging sessions.
- `created_at` (DateTime)

## 2. `plugs` Table
Represents the physical TP-Link Tapo P110 smart plugs.
- `id` (UUID, Primary Key)
- `name` (String) - e.g., "Parking Bay 1"
- `ip_address` (String) - Local LAN IP address (e.g., `192.168.1.50`)
- `status` (Enum: `online`, `offline`, `in_use`)
- `current_power_w` (Float) - Live wattage consumption. Updated periodically by the `scheduler.py`.
- `last_seen_at` (DateTime)

## 3. `charging_sessions` Table
The central transactional record tying a user, a plug, and power consumption together.
- `id` (Integer, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `plug_id` (UUID, Foreign Key -> `plugs.id`)
- `status` (Enum: `active`, `completed`, `failed`)
- `start_time` (DateTime)
- `end_time` (DateTime, Nullable)
- `total_kwh_consumed` (Float) - Accumulates as the scheduler polls the plug.
- `total_cost_coins` (Float) - Derived from `total_kwh_consumed` * `COINS_PER_KWH` plus any time-based fees.

## 4. `coin_transactions` Table
An audit log of all coin movements to ensure billing accuracy.
- `id` (Integer, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `amount` (Float) - Positive for top-ups, negative for session deductions.
- `transaction_type` (Enum: `topup`, `charging_fee`, `admin_adjustment`)
- `session_id` (Integer, Foreign Key -> `charging_sessions.id`, Nullable)
- `created_at` (DateTime)

## 5. `payments` Table (Optional / External)
Tracks external fiat transactions (e.g., via Stripe) used to purchase coins.
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `stripe_payment_intent_id` (String)
- `fiat_amount` (Float)
- `status` (Enum: `pending`, `succeeded`, `failed`)
- `coins_credited` (Float)

## Relationships
- **User -> Sessions**: One-to-Many
- **Plug -> Sessions**: One-to-Many (though only one *active* session per plug at a time).
- **User -> Coin Transactions**: One-to-Many

## Migrations
(If Alembic is configured, mention `alembic upgrade head` here. If tables are created on startup via `init_db()`, mention that `main.py` handles the schema creation during `lifespan`.)
