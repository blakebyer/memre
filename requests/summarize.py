import requests
import json
import os 
from dotenv import load_dotenv
from datetime import datetime
import random
from bs4 import BeautifulSoup
import re

load_dotenv() # load .env

# load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIKI_API_KEY = os.getenv("WIKI_API_KEY")

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

def summarize_text(text, api_key=OPENAI_API_KEY, model="gpt-4.1"):
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

def get_image_url(title, api_key=OPENAI_API_KEY, model="gpt-4o"):
    """
    Uses OpenAI GPT-4 with browsing to return a real Wikimedia Commons image URL related to the given title.
    """
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = (
        f"Search Wikimedia Commons, Unsplash, Shutterstock, Pexels, or Flickr for a publicly usable image related to the topic \"{title}\"."
        "Try synonyms or broader concepts if needed (e.g., if the topic is PTSD, try 'brain', 'neuroscience', or 'mental health')."
        "Pick one suitable, high-quality image and return only its direct image URL (ending in .jpg or .png). "
        "Do not guess. Do not invent a link. If no image is found, return 'None'. Return only the URL, no extra text."
    )
    data = {
        "model": model,
        "tools": [{ "type": "web_search_preview" }],
        "input": prompt,
        "temperature": 0.2
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()['output'][1]['content'][0]['text']

def get_wikimedia(title, api_key=WIKI_API_KEY):
    True

# # get neuro news files
json_files = [
    os.path.join("requests/json", f)
    for f in os.listdir("requests/json")
    if f.startswith("neuroscience_news") and f.endswith(".json")
]

# Sort files by last modified time (most recent first)
json_files.sort(key=os.path.getmtime, reverse=True)

# Load the most recent file
if json_files:
    latest_file = json_files[0]
    with open(latest_file, "r", encoding="utf-8") as f:
        response_json = json.load(f)
else:
    raise FileNotFoundError("No neuroscience_news JSON files found.")

def make_content(response_json, trim=5000, limit=None):
    processed_articles = []

    # Slice the list of articles if a limit is set
    articles = response_json.get("articles", [])
    if limit is not None:
        articles = articles[:limit]

    for article in articles:
        source = article.get("source", {}).get("name")
        author = article.get("author", "Unknown Author")
        title = article.get("title")
        url = article.get("url")

        try:
            text = scrape_text(url)
            summary = summarize_text(text[:trim])
            image = get_image_url(title)
            processed_articles.append({
                "title": title,
                "source": source,
                "author": author,
                "url": url,
                "summary": summary,
                "image": image
            })
            
            print(f"Done: {title}")
        except Exception as e:
            print(f"Failed to process {title}: {e}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"neuro_news_content_{timestamp}.json"
    output_path = os.path.join("requests/json", filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_articles, f, ensure_ascii=False, indent=2)

    return processed_articles

new_content = make_content(response_json, limit = 10) # only the first X articles 
