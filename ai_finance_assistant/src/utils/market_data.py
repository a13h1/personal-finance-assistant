import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
import time


class MarketDataService:
    def __init__(self, cache_ttl: int = 300):
        self._cache: Dict = {}
        self._cache_ttl = cache_ttl

    def _is_cached(self, key: str) -> bool:
        if key not in self._cache:
            return False
        return time.time() - self._cache[key]['timestamp'] < self._cache_ttl

    def get_quote(self, symbol: str) -> Optional[Dict]:
        cache_key = f"quote_{symbol}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]['data']

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            quote = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "change_pct": info.get("regularMarketChangePercent"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "volume": info.get("regularMarketVolume"),
                "sector": info.get("sector"),
            }
            self._cache[cache_key] = {'data': quote, 'timestamp': time.time()}
            return quote
        except Exception as e:
            return None

    def get_historical(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        cache_key = f"hist_{symbol}_{period}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]['data']

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            self._cache[cache_key] = {'data': hist, 'timestamp': time.time()}
            return hist
        except Exception:
            return None

    def get_multiple_quotes(self, symbols: List[str]) -> Dict:
        return {s: self.get_quote(s) for s in symbols}

    def get_market_indices(self) -> Dict:
        indices = {"^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ", "^VIX": "VIX"}
        result = {}
        for symbol, name in indices.items():
            quote = self.get_quote(symbol)
            if quote:
                result[name] = quote
        return result

    def get_news(self, symbol: str) -> List[Dict]:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            return news[:5] if news else []
        except Exception:
            return []

    def analyze_portfolio(self, holdings: List[Dict]) -> Dict:
        """holdings: [{"symbol": "AAPL", "shares": 10, "avg_cost": 150.0}]"""
        analysis = {
            "holdings": [],
            "total_value": 0,
            "total_cost": 0,
            "sector_allocation": {},
            "errors": [],
        }

        for holding in holdings:
            symbol = holding.get("symbol", "").upper()
            shares = float(holding.get("shares", 0))
            avg_cost = float(holding.get("avg_cost", 0))

            quote = self.get_quote(symbol)
            if not quote or not quote.get("price"):
                analysis["errors"].append(f"Could not fetch data for {symbol}")
                continue

            current_price = quote["price"]
            current_value = current_price * shares
            cost_basis = avg_cost * shares
            gain_loss = current_value - cost_basis
            gain_loss_pct = ((current_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

            holding_info = {
                "symbol": symbol,
                "name": quote.get("name", symbol),
                "shares": shares,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "current_value": current_value,
                "gain_loss": gain_loss,
                "gain_loss_pct": gain_loss_pct,
                "sector": quote.get("sector", "Unknown"),
            }
            analysis["holdings"].append(holding_info)
            analysis["total_value"] += current_value
            analysis["total_cost"] += cost_basis

            sector = quote.get("sector", "Unknown") or "Unknown"
            analysis["sector_allocation"][sector] = analysis["sector_allocation"].get(sector, 0) + current_value

        if analysis["total_cost"] > 0:
            analysis["total_gain_loss"] = analysis["total_value"] - analysis["total_cost"]
            analysis["total_gain_loss_pct"] = (analysis["total_gain_loss"] / analysis["total_cost"]) * 100

        # Convert sector allocation to percentages
        if analysis["total_value"] > 0:
            analysis["sector_allocation_pct"] = {
                k: (v / analysis["total_value"]) * 100
                for k, v in analysis["sector_allocation"].items()
            }

        return analysis
