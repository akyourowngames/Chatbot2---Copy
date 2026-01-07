"""
Real-Time Weather Service
========================
Provides real weather data using OpenWeatherMap API (free tier).
"""

import requests
import logging
import os
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherService:
    """Real-time weather service using OpenWeatherMap API."""
    
    def __init__(self, api_key: str = ""):
        """
        Initialize weather service.
        
        Args:
            api_key: OpenWeatherMap API key (optional - can use env var)
        """
        # Try environment variable first, then parameter, then default
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY') or "bd5e378503939ddaee76f12ad7a97608"
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self._cache = {}
        self._cache_duration = timedelta(minutes=10)  # Cache for 10 mins
        logger.info("[WEATHER] Service initialized")
    
    def get_weather(self, city: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Get current weather for a location.
        
        Args:
            city: City name (e.g., "London", "New York")
            lat: Latitude (alternative to city)
            lon: Longitude (alternative to city)
            
        Returns:
            Weather data dictionary
        """
        try:
            # Check cache
            cache_key = city or f"{lat},{lon}"
            if cache_key in self._cache:
                cached_data, cached_time = self._cache[cache_key]
                if datetime.now() - cached_time < self._cache_duration:
                    logger.info(f"[WEATHER] Returning cached data for {cache_key}")
                    return cached_data
            
            # Build request URL
            params = {"appid": self.api_key, "units": "metric"}
            
            if city:
                params["q"] = city
            elif lat and lon:
                params["lat"] = lat
                params["lon"] = lon
            else:
                # Default to user's approximate location (IP-based fallback)
                city = "London"  # Default city
                params["q"] = city
            
            # Make API request
            url = f"{self.base_url}/weather"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            result = {
                "status": "success",
                "location": {
                    "city": data.get("name", city),
                    "country": data.get("sys", {}).get("country", ""),
                    "coordinates": {
                        "lat": data.get("coord", {}).get("lat"),
                        "lon": data.get("coord", {}).get("lon")
                    }
                },
                "current": {
                    "temperature": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"].title(),
                    "icon": data["weather"][0]["icon"],
                    "wind_speed": round(data["wind"]["speed"] * 3.6),  # Convert to km/h
                    "clouds": data.get("clouds", {}).get("all", 0),
                    "visibility": data.get("visibility", 0) // 1000  # Convert to km
                },
                "sun": {
                    "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M"),
                    "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M")
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache result
            self._cache[cache_key] = (result, datetime.now())
            
            logger.info(f"[WEATHER] Fetched weather for {result['location']['city']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[WEATHER] API request failed: {e}")
            return {
                "status": "error",
                "error": "Failed to fetch weather data",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"[WEATHER] Unexpected error: {e}")
            return {
                "status": "error",
                "error": "Weather service error",
                "message": str(e)
            }
    
    def get_forecast(self, city: str = None, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for upcoming days.
        
        Args:
            city: City name
            days: Number of days (max 5 for free tier)
            
        Returns:
            Forecast data dictionary
        """
        try:
            params = {
                "appid": self.api_key,
                "units": "metric",
                "q": city or "London",
                "cnt": min(days * 8, 40)  # 8 data points per day (3-hour intervals)
            }
            
            url = f"{self.base_url}/forecast"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Group by day
            daily_forecasts = []
            current_date = None
            day_data = []
            
            for item in data["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                date_str = dt.strftime("%Y-%m-%d")
                
                if date_str != current_date:
                    if day_data:
                        daily_forecasts.append(self._process_day_forecast(day_data))
                    current_date = date_str
                    day_data = [item]
                else:
                    day_data.append(item)
            
            # Add last day
            if day_data:
                daily_forecasts.append(self._process_day_forecast(day_data))
            
            return {
                "status": "success",
                "location": {
                    "city": data["city"]["name"],
                    "country": data["city"]["country"]
                },
                "forecast": daily_forecasts[:days],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[WEATHER] Forecast error: {e}")
            return {
                "status": "error",
                "error": "Failed to fetch forecast",
                "message": str(e)
            }
    
    def _process_day_forecast(self, day_data: list) -> Dict[str, Any]:
        """Process forecast data for a single day."""
        temps = [item["main"]["temp"] for item in day_data]
        
        return {
            "date": datetime.fromtimestamp(day_data[0]["dt"]).strftime("%Y-%m-%d"),
            "day_name": datetime.fromtimestamp(day_data[0]["dt"]).strftime("%A"),
            "temp_min": round(min(temps)),
            "temp_max": round(max(temps)),
            "description": day_data[len(day_data)//2]["weather"][0]["description"].title(),
            "icon": day_data[len(day_data)//2]["weather"][0]["icon"],
            "humidity": sum(item["main"]["humidity"] for item in day_data) // len(day_data),
            "wind_speed": round(sum(item["wind"]["speed"] for item in day_data) / len(day_data) * 3.6)
        }


# Global instance
weather_service = WeatherService()


# Convenience functions
def get_weather(city: str = None) -> Dict[str, Any]:
    """Get current weather for a city."""
    return weather_service.get_weather(city=city)


def get_forecast(city: str = None, days: int = 5) -> Dict[str, Any]:
    """Get weather forecast."""
    return weather_service.get_forecast(city=city, days=days)


# Test
if __name__ == "__main__":
    print("🌤️ Testing Weather Service\n")
    
    # Test current weather
    weather = get_weather("London")
    if weather["status"] == "success":
        print(f"📍 {weather['location']['city']}, {weather['location']['country']}")
        print(f"🌡️ {weather['current']['temperature']}°C (Feels like {weather['current']['feels_like']}°C)")
        print(f"☁️ {weather['current']['description']}")
        print(f"💧 Humidity: {weather['current']['humidity']}%")
        print(f"💨 Wind: {weather['current']['wind_speed']} km/h\n")
    
    # Test forecast
    forecast = get_forecast("London", days=3)
    if forecast["status"] == "success":
        print(f"📅 3-Day Forecast for {forecast['location']['city']}:")
        for day in forecast["forecast"]:
            print(f"  {day['day_name']}: {day['temp_min']}°C - {day['temp_max']}°C, {day['description']}")
