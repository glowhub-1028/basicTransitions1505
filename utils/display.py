import streamlit as st

def layout_title_and_input():
    st.title("🇫🇷 Générateur de transitions françaises")
    st.markdown("Remplace chaque `TRANSITION` par une phrase de 5 mots sans répétition de mots.")
    return st.text_area("📝 Collez le texte contenant des `TRANSITION`", height=300)

def show_output(title, chapo, text):
    """Display the article with title, chapo, and main text."""
    st.markdown("### 📰 Titre")
    st.markdown(f"**{title}**")
    
    st.markdown("&nbsp;\n&nbsp;\n&nbsp;", unsafe_allow_html=True)
    
    st.markdown("### ✏️ Chapeau")
    st.markdown(chapo)
    
    st.markdown("&nbsp;\n" * 3, unsafe_allow_html=True)
    
    st.markdown("### 🧾 Article")
    st.text_area("📝 Texte avec transitions :", text, height=300)

def show_warning_or_error(missing=False, not_enough=False):
    if missing:
        st.warning("Aucune balise `TRANSITION` trouvée.")
    if not_enough:
        st.error("Pas assez de transitions uniques. Ajoutez-en dans transitions.json.")

def show_version(version_hash):
    st.caption(f"🔄 Version de l'application : `{version_hash}`")
