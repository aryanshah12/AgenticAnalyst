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

# List of data provider domains to exclude
EXCLUDED_DOMAINS = ["zoominfo.com", "owler.com", "trustpilot.com", "g2.com", "trustradius.com", "cbinsights.com", "craft.co", "tracxn.com"]
EXCLUDED_TITLES = ["Alternatives & Competitors"]

def query_serper_for_results(query):
    """Fetch search results for a given query from Serper API."""
    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": serper_api_key}
        data = {"q": query}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Serper API: {e}")
        return {}

def filter_search_results(search_results):
    """Filter search results to exclude known data provider domains and unwanted titles."""
    valid_results = []
    for result in search_results.get("organic", []):
        url = result.get("link", "")
        title = result.get("title", "")
        domain = tldextract.extract(url).domain
        if (
            domain not in EXCLUDED_DOMAINS
            and not any(excluded in title for excluded in EXCLUDED_TITLES)
        ):
            valid_results.append({"name": title, "url": url})
    return valid_results

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

def scrape_competitor_website(competitor_url):
    """Scrape the competitor website for homepage details."""
    try:
        homepage_text = scrape_page_text(competitor_url)
        return f"Homepage:\n{homepage_text}"
    except Exception as e:
        print(f"Error scraping {competitor_url}: {e}")
        return "Could not scrape data."

def fetch_competitor_info(client, startup_url):
    """Fetch competitor details and analyze their offerings."""
    # Extract startup name from URL
    domain_info = tldextract.extract(startup_url)
    company_name = domain_info.domain

    # Perform dual queries
    serper_results_name = query_serper_for_results(company_name)
    serper_results_competitors = query_serper_for_results(f"{company_name} competitors")

    # Combine and filter results
    combined_results = filter_search_results(serper_results_name) + filter_search_results(serper_results_competitors)
    combined_results = {result["url"]: result for result in combined_results}.values()  # Remove duplicates

    if not combined_results:
        return "No relevant competitors found."

    # Scrape competitor websites
    competitor_details = []
    for result in combined_results:
        competitor_name = result["name"]
        competitor_url = result["url"]
        product_details = scrape_competitor_website(competitor_url)
        competitor_details.append(
            {"name": competitor_name, "url": competitor_url, "raw_text": product_details}
        )

    # Prepare competitor descriptions
    competitor_descriptions = ""
    for c in competitor_details:
        competitor_descriptions += f"Name: {c['name']}\nURL: {c['url']}\nText Extracted:\n{c['raw_text']}\n\n"

    # GPT Prompt for competitor analysis
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
        print(f"Error generating GPT-4o response: {e}")
        return f"Error generating competitor analysis: {e}"
