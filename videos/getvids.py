import requests
import json
import os 
from dotenv import load_dotenv
from datetime import date, datetime
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

load_dotenv() # load .env

def get_urls(isbn='1546-1726', start_date='2020-01-01', end_date=date.today(), save=False):
    # default isbn is nature neuroscience online
    # other feasible isbn options: Neuron = 1097-4199, Acta Neuropathologica = 1432-0533, Trends in Neurosciences = 1878-108X, The Journal of Neuroscience = 1529-2401, Brain = 1460-2156,
    # eLife = 2050-084X, Annual Review of Neuroscience = 1545-4126, Current Opinion in Neurobiology = 1873-6882
    url = f"https://api.crossref.org/journals/{isbn}/works?filter=type:journal-article,from-pub-date:{start_date},until-pub-date:{end_date}&rows=100"

    headers = { # impersonate a browser to prevent 403 access forbidden errors
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36"
    }

    # save response to json with filename specified with datetime
    response = requests.get(url, headers = headers, timeout=10)
    response_json = response.json()

    results = []

    for article in response_json.get("message", {}).get("items", []):
        title = article.get("title", [""])[0]
        authors = article.get("author", [])
        formatted_names = [f"{a.get('family', '')}, {a.get('given', '')}" for a in authors]
        abstract = article.get("abstract", [""])
        url_field = article.get("URL", "")
        journal = article.get("container-title", [""])[0]

        results.append({
            "title": title,
            "authors" : formatted_names,
            "abstract" : abstract,
            "url": url_field,
            "journal": journal
        })

    if (save):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"{journal}_{timestamp}.json"
        output_path = os.path.join("videos//json", filename)

        # save json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

elife = get_urls(isbn= '2050-084X', start_date="2025-01-01", save = True)

def get_vids(articles, extensions= ['.mp4'], save=False):
    all_videos = []

    for article in articles:
        url = article.get("url")
        print(f"Searching: {url}")
        journal = article.get("journal")

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            found = False
            for a in soup.find_all("a", href=True):
                href = a['href']
                if any(href.lower().endswith(ext) for ext in extensions):
                    full_url = urljoin(url, href)
                    print(f"Found: {full_url}")
                    all_videos.append({
                        "title": article.get("title"),
                        "article_url": url,
                        "video_url": full_url
                    })
                    found = True

            if not found:
                print("No video links found.")

        except Exception as e:
            print(f"Error with {url}: {e}")

    if (save):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"{journal}_vids_{timestamp}.json"
        output_path = os.path.join("videos//json", filename)

        # save json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_videos, f, ensure_ascii=False, indent=2)

    return all_videos

#vids = get_vids(elife, save = True)