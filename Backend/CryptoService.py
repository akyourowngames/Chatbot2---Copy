"""
Real-Time Crypto Price Service
==============================
Provides real cryptocurrency prices using CoinGecko API (free, no auth needed).
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoService:
    """Real-time cryptocurrency price service using CoinGecko API."""
    
    def __init__(self):
        """Initialize crypto service."""
        self.base_url = "https://api.coingecko.com/api/v3"
        self._cache = {}
        self._cache_duration = timedelta(minutes=5)  # Cache for 5 mins
        logger.info("[CRYPTO] Service initialized")
    
    def get_prices(self, coins: List[str] = None, vs_currency: str = "usd") -> Dict[str, Any]:
        """
        Get current prices for cryptocurrencies.
        
        Args:
            coins: List of coin IDs (e.g., ["bitcoin", "ethereum"])
                  If None, returns top 10 by market cap
            vs_currency: Currency to compare against (default: usd)
            
        Returns:
            Price data dictionary
        """
        try:
            # Check cache
            cache_key = f"{','.join(coins or ['top10'])}_{vs_currency}"
            if cache_key in self._cache:
                cached_data, cached_time = self._cache[cache_key]
                if datetime.now() - cached_time < self._cache_duration:
                    logger.info(f"[CRYPTO] Returning cached data")
                    return cached_data
            
            # Build request
            params = {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": len(coins) if coins else 10,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h,7d"
            }
            
            if coins:
                params["ids"] = ",".join(coins)
            
            url = f"{self.base_url}/coins/markets"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            coins_data = []
            for coin in data:
                coins_data.append({
                    "id": coin["id"],
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "image": coin["image"],
                    "current_price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "market_cap_rank": coin["market_cap_rank"],
                    "price_change_24h": round(coin.get("price_change_percentage_24h", 0), 2),
                    "price_change_7d": round(coin.get("price_change_percentage_7d_in_currency", 0), 2),
                    "high_24h": coin.get("high_24h"),
                    "low_24h": coin.get("low_24h"),
                    "total_volume": coin.get("total_volume"),
                    "circulating_supply": coin.get("circulating_supply")
                })
            
            result = {
                "status": "success",
                "currency": vs_currency.upper(),
                "coins": coins_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache result
            self._cache[cache_key] = (result, datetime.now())
            
            logger.info(f"[CRYPTO] Fetched prices for {len(coins_data)} coins")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[CRYPTO] API request failed: {e}")
            return {
                "status": "error",
                "error": "Failed to fetch crypto prices",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"[CRYPTO] Unexpected error: {e}")
            return {
                "status": "error",
                "error": "Crypto service error",
                "message": str(e)
            }
    
    def get_coin_details(self, coin_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific cryptocurrency.
        
        Args:
            coin_id: Coin ID (e.g., "bitcoin")
            
        Returns:
            Detailed coin data
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                "localization": False,
                "tickers": False,
                "community_data": False,
                "developer_data": False
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": "success",
                "coin": {
                    "id": data["id"],
                    "symbol": data["symbol"].upper(),
                    "name": data["name"],
                    "description": data.get("description", {}).get("en", "")[:500],
                    "image": data["image"]["large"],
                    "current_price": data["market_data"]["current_price"]["usd"],
                    "market_cap": data["market_data"]["market_cap"]["usd"],
                    "market_cap_rank": data["market_cap_rank"],
                    "ath": data["market_data"]["ath"]["usd"],
                    "ath_date": data["market_data"]["ath_date"]["usd"],
                    "atl": data["market_data"]["atl"]["usd"],
                    "atl_date": data["market_data"]["atl_date"]["usd"],
                    "price_change_24h": round(data["market_data"]["price_change_percentage_24h"], 2),
                    "price_change_7d": round(data["market_data"]["price_change_percentage_7d"], 2),
                    "price_change_30d": round(data["market_data"]["price_change_percentage_30d"], 2)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[CRYPTO] Failed to fetch coin details: {e}")
            return {
                "status": "error",
                "error": "Failed to fetch coin details",
                "message": str(e)
            }
    
    def search_coins(self, query: str) -> Dict[str, Any]:
        """
        Search for cryptocurrencies by name or symbol.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        try:
            url = f"{self.base_url}/search"
            params = {"query": query}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            coins = [
                {
                    "id": coin["id"],
                    "name": coin["name"],
                    "symbol": coin["symbol"].upper(),
                    "market_cap_rank": coin.get("market_cap_rank"),
                    "thumb": coin.get("thumb")
                }
                for coin in data.get("coins", [])[:10]  # Top 10 results
            ]
            
            return {
                "status": "success",
                "query": query,
                "results": coins,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[CRYPTO] Search failed: {e}")
            return {
                "status": "error",
                "error": "Search failed",
                "message": str(e)
            }


# Global instance
crypto_service = CryptoService()


# Convenience functions
def get_crypto_prices(coins: List[str] = None) -> Dict[str, Any]:
    """Get cryptocurrency prices."""
    return crypto_service.get_prices(coins=coins)


def search_crypto(query: str) -> Dict[str, Any]:
    """Search for cryptocurrencies."""
    return crypto_service.search_coins(query)


# Test
if __name__ == "__main__":
    print("₿ Testing Crypto Service\n")
    
    # Test top cryptos
    prices = get_crypto_prices()
    if prices["status"] == "success":
        print(f"💰 Top {len(prices['coins'])} Cryptocurrencies:\n")
        for coin in prices["coins"][:5]:
            change_emoji = "🟢" if coin["price_change_24h"] > 0 else "🔴"
            print(f"{coin['market_cap_rank']}. {coin['name']} ({coin['symbol']})")
            print(f"   ${coin['current_price']:,.2f} {change_emoji} {coin['price_change_24h']:+.2f}% (24h)")
            print()
    
    # Test search
    search_results = search_crypto("ethereum")
    if search_results["status"] == "success":
        print(f"\n🔍 Search results for '{search_results['query']}':")
        for coin in search_results["results"][:3]:
            print(f"  - {coin['name']} ({coin['symbol']})")
