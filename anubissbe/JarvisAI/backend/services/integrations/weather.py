import aiohttp
import logging
from typing import Dict, Any, Optional

from .base import BaseIntegration

logger = logging.getLogger(__name__)

class WeatherIntegration(BaseIntegration):
    async def execute(self, action: str, parameters: Dict[str, Any], api_key: Optional[str] = None) -> Any:
        """Execute a weather action"""
        if not api_key:
            return {"error": "Weather API key not provided"}
        
        action = action.lower()
        
        if action == "current":
            return await self._get_current_weather(
                parameters.get("location", ""),
                api_key
            )
        elif action == "forecast":
            return await self._get_weather_forecast(
                parameters.get("location", ""),
                parameters.get("days", 5),
                api_key
            )
        else:
            raise ValueError(f"Unknown weather action: {action}")
    
    async def _get_current_weather(self, location: str, api_key: str) -> Dict[str, Any]:
        """Get current weather for a location"""
        if not location:
            return {"error": "Location not provided"}
        
        # Using OpenWeatherMap API as an example
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        return {
                            "location": location,
                            "temperature": data["main"]["temp"],
                            "feels_like": data["main"]["feels_like"],
                            "humidity": data["main"]["humidity"],
                            "pressure": data["main"]["pressure"],
                            "wind_speed": data["wind"]["speed"],
                            "description": data["weather"][0]["description"],
                            "icon": data["weather"][0]["icon"]
                        }
                    else:
                        return {"error": f"Failed to get weather: HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Error getting weather: {str(e)}")
            return {"error": f"Weather request failed: {str(e)}"}
    
    async def _get_weather_forecast(self, location: str, days: int, api_key: str) -> Dict[str, Any]:
        """Get weather forecast for a location"""
        if not location:
            return {"error": "Location not provided"}
        
        # Using OpenWeatherMap API as an example
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric&cnt={days * 8}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process forecast data
                        forecast = []
                        for item in data["list"]:
                            forecast.append({
                                "datetime": item["dt_txt"],
                                "temperature": item["main"]["temp"],
                                "feels_like": item["main"]["feels_like"],
                                "humidity": item["main"]["humidity"],
                                "description": item["weather"][0]["description"],
                                "icon": item["weather"][0]["icon"]
                            })
                        
                        return {
                            "location": location,
                            "forecast": forecast
                        }
                    else:
                        return {"error": f"Failed to get forecast: HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Error getting forecast: {str(e)}")
            return {"error": f"Forecast request failed: {str(e)}"}