import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from gnews import GNews
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def is_valid_url(url):
    return isinstance(url, str) and url.startswith(('http://', 'https://'))

def get_site(url):
    if is_valid_url(url):
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.split('.')[0].lower()
    
    else:
        return ""

def get_random_user_agent():
    try:
        ua = UserAgent()
        return ua.random
    except Exception:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

def extract_external_citations(soup, main_content, base_url):
    base_domain = urllib.parse.urlparse(base_url).netloc.replace("www.", "")
    citations = []

    for a_tag in main_content.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True)
        full_link = urllib.parse.urljoin(base_url, href)
        link_domain = urllib.parse.urlparse(full_link).netloc.replace("www.", "")

        if len(text) > 3 and base_domain not in link_domain and link_domain:
            if is_valid_url(full_link):
                citations.append(full_link)
    
    return citations

def scrape_news(url):
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove noise
        for tag in soup(['script', 'style', 'video', 'iframe', 'source', 'nav', 'footer', 'aside']):
            tag.decompose()

        # Headline
        headline = soup.title.string.strip() if soup.title else ""

        if headline == None:
            headline = ''

        # Main content
        main_content = soup.find('article') or soup.find('main') or soup.body
        if not main_content:
            return {"headline": headline, "content": "", "citations": []}

        text_content = main_content.get_text(separator='\n', strip=True)
        if not text_content.strip():
            return {"headline": headline, "content": "", "citations": []}

        # Citations
        citations = extract_external_citations(soup, main_content, url)
        for cit in citations:
            if (get_site(cit) == get_site(url)):
                citations.remove(cit)

        return {
            "headline": headline,
            "content": text_content,
            "citations": citations
        }
    
    else:
        return {"headline": "", "content": "", "citations": []}

def get_final_url_selenium(input_url):
    # Set up headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(input_url)
        time.sleep(5)  # Allow time for redirect
        
        final_url = driver.current_url
        return final_url
    finally:
        driver.quit()

def find_news_sources(news_title, num_results=8):
    google_news = GNews(language='en', max_results=num_results)
    results = google_news.get_news(news_title)

    clean_urls = []
    if results:
        for article in results:
            try:
                clean_url = get_final_url_selenium(article["url"])
                if clean_url:
                    clean_urls.append(clean_url)
            except Exception as e:
                continue
        
        return clean_urls
    
    else:
        return []


def get_page(url, original_flag = False):
    data = scrape_news(url)
    flag = False
    
    if (not original_flag) and (len(data["citations"]) == 0) and data["headline"]:
            data["citations"] = find_news_sources(data["headline"])
            flag = True
    
    elif len(data["citations"]) == 0:
            flag = True
        
    return data, flag
