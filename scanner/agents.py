import json

import google.genai as genai

client = genai.Client()


def analyze_opportunity(ticker, market_data, news_context):
    """
    Sends data to Gemini 1.5 Flash and returns a JSON decision.
    """

    prompt = f"""
    ROLE: You are a strict, cynical financial analyst. You only care about FACTS.

    TASK: Analyze the following stock data and news.

    STOCK: {ticker}
    PRICE DATA: {market_data}
    NEWS CONTEXT:
    {news_context}

    INSTRUCTIONS:
    1. Ignore vague opinion pieces. Look for hard numbers (Earnings, Orders, Tax changes).
    2. Suggest a trade ONLY if confidence is > 75%.
    3. Calculate sensible Stoploss (approx 2-3% below) and Target (approx 5-6% above) based on current price.

    OUTPUT FORMAT (Strict JSON):
    {{
        "action": "BUY" | "SELL" | "HOLD",
        "confidence_score": 0-100,
        "reasoning": "Brief summary of the specific fact causing this move.",
        "entry_price": {market_data['current_price']},
        "target_price": 0.0,
        "stop_loss": 0.0
    }}
    """

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        print(text)
        return json.loads(text)
    except Exception as e:
        print(f"❌ AI Error for {ticker}: {e}")
        return None
