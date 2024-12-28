import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
serper_api_key = os.getenv("SERPER_API_KEY")


def query_serper_for_market_data(query):
    """Search for market data using Serper API."""
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


def extract_numbers_from_text(text):
    """Extract numerical estimates from text."""
    numbers = re.findall(r"\b\d[\d,]*\b", text)
    numbers = [int(n.replace(",", "")) for n in numbers if n.replace(",", "").isdigit()]
    return numbers


def fetch_market_size_data(target_market):
    """Fetch market size data using Serper API."""
    search_query = f"number of {target_market} globally"
    serper_results = query_serper_for_market_data(search_query)
    relevant_snippets = [result.get("snippet", "") for result in serper_results.get("organic", [])]
    potential_sizes = []

    for snippet in relevant_snippets:
        numbers = extract_numbers_from_text(snippet)
        potential_sizes.extend(numbers)

    if potential_sizes:
        return max(potential_sizes)  # Use the largest reasonable estimate
    return None


def fetch_customer_spend_data(target_market):
    """Fetch average revenue per customer data using Serper API."""
    search_query = f"average spend per {target_market}"
    serper_results = query_serper_for_market_data(search_query)
    relevant_snippets = [result.get("snippet", "") for result in serper_results.get("organic", [])]
    potential_spends = []

    for snippet in relevant_snippets:
        numbers = extract_numbers_from_text(snippet)
        potential_spends.extend(numbers)

    if potential_spends:
        return max(potential_spends)  # Use the largest reasonable estimate
    return None


def calculate_tam(client, target_market):
    """Calculate the Total Addressable Market (TAM)."""
    # Step 1: Fetch market size data
    market_size = fetch_market_size_data(target_market)

    # Step 2: Fetch average revenue per customer
    average_spend = fetch_customer_spend_data(target_market)

    # Step 3: Calculate TAM
    if market_size and average_spend:
        tam = market_size * average_spend
        return {
            "market_size": market_size,
            "average_spend": average_spend,
            "tam": tam,
        }
    else:
        return "Insufficient data to calculate TAM."


def refine_tam_with_gpt(client, target_market, tam_data):
    """Refine TAM calculation using GPT."""
    prompt = f"""
    You are a market analyst. Based on the following data:
    - Target Market: {target_market}
    - Market Size: {tam_data.get('market_size', 'N/A')} potential customers
    - Average Revenue per Customer: ${tam_data.get('average_spend', 'N/A')}
    - Calculated TAM: ${tam_data.get('tam', 'N/A')}
    
    Please validate the assumptions and provide additional insights into the TAM for the {target_market}. Suggest any corrections or improvements.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert market analyst."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating GPT response: {e}")
        return "Error refining TAM with GPT."

