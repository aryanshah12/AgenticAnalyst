from competitor_analysis import fetch_competitor_info
from tam_calculation import calculate_tam, refine_tam_with_gpt
from dotenv import load_dotenv
from openai import OpenAI
import os
import streamlit as st

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("Startup Investment Memo Generator")
st.subheader("Generate Competitor Analysis and Market Size")

# Input field for startup URL and target market
startup_url = st.text_input("Enter the Startup's Website URL:")
target_market = st.text_input("Describe the Target Market (e.g., SaaS companies, e-commerce stores):")

if st.button("Generate Report"):
    with st.spinner("Testing OpenAI API connection..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Test OpenAI API connection."},
                ],
            )
            st.success("OpenAI API connection successful!")
        except Exception as e:
            st.error(f"Error connecting to OpenAI API: {e}")
            st.stop()

    with st.spinner("Generating your report..."):
        try:
            # Perform competitor analysis
            competitor_analysis = fetch_competitor_info(client, startup_url)

            # Perform TAM calculation
            tam_data = calculate_tam(client, target_market)
            refined_tam = refine_tam_with_gpt(client, target_market, tam_data)

            # Display the result
            st.markdown("## Competitor Analysis", unsafe_allow_html=True)
            st.markdown(competitor_analysis, unsafe_allow_html=True)

            st.markdown("## Bottom-Up Market Size", unsafe_allow_html=True)
            if isinstance(tam_data, dict):
                st.markdown(f"### Market Size: {tam_data['market_size']} potential customers")
                st.markdown(f"### Average Revenue per Customer: ${tam_data['average_spend']}")
                st.markdown(f"### Total Addressable Market (TAM): ${tam_data['tam']}")
                st.markdown(f"### Refined TAM Analysis:\n\n{refined_tam}")
            else:
                st.markdown(tam_data)
        except Exception as e:
            st.error(f"Error generating report: {e}")
