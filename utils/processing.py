# utils/processing.py

import random
import requests
import os
import streamlit as st

# Get token and URL from Streamlit secrets
API_TOKEN = st.secrets.get("API_TOKEN")
API_URL = st.secrets.get("API_URL")

if not API_TOKEN:
    raise ValueError("API_TOKEN not found in Streamlit secrets")
if not API_URL:
    raise ValueError("API_URL not found in Streamlit secrets")

def get_transition_from_gpt(para_a, para_b, examples, model="gpt-4"):
    """
    Generate a context-aware French transition (max 5 words)
    using few-shot prompting from the examples list and OpenAI GPT.
    """
    # Select 3 random examples for few-shot context
    selected_examples = random.sample(examples, min(3, len(examples)))

    system_prompt = (
        "Tu es un assistant de presse francophone. "
        "Ta tâche est d'insérer une transition brève et naturelle (5 mots maximum) "
        "entre deux paragraphes d'actualité régionale. "
        "La transition doit être journalistique, fluide, neutre et ne pas répéter les débuts comme 'Par ailleurs' ou parallèlement ou sujet."
        "the final TRANSITION in the article must be a proper concluding transition that clearly signals the end of the article. For that final transition only, choose from the following list of expressions: Enfin, Et pour finir, Pour terminer, Pour finir, En guise de conclusion, En conclusion, En guise de mot de la fin, Pour clore cette revue, Pour conclure cette sélection, Dernier point à noter, Pour refermer ce tour d’horizon. These closing transitions should only appear once and exclusively as the last transition in the article."
        "if you use par ailleurs, c'est mieux d'étoffer, avec Par ailleurs, on annonce que, Par ailleurs, sachez que,"
        "avoid the use of en parallèle"
        
    )

    # Prepare messages for OpenAI chat completion
    messages = [{"role": "system", "content": system_prompt}]
    for ex in selected_examples:
        messages.append({"role": "user", "content": ex["input"]})
        messages.append({"role": "assistant", "content": ex["transition"]})

    # Add the real paragraph pair
    messages.append({
        "role": "user",
        "content": f"{para_a.strip()}\nTRANSITION\n{para_b.strip()}"
    })

    # Generate with OpenAI client
    # response = client.chat.completions.create(
    #     model=model,
    #     messages=messages,
    #     temperature=0.5,
    #     max_tokens=20
    # )

    # Prepare request headers and body
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Prepare the prompt dictionary
    prompt_dict = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 20
    }

    # Convert prompt dictionary to string
    prompt_str = str(prompt_dict)

    # Send request to /chat endpoint
    response = requests.post(
        API_URL,
        headers=headers,
        json={"prompt": prompt_str}
    )

    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")

    response_data = response.json()
    if response_data["status"] != "success":
        raise Exception(f"API request failed: {response_data.get('error', 'Unknown error')}")

    return response_data["reply"].strip()
