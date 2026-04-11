import requests

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 33.4453,
    "longitude": -112.0667,
    "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
    "temperature_unit": "fahrenheit",
    "wind_speed_unit": "mph",
    "timezone": "auto"
}

response = requests.get(url, params=params)
data = response.json()

hourly = data["hourly"]

print("Temp:", hourly["temperature_2m"][0])
print("Wind Speed:", hourly["wind_speed_10m"][0])
print("Wind Dir:", hourly["wind_direction_10m"][0])
print("Humidity:", hourly["relative_humidity_2m"][0])