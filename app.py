from competitor_analysis import fetch_competitor_info
from dotenv import load_dotenv
from openai import OpenAI
import os
import streamlit as st

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("Competitive Landscape Generator - by Aryan")
st.subheader("Generate Competitor Analysis for a Startup")

# Input field for startup URL
startup_url = st.text_input("Enter the Startup's Website URL:")

if st.button("Generate Report"):
    with st.spinner("Generating your report..."):
        try:
            # Perform competitor analysis
            competitor_analysis = fetch_competitor_info(client, startup_url)

            # Display the result
            st.markdown(competitor_analysis, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error generating report: {e}")
