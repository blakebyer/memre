import requests
import json
url = ('https://newsapi.org/v2/top-headlines?country=us&category=science&apiKey=2f40e89b12054edbba8eab400c7b5c82')

response = requests.get(url)
print(response.json())