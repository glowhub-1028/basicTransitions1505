# utils/title_blurb.py

import requests
import streamlit as st

API_TOKEN = st.secrets.get("API_TOKEN")
API_URL = st.secrets.get("API_URL")

if not API_TOKEN:
    raise ValueError("API_TOKEN is not set in Streamlit secrets")

PROMPT = """Tu es un assistant de rédaction pour un journal local français.

Ta tâche est de générer un **titre** et un **chapeau** (blurb) à partir du **premier paragraphe uniquement**.

Règles :

1. Titre :
   - Court, clair et journalistique (max. 12 mots).
   - Inclure le lieu si mentionné dans le paragraphe.
   - Inclure la date si mentionnée dans le paragraphe.
   - Doit annoncer le fait principal.

2. Chapeau :
   - Résume quoi, qui, où, quand.
   - Mentionner la date et le lieu s'ils sont dans le paragraphe.
   - Max. 30 mots, ton neutre.

Utilise uniquement le contenu du paragraphe fourni, sans rien ajouter.

Format de réponse :
Titre : [titre généré]
Chapeau : [chapeau généré]
"""

def generate_title_and_blurb(paragraph: str):
    
    prompt_dict = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": paragraph.strip()}
        ],
        "temperature": 0.5,
        "max_tokens": 100
    }

    # Convert prompt dictionary to string
    prompt_str = str(prompt_dict)

    # Prepare request headers
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 🔍 Debug log
    st.write("🧪 Prompt sent to API:")
    st.code(prompt_str)

    response = requests.post(API_URL, headers=headers, json={"prompt": prompt_str})

    # 🔍 Debug log
    st.write("🧪 Raw API response:")
    st.code(response.text)

    if response.status_code != 200:
        raise Exception(
            f"API request failed with status code {response.status_code}\n"
            f"Response content:\n{response.text}"
        )

    response_data = response.json()

    if response_data.get("status") != "success":
        raise Exception(
            f"API request failed:\nStatus: {response_data.get('status')}\n"
            f"Error: {response_data.get('error', 'Unknown error')}\n"
            f"Full response:\n{response.text}"
        )
    
    return response_data["reply"].strip()
