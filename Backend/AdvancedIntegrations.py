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
            "figma": os.getenv("FIGMA_ACCESS_TOKEN", ""),
            "notion": os.getenv("NOTION_API_KEY", ""),
            "slack": os.getenv("SLACK_BOT_TOKEN", ""),
            "trello_key": os.getenv("TRELLO_API_KEY", ""),
            "trello_token": os.getenv("TRELLO_TOKEN", ""),
            "calendar": os.getenv("GOOGLE_CALENDAR_CREDENTIALS", "")
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
        """Get latest news using free GNews API"""
        try:
            # Using free GNews API - no API key required
            url = f"https://gnews.io/api/v4/search?q={topic}&max={limit}&lang=en&apikey=demo"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get('articles', [])[:limit]:
                    articles.append({
                        "title": article.get('title', ''),
                        "description": article.get('description', ''),
                        "url": article.get('url', ''),
                        "source": article.get('source', {}).get('name', 'Unknown'),
                        "published": article.get('publishedAt', '')
                    })
                
                if articles:
                    return articles
        except Exception as e:
            print(f"[NEWS] GNews API failed: {e}")
        
        # Fallback: Use free RSS-based news
        try:
            # Use Google News RSS feed as fallback
            import xml.etree.ElementTree as ET
            rss_url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
            response = requests.get(rss_url, timeout=5)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                articles = []
                
                for item in root.findall('.//item')[:limit]:
                    title = item.find('title')
                    link = item.find('link')
                    source = item.find('source')
                    
                    articles.append({
                        "title": title.text if title is not None else "Untitled",
                        "description": "",
                        "url": link.text if link is not None else "#",
                        "source": source.text if source is not None else "Google News",
                        "published": ""
                    })
                
                return articles
        except Exception as e:
            print(f"[NEWS] RSS fallback failed: {e}")
        
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
        
    
    # ==================== SYSTEM STATS ====================
    
    def get_system_stats(self) -> Dict:
        """Get real-time system statistics"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            battery_info = {"percent": 100, "plugged": True}
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        "percent": battery.percent,
                        "plugged": battery.power_plugged,
                        "secsleft": battery.secsleft
                    }
            except:
                pass
            
            return {
                "cpu": f"{cpu_percent}%",
                "ram": f"{ram.percent}%",
                "ram_used": f"{ram.used / (1024**3):.1f}GB",
                "ram_total": f"{ram.total / (1024**3):.1f}GB",
                "disk": f"{disk.percent}%",
                "battery": battery_info
            }
        except ImportError:
            return {"error": "psutil not installed"}
        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}

    # ==================== NASA APOD ====================
    
    def get_nasa_apod(self) -> Dict:
        """Get NASA Astronomy Picture of the Day"""
        try:
            # Using specific demo key for NASA
            url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get('title'),
                    "url": data.get('url'),
                    "hdurl": data.get('hdurl'),
                    "explanation": data.get('explanation'),
                    "date": data.get('date'),
                    "copyright": data.get('copyright', 'NASA')
                }
        except:
            pass
        
        return {"error": "Could not fetch APOD"}

    # ==================== HACKER NEWS ====================
    
    def get_hacker_news(self, limit: int = 5) -> List[Dict]:
        """Get top stories from Hacker News"""
        try:
            # Get top stories IDs
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_stories_url, timeout=5)
            
            if response.status_code == 200:
                story_ids = response.json()[:limit]
                stories = []
                
                for sid in story_ids:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                    story_resp = requests.get(story_url, timeout=2)
                    if story_resp.status_code == 200:
                        story = story_resp.json()
                        stories.append({
                            "title": story.get('title'),
                            "url": story.get('url', f"https://news.ycombinator.com/item?id={sid}"),
                            "score": story.get('score'),
                            "by": story.get('by'),
                            "time": story.get('time')
                        })
                
                return stories
        except:
            pass
        
        return []



    # ==================== FIGMA ====================
    
    def get_figma_files(self, team_id: str = "demo") -> List[Dict]:
        """Get recent Figma files"""
        try:
            token = self.api_keys.get("figma", "")
            if not token:
                 # Mock data for demo if no key
                 return [
                     {"key": "abc1", "name": "App UI Design", "last_modified": "2h ago", "thumbnail": "https://figma.com/demo1.png", "url": "https://www.figma.com/file/abc1"},
                     {"key": "abc2", "name": "Marketing Assets", "last_modified": "5h ago", "thumbnail": "https://figma.com/demo2.png", "url": "https://www.figma.com/file/abc2"},
                     {"key": "abc3", "name": "Design System", "last_modified": "1d ago", "thumbnail": "https://figma.com/demo3.png", "url": "https://www.figma.com/file/abc3"}
                 ]

            # Use /me endpoint which works without team_id
            url = "https://api.figma.com/v1/me"
            headers = {"X-Figma-Token": token}
            me_resp = requests.get(url, headers=headers, timeout=5)
            
            if me_resp.status_code != 200:
                return [{"error": f"Auth failed: {me_resp.status_code}"}]
            
            # Get recent files from all teams the user belongs to
            user_data = me_resp.json()
            files = []
            
            # Try to get files from user's teams
            for team in user_data.get('teams', [])[:2]:  # Limit to 2 teams
                team_url = f"https://api.figma.com/v1/teams/{team['id']}/projects"
                team_resp = requests.get(team_url, headers=headers, timeout=5)
                
                if team_resp.status_code == 200:
                    for proj in team_resp.json().get('projects', [])[:2]:
                        files_url = f"https://api.figma.com/v1/projects/{proj['id']}/files"
                        files_resp = requests.get(files_url, headers=headers, timeout=5)
                        
                        if files_resp.status_code == 200:
                            for f in files_resp.json().get('files', [])[:3]:
                                files.append({
                                    "key": f['key'],
                                    "name": f['name'],
                                    "last_modified": f.get('last_modified', 'N/A'),
                                    "thumbnail": f.get('thumbnail_url', ''),
                                    "url": f"https://www.figma.com/file/{f['key']}"
                                })
            
            return files if files else [{"error": "No files found in your teams"}]
        except Exception as e:
            return [{"error": f"Figma API error: {str(e)}"}]


    # ==================== NOTION ====================

    def search_notion(self, query: str = "") -> List[Dict]:
        """Search Notion workspace"""
        try:
            token = self.api_keys.get("notion", "")
            if not token:
                # Mock data
                return [
                    {"id": "1", "title": "Project Roadmap", "url": "https://notion.so/roadmap", "icon": "🗺️"},
                    {"id": "2", "title": "Meeting Notes", "url": "https://notion.so/notes", "icon": "📝"},
                    {"id": "3", "title": "Design Specs", "url": "https://notion.so/specs", "icon": "🎨"}
                ]
            
            url = "https://api.notion.com/v1/search"
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            payload = {"query": query, "page_size": 5} if query else {"page_size": 5}
            
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                results = []
                for item in response.json().get('results', []):
                    title = "Untitled"
                    try:
                        if item['object'] == 'page':
                            # Notion properties are complex, simplified extraction
                            props = item.get('properties', {})
                            for key, val in props.items():
                                if val['type'] == 'title':
                                    title = val['title'][0]['plain_text']
                                    break
                    except: pass
                    
                    results.append({
                        "id": item['id'],
                        "title": title,
                        "url": item.get('url'),
                        "icon": item.get('icon', {}).get('emoji', '📄')
                    })
                return results
        except:
             pass
        return []

    # ==================== SLACK ====================

    def get_slack_channels(self) -> List[Dict]:
        """Get public Slack channels"""
        try:
            token = self.api_keys.get("slack", "")
            if not token:
                return [
                    {"id": "C1", "name": "general", "members": 42},
                    {"id": "C2", "name": "random", "members": 35},
                    {"id": "C3", "name": "development", "members": 12}
                ]
            
            url = "https://slack.com/api/conversations.list"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, params={"types": "public_channel", "limit": 10})
            
            if response.status_code == 200:
                channels = response.json().get('channels', [])
                return [{"id": c['id'], "name": c['name'], "members": c['num_members']} for c in channels]
        except: pass
        return []

    def send_slack_message(self, channel: str, text: str) -> Dict:
        """Send message to Slack"""
        try:
            token = self.api_keys.get("slack", "")
            if not token: return {"status": "mock_success", "channel": channel}
            
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            # Resolve channel name to ID if needed, or assume ID/Name works
            resp = requests.post(url, headers=headers, json={"channel": channel, "text": text})
            if resp.json().get('ok'):
                return {"status": "success", "ts": resp.json().get('ts')}
        except: pass
        return {"error": "Failed to send"}

    # ==================== TRELLO ====================

    def get_trello_boards(self) -> List[Dict]:
        """Get Trello boards"""
        try:
            key = self.api_keys.get("trello_key", "")
            token = self.api_keys.get("trello_token", "")
            if not key or not token:
                return [
                    {"id": "b1", "name": "Product Backlog", "url": "https://trello.com/b/1", "bg": "blue"},
                    {"id": "b2", "name": "Sprint 42", "url": "https://trello.com/b/2", "bg": "green"},
                ]
                
            url = f"https://api.trello.com/1/members/me/boards?key={key}&token={token}"
            resp = requests.get(url)
            if resp.status_code == 200:
                return [{"id": b['id'], "name": b['name'], "url": b['url'], "bg": b['prefs']['backgroundColor']} for b in resp.json()[:5]]
        except: pass
        return []

    # ==================== GOOGLE CALENDAR ====================

    def get_calendar_events(self, count: int = 5) -> List[Dict]:
        """Get upcoming Google Calendar events"""
        try:
            # Requires complex OAuth, using simplified or mock for now
            creds = self.api_keys.get("calendar", "")
            if not creds:
                now = datetime.now()
                return [
                    {"summary": "Team Standup", "start": "10:00 AM", "date": "Today"},
                    {"summary": "Client Call", "start": "2:00 PM", "date": "Today"},
                    {"summary": "Project Review", "start": "11:00 AM", "date": "Tomorrow"}
                ]
            pass # Real implementation would use google-api-python-client
        except: pass
        return []

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
