import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from openai import OpenAI
from dotenv import load_dotenv
import tldextract
import re
import os

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
serper_api_key = os.getenv("SERPER_API_KEY")


def query_serper_for_competitors(startup_url):
    """Fetch competitor information from Serper API."""
    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": serper_api_key}
        domain_info = tldextract.extract(startup_url)
        company_name = domain_info.domain
        data = {"q": f"{company_name} competitors"}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Serper API: {e}")
        return {}


def scrape_page_text(url):
    """Scrape text from a given URL page."""
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text(separator=" ") for p in paragraphs).strip()
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""


def find_product_links(base_url, soup, keyword_patterns=["product", "products", "solution", "solutions"]):
    """Find potential product-related links within a competitor's website."""
    links = soup.find_all("a", href=True)
    product_links = []
    for link in links:
        href = link['href']
        if any(re.search(pattern, href, re.IGNORECASE) for pattern in keyword_patterns):
            full_url = urljoin(base_url, href)
            if full_url not in product_links:
                product_links.append(full_url)
    return product_links[:3]  # Limit to 3 product pages


def scrape_competitor_website(competitor_url):
    """Scrape the competitor website thoroughly."""
    homepage_text = scrape_page_text(competitor_url)
    product_texts = ""
    try:
        response = requests.get(competitor_url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        product_links = find_product_links(competitor_url, soup)
        for p_link in product_links:
            product_texts += "\n" + scrape_page_text(p_link)
    except Exception as e:
        print(f"Error scraping product pages for {competitor_url}: {e}")
    return f"Homepage:\n{homepage_text}\n\nProduct Pages:\n{product_texts}"


def fetch_competitor_info(startup_url):
    """Fetch competitor details and analyze their offerings."""
    serper_results = query_serper_for_competitors(startup_url)
    competitors = serper_results.get("organic", [])

    if not competitors:
        return "No competitors found."

    competitor_details = []
    for result in competitors:
        competitor_name = result["title"]
        competitor_url = result["link"]
        product_details = scrape_competitor_website(competitor_url)
        competitor_details.append(
            {"name": competitor_name, "url": competitor_url, "raw_text": product_details}
        )

    competitor_descriptions = ""
    for c in competitor_details:
        competitor_descriptions += f"Name: {c['name']}\nURL: {c['url']}\nText Extracted:\n{c['raw_text']}\n\n"

    competitor_prompt = f"""
    You are a market research analyst. Analyze the competitors for the company hosted at {startup_url}. 
    1. Identify each competitor's core product or service offering based on the provided text.
    2. Compare how their product offerings are similar or different to the startup's offering.
    3. Provide a detailed competitor comparison on key dimensions.
    Data:
    {competitor_descriptions}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a market research assistant specialized in competitor analysis."},
                {"role": "user", "content": competitor_prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating GPT-4 response: {e}")
        return "Error generating competitor analysis."
