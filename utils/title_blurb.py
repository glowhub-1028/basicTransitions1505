# utils/title_blurb.py

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get token and URL from environment variables
API_TOKEN = os.getenv('API_TOKEN')
API_URL = os.getenv('API_URL')

if not API_TOKEN:
    raise ValueError("API_TOKEN environment variable is not set")

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

def generate_title_and_blurb(paragraph):
    # Prepare the prompt dictionary
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
