# 🧠 TradeBrain API

**TradeBrain** is an autonomous, AI-powered trading intelligence platform that identifies high-probability swing trading opportunities in the Indian Market (NSE/BSE) using a "Triple Confirmation" logic engine.

Unlike simple screeners, TradeBrain acts as a disciplined analyst: checking Technicals, Fundamentals, and News Catalysts before generating a signal. It combines real-time market data, AI-driven analysis, and automated risk management to deliver actionable trading setups.

## 🚀 Core Features

* **24/7 Market Scanning**: Automatically monitors a custom watchlist of tickers and discovers new "stocks in play" through news analysis.
* **Triple Confirmation Analysis**: Every opportunity is analyzed across Technical, Fundamental, and Catalyst layers using AI.
* **Smart Optimization Engine**: Built-in "Gatekeeper" prevents redundant AI calls by skipping scans when price action or news hasn't changed (saves API costs).
* **Risk Management ("Math Police")**: Dedicated validation layer ensures every signal meets strict financial logic (1:2 Risk/Reward minimum).
* **Automated Auditing**: Background engine tracks active signals against live prices to determine if they hit targets or stop losses.
* **Paper Trading**: Users can "take" a signal to create a paper trade and track performance.
* **Notifications**: Real-time alerts for new signals, target hits, and stop losses.
* **Admin Tools**: Seed data, manage users, and monitor system health.

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

---

## 📚 Documentation

* **[Architecture](https://www.google.com/search?q=docs/architecture.md)** - System design & data flow
* **[API Reference](https://www.google.com/search?q=docs/api.md)** - Complete endpoint documentation
* **[Models](https://www.google.com/search?q=docs/models.md)** - Database schema documentation
* **[Implementation](https://www.google.com/search?q=docs/implementation.md)** - Technical implementation details
