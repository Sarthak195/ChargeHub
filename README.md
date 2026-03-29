# ChargeHub

ChargeHub is an open-source, locally run EV charging management system designed for apartment complexes. It integrates directly with TP-Link Tapo P110 smart plugs over the local area network (LAN), bypassing the need for cloud dependency while offering a complete full-stack solution to manage charging sessions, coin-based billing, user authentication, and multi-tenant access.

<p align="center">
  <img src="frontend/public/vite.svg" alt="ChargeHub Logo" width="100"/>
</p>

## ✨ Features

- **Local LAN Control:** Securely controls TP-Link Tapo P110 plugs locally. Built for privacy, reducing cloud latency and completely avoiding third-party downtimes.
- **Coin-based Billing System:** Allows residents to use virtual coins to pay for charging.
- **Real-Time Dashboards:** Real-time energy monitoring with dynamic SSE (Server-Sent Events) providing live Watt and kWh reporting.
- **Role-Based Access:** Segregates user access between standard "Residents" and "Admins". Admins can add/remove chargers and credit user balances manually.
- **Dynamic Dark UI:** Modern, responsive, and glassmorphic UI built in React meant to look sleek and operate smoothly across devices.
- **Dockerized Deployments:** Contains both the frontend and backend in simple containers preventing "Works on my machine" syndromes.

## 🏗️ Architecture Stack

- **Frontend:** React + Vite, TypeScript, Lucide React (Icons).
- **Backend:** FastAPI (Python 3.11), SQLAlchemy 2 (Async), PostgreSQL.
- **Hardware Integration:** Python-Kasa / Tapo library.

## 🚀 Quickstart Installation (1-Command Deploy)

ChargeHub can be booted up on any machine with Docker installed. You only need to run a single setup script. 

### Prerequisites
- **Docker Engine & Docker Compose** installed.
- TP-Link Tapo Account credentials (for initial plug handshakes).
- A local Kasa/Tapo P110 plug connected to your local network.

### 1-Click Setup

**For Windows (PowerShell):**
```powershell
.\setup.ps1
```

**For Linux/Mac (Bash):**
```bash
bash setup.sh
```

**What the setup script does:**
1. Clones `.env.example` to `.env` if not present.
2. Prompts you to update your `TAPO_USERNAME` and `TAPO_PASSWORD` in `.env`.
3. Runs `docker compose up --build -d`.
4. Executes the initial backend Database Migrations / Seeding.

---

## 🔧 Environment Configuration

You'll need a `.env` file at the root. The setup script will copy `.env.example` into `.env` for you.
Here are the critical keys you must configure:

```ini
TAPO_USERNAME=your_tplink_email@example.com
TAPO_PASSWORD=your_tplink_password

# Optional: Stripe (For automatic coin top-ups)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Coin Logic Variables
COINS_PER_KWH=10.0
COINS_PER_MINUTE=0.5
COIN_TOPUP_RATE=0.10
```

---

## 🔑 Default Credentials

If the database is successfully seeded, the following admin user will be created:

| **Access Level** | **Email** | **Password** |
| :--- | :--- | :--- |
| **Admin** | `admin@chargehub.local` | `admin123` |

Log in to the frontend dashboard and head over to the **Admin** panel to register your local `192.168.1.X` plugs.

---

## 🖥️ Exposed Ports

After running Docker Compose, you can access:
- **Frontend App:** [http://localhost:5173](http://localhost:5173)
- **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL Database:** `localhost:5432`

## ⚠️ Notes for Docker Desktop (Windows/Mac)

By default, Docker for Desktop runs in a virtual machine that intercepts UDP broadcast traffic. For Tapo/Kasa discovery and monitoring, this limits standard UDP discovery. The app uses direct IP connections (`discover_single`) instead. Ensure you provide **static IP addresses** for your smart plugs via your router's DHCP reservation or bindings for full stability!
