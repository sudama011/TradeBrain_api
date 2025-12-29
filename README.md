# 🧠 TradeBrain API

**TradeBrain** is a personal, AI-powered stock market assistant designed to identify high-probability swing trading opportunities in the Indian Market (NSE/BSE).

It uses a "Scanner" architecture to analyze market data and news 24/7, storing actionable signals in a database for the mobile app to consume.

## 🚀 Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **AI/LLM:** LangChain + Gemini 1.5 Flash / OpenAI
- **Data Source:** yfinance / Angel One SmartAPI / Tavily Search

## 📂 Project Structure

- `app/`: Main FastAPI application.
- `app/api/`: API Endpoints (Routes).
- `scanner/`: Background worker logic (Cron jobs & AI Agents).
- `Makefile`: Command shortcuts.

## 🛠️ Setup

1. **Create Virtual Env:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate