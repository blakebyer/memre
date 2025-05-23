import requests
import json
import os 
from dotenv import load_dotenv
from datetime import datetime, date
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

load_dotenv() # load .env

# load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIKI_API_KEY = os.getenv("WIKI_API_KEY")

def get_urls(isbn='1546-1726', start_date='2024-01-01', end_date=date.today(), save=False):
    # default isbn is nature neuroscience online
    # other feasible isbn options: Neuron = 1097-4199, Acta Neuropathologica = 1432-0533, Trends in Neurosciences = 1878-108X, The Journal of Neuroscience = 1529-2401, Brain = 1460-2156,
    # eLife = 2050-084X, Annual Review of Neuroscience = 1545-4126, Current Opinion in Neurobiology = 1873-6882
    url = f"https://api.crossref.org/journals/{isbn}/works?filter=type:journal-article,from-pub-date:{start_date},until-pub-date:{end_date}&rows=100"

    headers = { # impersonate a browser to prevent 403 access forbidden errors
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'http://google.com'
    }

    # save response to json with filename specified with datetime
    response = requests.get(url, headers = headers, timeout=30)
    response.raise_for_status()
    response_json = response.json()

    results = []

    for article in response_json.get("message", {}).get("items", []):
        title = article.get("title", [""])[0]
        authors = article.get("author", [])
        date = article.get("created", []).get("date-time")
        formatted_names = [f"{a.get('family', '')}, {a.get('given', '')}" for a in authors]
        abstract = article.get("abstract", [""])
        url_field = article.get("URL", "")
        journal = article.get("container-title", [""])[0]

        results.append({
            "title": title,
            "authors" : formatted_names,
            "date" : date,
            "abstract" : abstract,
            "url": url_field,
            "journal": journal
        })

    if (save):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"article_urls_{timestamp}.json"
        output_path = os.path.join("requests//json", filename)

        # save json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

def scrape_text(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ))
        page = context.new_page()
        page.goto(url, wait_until="load", timeout=60000)  # Wait for full JS load
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    
    # Remove irrelevant elements
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()

    # Return clean text
    return soup.get_text(separator="\n", strip=True)


def summarize_text(text, api_key=OPENAI_API_KEY, model="gpt-4o"):
    results = []
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes web content to be used in an Instagram post caption."},
            {"role": "user", "content": f"Summarize the following article, address its current relevance to neuroscience, and craft it into a succint (<250 words) Instagram caption with appropriate but sparse emojis and hashtags. Please do not mention the name of the journal, figures within the article, author names, or tag an account using an @ symbol.\n\n{text}"}
        ],
        "temperature": 0.5,
        "max_tokens": 500
    }
    keyword_data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that uses web content to find relevant keywords to be used to search an image database."},
            {"role": "user", "content": f"Using the following article, find three specific keywords that could be used to search an image database such as Wikimedia Commons. Return the words in comma delimited string (i.e. 'neurodegeneration,gliosis'). Please do not use overly technical terms within the article, such as the name of a protein (e.g. PSEN1 or GFAP) or an acronym, instead return keywords relevant to the topics of the article (e.g. 'Parkinsonism' or 'diffusion tensor imaging'). Please do not mention author names and do not return any additional text besides the comma-delimited keyword string.\n\n{text}"}
        ],
        "temperature": 0.5,
        "max_tokens": 20
    }

    # get article summary as an Instagram caption
    response1 = requests.post(url, headers=headers, json=data)
    response1.raise_for_status()
    summary = response1.json()['choices'][0]['message']['content']
    
    # get article keywords
    response2 = requests.post(url, headers=headers, json=keyword_data)
    keywords = response2.json()['choices'][0]['message']['content']
    
    return {
    "summary": summary,
    "keywords": keywords
    }

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

def get_wikimedia(query, extensions= ('.jpg', '.jpeg', '.png', '.svg'), limit=5):
    url = 'https://api.wikimedia.org/core/v1/commons/search/page'
    headers = { # impersonate a browser to prevent 403 access forbidden errors
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36"
    }
    params = {
        'q' : query,
        'limit' : limit
    }
    res = requests.get(url, headers = headers, params = params, timeout=30)
    res.raise_for_status()

    res = requests.get(url, headers=headers, params=params, timeout=30)
    res.raise_for_status()
    pages = res.json().get("pages", [])

    results = []
    for page in pages[:limit]:
        title = page.get("title", "")

        if not title.startswith("File:") or not title.lower().endswith(extensions):
            continue

        img_url = 'https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&format=json'
        img_params = {
            'titles' : title
        }
        metadata = requests.get(img_url, headers = headers, params = img_params, timeout=30)
        metadata.raise_for_status()
        data = metadata.json()

        # Navigate to the page object
        pages_dict = data.get("query", {}).get("pages", {})
        page_info = next(iter(pages_dict.values()))  # safely get the first (and only) page

        # get metadata
        img_info = page_info.get("imageinfo", [{}])[0]
        extmetadata = img_info.get("extmetadata", {})
        author =  extmetadata.get("Artist", {}).get("value")
        description = extmetadata.get("ImageDescription", {}).get("value")
        credit =  extmetadata.get("Credit", {}).get("value")
        license = extmetadata.get("License", {}).get("value")

        link = f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}"
        results.append({
            "title": title,
            "author": author,
            "description" : description,
            "credit" : credit,
            "license" : license,
            "url": link
        })

    return results

def make_content(isbn='1546-1726', start_date='2025-01-01', end_date=date.today(), trim=5000, limit=None, save=False):
    processed_articles = []

    articles = get_urls(isbn = isbn, start_date=start_date, end_date=end_date)

    if limit is not None:
        articles = articles[:limit]

    for article in articles:
        atitle = article.get("title")
        aurl = article.get("url")
        ajournal = article.get("journal")
        authors = article.get("authors")
        date = article.get("date")
        abstract = article.get("abstract")

        try:
            images = []
            text = scrape_text(aurl)
            sum_key = summarize_text(text[:trim])
            summary = sum_key.get("summary")
            keywords = sum_key.get("keywords").split(",") # convert to list

            for keyword in keywords:
                image = get_wikimedia(keyword)
                images.append(image)

            processed_articles.append({
                "title": atitle,
                "authors": authors,
                "date" : date,
                "abstract" : abstract,
                "url": aurl,
                "journal": ajournal,
                "keywords" : keywords,
                "caption" : summary,
                "images": images
            })
            print(f"Done: {atitle}")

        except Exception as e:
            print(f"Failed to process article {atitle} : {e}")
    
    if (save):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"{ajournal}_content_{timestamp}.json"
        output_path = os.path.join("requests//json", filename)

        # save json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(processed_articles, f, ensure_ascii=False, indent=2)
    
    return processed_articles

new_content = make_content(isbn='1545-4126', limit = 5, save=True) # only the first X articles 