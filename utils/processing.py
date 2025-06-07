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
        "La transition doit être journalistique, fluide, neutre et ne pas répéter les débuts comme 'Par ailleurs' ou parallèlement ou sujet. "
        "AVANT de générer une transition, tu DOIS d'abord analyser le contenu du paragraphe qui suit pour identifier son sujet principal. "
        "Le sujet principal est déterminé par les mots-clés et le contexte du paragraphe. "
        "Par exemple : "
        "- Si le paragraphe contient des mots comme 'CRS', 'police', 'sécurité', 'maintien de l'ordre' → sujet = sécurité "
        "- Si le paragraphe contient des mots comme 'école', 'élèves', 'enseignement', 'éducation' → sujet = éducation "
        "- Si le paragraphe contient des mots comme 'innovation', 'technologie', 'recherche' → sujet = innovation "
        "UNE FOIS le sujet identifié, utilise UNIQUEMENT la transition correspondante : "
        "- Pour la sécurité : 'Sur le plan sécuritaire,', 'Dans le domaine de la sécurité,', 'Côté maintien de l'ordre,' "
        "- Pour l'éducation : 'Sur le plan éducatif,', 'Dans le domaine de l'enseignement,', 'Côté formation,' "
        "- Pour l'innovation : 'Dans le domaine de l'innovation,', 'Sur le plan technologique,', 'Côté recherche,' "
        "- Pour la culture : 'Sur la scène culturelle,', 'Dans le domaine artistique,', 'Côté culture,' "
        "- Pour le sport : 'Sur le plan sportif,', 'Dans le domaine sportif,', 'Côté sport,' "
        "- Pour l'environnement : 'Sur le plan écologique,', 'Dans le domaine environnemental,', 'Côté développement durable,' "
        "- Pour la politique : 'Sur le plan politique,', 'Dans le domaine institutionnel,', 'Côté gouvernance,' "
        "- Pour l'économie : 'Sur le plan économique,', 'Dans le domaine financier,', 'Côté business,' "
        "La dernière transition de l'article doit signaler clairement la fin de l'article. "
        "Utilise uniquement une des formules de clôture suivantes pour la dernière transition : "
        "Enfin, Et pour finir, Pour terminer, En guise de conclusion, En conclusion, En guise de mot de la fin, "
        "Pour clore cette revue, Pour conclure cette sélection, Dernier point à noter, Pour refermer ce tour d'horizon. "
        "Ces formules de conclusion ne doivent apparaître qu'une seule fois, à la toute fin. "
        "Si tu utilises 'Par ailleurs', étoffe la formulation : par exemple 'Par ailleurs, on annonce que'. "
        "Évite 'En parallèle'."
    )

    # Prepare messages for OpenAI chat completion
    messages = [{"role": "system", "content": system_prompt}]
    for ex in selected_examples:
        if "paragraph_a" in ex and "paragraph_b" in ex and "transition" in ex:
            messages.append({
                "role": "user",
                "content": f"{ex['paragraph_a'].strip()}\nTRANSITION\n{ex['paragraph_b'].strip()}"
            })
            messages.append({"role": "assistant", "content": ex["transition"].strip()})
        else:
            raise ValueError(f"Example format invalid: {ex}")

    # Add the real paragraph pair
    messages.append({
        "role": "user",
        "content": f"{para_a.strip()}\nTRANSITION\n{para_b.strip()}"
    })

    # Send request to your proxy endpoint
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 20
    }

    response = requests.post(API_URL, headers=headers, json={"prompt": str(payload)})

    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")

    data = response.json()
    if data.get("status") != "success":
        raise Exception(f"API request failed: {data.get('error', 'Unknown error')}")

    return data["reply"].strip()
