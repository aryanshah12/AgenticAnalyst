import openai

# Calculate Total Addressable Market
def calculate_tam(startup_url):
    prompt = f"""
    Based on the company hosted at {startup_url}, calculate the Total Addressable Market (TAM).
    Use a bottom-up approach and provide clear assumptions.
    """
    response = openai.Completion.create(
        model="gpt-4o",
        prompt=prompt,
    )
    return response['choices'][0]['text']
