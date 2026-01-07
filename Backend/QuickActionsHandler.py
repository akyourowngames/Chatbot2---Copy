"""
Quick Actions Command Handler
==============================
Intercepts @commands (@news, @weather, @crypto, @github) and routes to real APIs.
"""

import logging
import re
from typing import Dict, Any, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickActionsHandler:
    """Handles quick action commands before they reach the LLM."""
    
    def __init__(self):
        self.command_patterns = {
            'news': r'@news\s+(.+)',
            'weather': r'@weather\s+(.+)',
            'crypto': r'@crypto\s+(.+)',
            'github': r'@github\s+(.+)'
        }
        logger.info("[QUICK-ACTIONS] Handler initialized")
    
    def detect_command(self, message: str) -> Optional[Tuple[str, str]]:
        """
        Detect if message contains a quick action command.
        
        Args:
            message: User message
            
        Returns:
            Tuple of (command_type, param) if found, None otherwise
        """
        message = message.strip()
        
        for cmd_type, pattern in self.command_patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                param = match.group(1).strip()
                return (cmd_type, param)
        
        return None
    
    def handle_news(self, query: str) -> Dict[str, Any]:
        """
        Handle @news command.
        
        Args:
            query: Category or search term (e.g., "sports", "technology")
        """
        from Backend.NewsService import news_service
        
        # Common categories
        categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
        
        # Check if query is a category
        query_lower = query.lower()
        category = None
        for cat in categories:
            if cat in query_lower:
                category = cat
                break
        
        if category:
            # Fetch headlines by category
            result = news_service.get_top_headlines(category=category)
        else:
            # Search news
            result = news_service.search_news(query)
        
        if result.get('status') == 'success':
            articles = result.get('articles', [])
            
            if not articles:
                return {
                    "status": "success",
                    "trigger": "news",
                    "data": {
                        "message": f"No news found for '{query}'"
                    }
                }
            
            # Format response
            headlines = []
            for i, article in enumerate(articles[:5], 1):
                headlines.append({
                    "title": article['title'],
                    "source": article['source'],
                    "url": article['url'],
                    "description": article['description']
                })
            
            return {
                "status": "success",
                "trigger": "news",
                "data": {
                    "query": query,
                    "category": category or "search",
                    "total": result.get('total_results', 0),
                    "headlines": headlines
                }
            }
        else:
            return {
                "status": "error",
                "trigger": "news",
                "data": {
                    "message": f"Failed to fetch news: {result.get('message', 'Unknown error')}"
                }
            }
    
    def handle_weather(self, location: str) -> Dict[str, Any]:
        """
        Handle @weather command.
        
        Args:
            location: City name
        """
        from Backend.WeatherService import weather_service
        
        result = weather_service.get_weather(city=location)
        
        if result.get('status') == 'success':
            current = result['current']
            location_info = result['location']
            
            return {
                "status": "success",
                "trigger": "weather",
                "data": {
                    "city": location_info['city'],
                    "country": location_info['country'],
                    "temperature": current['temperature'],
                    "feels_like": current['feels_like'],
                    "description": current['description'],
                    "humidity": current['humidity'],
                    "wind_speed": current['wind_speed'],
                    "icon": current['icon']
                }
            }
        else:
            return {
                "status": "error",
                "trigger": "weather",
                "data": {
                    "message": f"Failed to fetch weather for {location}"
                }
            }
    
    def handle_crypto(self, query: str) -> Dict[str, Any]:
        """
        Handle @crypto command.
        
        Args:
            query: Coin name or "prices" for top coins
        """
        from Backend.CryptoService import crypto_service
        
        query_lower = query.lower()
        
        if query_lower in ['prices', 'top', 'list']:
            # Get top cryptos
            result = crypto_service.get_prices()
        else:
            # Search for specific coin
            search_result = crypto_service.search_coins(query)
            
            if search_result.get('status') == 'success' and search_result.get('results'):
                coin_id = search_result['results'][0]['id']
                result = crypto_service.get_prices(coins=[coin_id])
            else:
                return {
                    "status": "error",
                    "trigger": "crypto",
                    "data": {
                        "message": f"Cryptocurrency '{query}' not found"
                    }
                }
        
        if result.get('status') == 'success':
            coins = result.get('coins', [])
            
            if not coins:
                return {
                    "status": "error",
                    "trigger": "crypto",
                    "data": {
                        "message": "No cryptocurrency data available"
                    }
                }
            
            # For single coin, return detailed info
            if len(coins) == 1:
                coin = coins[0]
                return {
                    "status": "success",
                    "trigger": "crypto",
                    "data": {
                        "name": coin['name'],
                        "symbol": coin['symbol'],
                        "price": coin['current_price'],
                        "change_24h": coin['price_change_24h'],
                        "market_cap": coin['market_cap'],
                        "market_cap_rank": coin['market_cap_rank'],
                        "single_coin": True
                    }
                }
            else:
                # Multiple coins - return list
                coin_list = []
                for coin in coins[:10]:
                    coin_list.append({
                        "name": coin['name'],
                        "symbol": coin['symbol'],
                        "price": coin['current_price'],
                        "change_24h": coin['price_change_24h'],
                        "rank": coin['market_cap_rank']
                    })
                
                return {
                    "status": "success",
                    "trigger": "crypto",
                    "data": {
                        "coins": coin_list,
                        "single_coin": False
                    }
                }
        else:
            return {
                "status": "error",
                "trigger": "crypto",
                "data": {
                    "message": "Failed to fetch cryptocurrency data"
                }
            }
    
    def handle_github(self, query: str) -> Dict[str, Any]:
        """
        Handle @github command.
        
        Args:
            query: Username, "trending", or search term
        """
        from Backend.GitHubService import github_service
        
        query_lower = query.lower()
        
        if query_lower.startswith('trending'):
            # Extract language if specified
            parts = query.split()
            language = parts[1] if len(parts) > 1 else ''
            result = github_service.get_trending_repos(language=language)
            
            if result.get('status') == 'success':
                repos = result.get('trending', [])[:5]
                return {
                    "status": "success",
                    "trigger": "github",
                    "data": {
                        "type": "trending",
                        "language": language or "all",
                        "repos": repos
                    }
                }
        else:
            # Treat as username
            result = github_service.get_user_repos(username=query)
            
            if result.get('status') == 'success':
                repos = result.get('repos', [])[:5]
                return {
                    "status": "success",
                    "trigger": "github",
                    "data": {
                        "type": "user_repos",
                        "username": query,
                        "repos": repos
                    }
                }
        
        return {
            "status": "error",
            "trigger": "github",
            "data": {
                "message": f"Failed to fetch GitHub data for '{query}'"
            }
        }
    
    def process_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Process message and execute command if found.
        
        Args:
            message: User message
            
        Returns:
            Command result if command was found and executed, None otherwise
        """
        command = self.detect_command(message)
        
        if not command:
            return None
        
        cmd_type, param = command
        logger.info(f"[QUICK-ACTIONS] Detected: {cmd_type} with param: {param}")
        
        try:
            if cmd_type == 'news':
                return self.handle_news(param)
            elif cmd_type == 'weather':
                return self.handle_weather(param)
            elif cmd_type == 'crypto':
                return self.handle_crypto(param)
            elif cmd_type == 'github':
                return self.handle_github(param)
        except Exception as e:
            logger.error(f"[QUICK-ACTIONS] Error handling {cmd_type}: {e}")
            return {
                "status": "error",
                "trigger": cmd_type,
                "data": {
                    "message": f"Error processing {cmd_type} command: {str(e)}"
                }
            }
        
        return None


# Global instance
quick_actions_handler = QuickActionsHandler()


# Test
if __name__ == "__main__":
    print("🚀 Testing Quick Actions Handler\n")
    
    handler = QuickActionsHandler()
    
    # Test news
    result = handler.process_message("@news sports")
    print(f"News test: {result.get('status')}")
    
    # Test weather
    result = handler.process_message("@weather London")
    print(f"Weather test: {result.get('status')}")
    
    # Test crypto
    result = handler.process_message("@crypto bitcoin")
    print(f"Crypto test: {result.get('status')}")
