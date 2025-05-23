from bs4 import BeautifulSoup
import urllib.robotparser
import requests

rp = urllib.robotparser.RobotFileParser()
rp.set_url('http://example.com/robots.txt')
rp.read()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'http://google.com'
}

url = 'https://academic.oup.com/braincomms/article/6/5/fcae341/7796664'
if rp.can_fetch('*', url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
else:
    print("Scraping not allowed by robots.txt")