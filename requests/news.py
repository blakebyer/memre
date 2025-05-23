import requests
import json
import os 
from dotenv import load_dotenv
from datetime import datetime

load_dotenv() # load .env

# load API key
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# example request urls
url = (f'https://newsapi.org/v2/top-headlines?country=us&category=science&apiKey={NEWS_API_KEY}')

url2 = ('https://newsapi.org/v2/everything'
'?domains=nature.com,'
'sciencedaily.com,'
'sciencenews.org,'
'neurosciencenews.com,'
'scientificamerican.com,'
'newscientist.com,'
'brainblogger.com,'
'thetransmitter.org,'
'nih.gov,'
'ninds.nih.gov,'
'cell.com,'
'thelancet.com,'
'jneurosci.org,'
'frontiersin.org,'
'plos.org,'
'biorxiv.org,'
'elifesciences.org,'
'jneuro.org,'
'medrxiv.org,'
'alzforum.org,'
'psychologytoday.com,'
'sfn.org,'
'mit.edu,'
'harvard.edu,'
'cam.ac.uk'
f'&q=neuroscience&language=en&sortBy=relevancy&apiKey={NEWS_API_KEY}') # can sort by relevancy or popularity or publishedAt (newest first)

# save response to json with filename specified with datetime
response = requests.get(url2)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = f"neuroscience_news_{timestamp}.json"
output_path = os.path.join("requests//json", filename)

# save json
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(response.json(), f, ensure_ascii=False, indent=2)