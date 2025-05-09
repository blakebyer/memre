import requests
import json
import os 
from dotenv import load_dotenv
from datetime import datetime
import random
from bs4 import BeautifulSoup

load_dotenv() # load .env

# load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
api_key = OPENAI_API_KEY

def scrape_text(url):
    headers = { # impersonate a browser to prevent 403 access forbidden errors
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def summarize_text(text, api_key, model="gpt-4.1"):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes web content to be used in an Instagram post caption."},
            {"role": "user", "content": f"Summarize the following article, address its current relevance to neuroscience, and craft it into a succint (<250 words) Instagram caption with appropriate but sparse emojis and hashtags. Please do not mention figures within the article, author names, or tag an account using an @ symbol.\n\n{text}"}
        ],
        "temperature": 0.5,
        "max_tokens": 500
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

filename = "neuroscience_news_2025-05-09_12-32.json"
input_path = os.path.join("requests//json", filename)

with open(input_path, "r", encoding="utf-8") as f:
    response_json = json.load(f)

def make_content(response_json, trim=5000):
    processed_articles = []

    for article in response_json.get("articles", []):
        source = article.get("source", {}).get("name")
        author = article.get("author", "Unknown Author")
        title = article.get("title")
        url = article.get("url")

        try:
            text = scrape_text(url)
            article["text"] = text[:trim]  # Trim if needed
            article["summary"] = summarize_text(text[:trim], api_key)
            processed_articles.append(article)
            print(f"Done: {title}")
        except Exception as e:
            print(f"Failed to process {title}: {e}")
    return processed_articles

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = f"summarized_news_{timestamp}.json"
output_path = os.path.join("requests//json", filename)

new_content = make_content(response_json)

# save summarized content
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(new_content, f, ensure_ascii=False, indent=2)