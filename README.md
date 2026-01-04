# 🧠 TradeBrain API

**TradeBrain** is an autonomous, AI-powered trading intelligence platform that identifies high-probability swing trading opportunities in the Indian Market (NSE/BSE) using a "Triple Confirmation" logic engine.

Unlike simple screeners, TradeBrain acts as a disciplined analyst: checking Technicals, Fundamentals, and News Catalysts before generating a signal. It combines real-time market data, AI-driven analysis, and automated risk management to deliver actionable trading setups.

---

## 📚 Documentation Hub

* **[🏛️ System Architecture](docs/architecture.md)**
    * The "Brain" of the system. Explains the Discovery → Analysis → Validation → Audit pipeline.
* **[🗄️ Domain Models & Database](docs/domain_models.md)**
    * The Source of Truth for the DB Schema, Enums, Indexes, and Integrity Rules.
* **[🔌 API Specification](docs/api_spec.md)**
    * Detailed Endpoint definitions with **Request/Response JSON examples**.

---

## 🚀 Core Features

* **24/7 Market Scanning**: Autonomous background workers monitor watchlists and "Stocks in Play".
* **Triple Confirmation**: AI Analysis based on Technicals + Fundamentals + Catalysts.
* **Optimization Engine**: Smart caching prevents redundant AI calls (checks price variance < 0.5%).
* **Risk Management**: "Math Police" validation (e.g., Risk/Reward ≥ 1:2) enforced before DB entry.
* **Signal Auditing**: Automated "The Truth" checks against live prices to update signal status.
* **Paper Trading**: Virtual portfolio management to track signal performance.

---

## 🏗️ Project Structure

The project follows a strict "Engine vs. API" separation of concerns:

```bash
TradeBrain_api/
├── app/
│   ├── api/            # The Face: REST API Endpoints (FastAPI)
│   ├── engine/         # The Brain: Background Intelligence (Scanner, Validator)
│   ├── models/         # Database Schemas (SQLAlchemy)
│   ├── repositories/   # Data Access Layer
│   ├── services/       # Business Logic & Orchestration
│   └── core/           # Config, Logging, Security
└── tests/              # Unit and Integration Tests
```

---

## 🚀 Tech Stack

| Component | Technology |
| --- | --- |
| **Core Framework** | Python 3.13+, FastAPI |
| **Database** | PostgreSQL (Async via SQLAlchemy 2.0) |
| **AI Engine** | Google Gemini Flash (1.5/2.0) |
| **Data Sources** | yfinance, Tavily Search API |
| **Scheduling** | APScheduler (Cron Jobs) |
| **Authentication** | JWT (PyJWT) with Session Tracking |
| **Validation** | Pydantic v2 |

---

## 🔧 Installation & Setup

### Prerequisites

* Python 3.13+
* PostgreSQL 14+
* Docker & Docker Compose (optional)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/sudama011/tradebrain.git
cd tradebrain

```


2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

```


3. **Install dependencies**
```bash
pip install -r requirements-dev.txt

```


4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys (Gemini, Tavily) and Database URL

```


5. **Initialize database**
```bash
make db-migrate
make db-seed

```


6. **Run the server**
```bash
make run
# Or: uvicorn app.main:app --reload

```



The API will be available at `http://localhost:8000`

* **API Docs**: http://localhost:8000/docs
* **ReDoc**: http://localhost:8000/redoc

### Docker Setup

```bash
docker-compose up -d
# Database will be available at localhost:5432
# API will be available at localhost:8000

```
