"""
Advanced Integrations - Connect JARVIS to Everything
=====================================================
Integrations with popular services and APIs
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class AdvancedIntegrations:
    def __init__(self):
        self.api_keys = self._load_api_keys()
        
    def _load_api_keys(self) -> Dict:
        """Load API keys from environment"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        return {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "weather": os.getenv("WEATHER_API_KEY", ""),
            "news": os.getenv("NEWS_API_KEY", ""),
            "spotify": os.getenv("SPOTIFY_API_KEY", ""),
            "github": os.getenv("GITHUB_TOKEN", ""),
        }
    
    # ==================== WEATHER ====================
    
    def get_weather(self, city: str = "London") -> Dict:
        """Get current weather"""
        try:
            # Using free OpenWeatherMap API
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                
                return {
                    "city": city,
                    "temperature": f"{current['temp_C']}°C",
                    "feels_like": f"{current['FeelsLikeC']}°C",
                    "condition": current['weatherDesc'][0]['value'],
                    "humidity": f"{current['humidity']}%",
                    "wind": f"{current['windspeedKmph']} km/h"
                }
        except:
            pass
        
        return {"error": "Could not fetch weather"}
    
    def get_forecast(self, city: str = "London", days: int = 3) -> List[Dict]:
        """Get weather forecast"""
        try:
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                forecast = []
                
                for day in data['weather'][:days]:
                    forecast.append({
                        "date": day['date'],
                        "max_temp": f"{day['maxtempC']}°C",
                        "min_temp": f"{day['mintempC']}°C",
                        "condition": day['hourly'][0]['weatherDesc'][0]['value']
                    })
                
                return forecast
        except:
            pass
        
        return []
    
    # ==================== NEWS ====================
    
    def get_news(self, topic: str = "technology", limit: int = 5) -> List[Dict]:
        """Get latest news"""
        try:
            # Using free NewsAPI
            url = f"https://newsapi.org/v2/everything?q={topic}&pageSize={limit}&apiKey=demo"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get('articles', [])[:limit]:
                    articles.append({
                        "title": article['title'],
                        "description": article['description'],
                        "url": article['url'],
                        "source": article['source']['name'],
                        "published": article['publishedAt']
                    })
                
                return articles
        except:
            pass
        
        return []
    
    # ==================== CRYPTO ====================
    
    def get_crypto_price(self, symbol: str = "bitcoin") -> Dict:
        """Get cryptocurrency price"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if symbol in data:
                    return {
                        "symbol": symbol,
                        "price": f"${data[symbol]['usd']:,.2f}",
                        "change_24h": f"{data[symbol]['usd_24h_change']:.2f}%"
                    }
        except:
            pass
        
        return {"error": "Could not fetch price"}
    
    # ==================== STOCKS ====================
    
    def get_stock_price(self, symbol: str = "AAPL") -> Dict:
        """Get stock price"""
        try:
            # Using free Alpha Vantage API
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=demo"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                
                if quote:
                    return {
                        "symbol": symbol,
                        "price": quote.get('05. price', 'N/A'),
                        "change": quote.get('09. change', 'N/A'),
                        "change_percent": quote.get('10. change percent', 'N/A')
                    }
        except:
            pass
        
        return {"error": "Could not fetch stock price"}
    
    # ==================== GITHUB ====================
    
    def get_github_repos(self, username: str) -> List[Dict]:
        """Get user's GitHub repositories"""
        try:
            url = f"https://api.github.com/users/{username}/repos"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                repos = response.json()
                return [{
                    "name": repo['name'],
                    "description": repo['description'],
                    "stars": repo['stargazers_count'],
                    "language": repo['language'],
                    "url": repo['html_url']
                } for repo in repos[:10]]
        except:
            pass
        
        return []
    
    # ==================== QUOTES ====================
    
    def get_quote(self) -> Dict:
        """Get inspirational quote"""
        try:
            url = "https://api.quotable.io/random"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "quote": data['content'],
                    "author": data['author']
                }
        except:
            pass
        
        return {"quote": "Stay focused and never give up!", "author": "JARVIS"}
    
    # ==================== JOKES ====================
    
    def get_joke(self) -> str:
        """Get a random joke"""
        try:
            url = "https://official-joke-api.appspot.com/random_joke"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return f"{data['setup']} - {data['punchline']}"
        except:
            pass
        
        return "Why did the AI go to school? To improve its learning rate!"
    
    # ==================== FACTS ====================
    
    def get_fact(self) -> str:
        """Get random fact"""
        try:
            url = "https://uselessfacts.jsph.pl/random.json?language=en"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data['text']
        except:
            pass
        
        return "AI assistants are becoming increasingly sophisticated!"
    
    # ==================== DICTIONARY ====================
    
    def define_word(self, word: str) -> Dict:
        """Get word definition"""
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()[0]
                meanings = data['meanings'][0]
                
                return {
                    "word": word,
                    "phonetic": data.get('phonetic', ''),
                    "definition": meanings['definitions'][0]['definition'],
                    "example": meanings['definitions'][0].get('example', ''),
                    "part_of_speech": meanings['partOfSpeech']
                }
        except:
            pass
        
        return {"error": "Word not found"}
    
    # ==================== IP INFO ====================
    
    def get_ip_info(self) -> Dict:
        """Get IP information"""
        try:
            url = "https://ipapi.co/json/"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "ip": data.get('ip', ''),
                    "city": data.get('city', ''),
                    "region": data.get('region', ''),
                    "country": data.get('country_name', ''),
                    "timezone": data.get('timezone', '')
                }
        except:
            pass
        
        return {"error": "Could not fetch IP info"}

# Global instance
integrations = AdvancedIntegrations()

if __name__ == "__main__":
    # Test integrations
    print("🌤️ Weather:")
    print(integrations.get_weather("London"))
    
    print("\n📰 News:")
    news = integrations.get_news("AI", limit=3)
    for article in news:
        print(f"  - {article['title']}")
    
    print("\n💰 Crypto:")
    print(integrations.get_crypto_price("bitcoin"))
    
    print("\n💡 Quote:")
    print(integrations.get_quote())
    
    print("\n😄 Joke:")
    print(integrations.get_joke())
