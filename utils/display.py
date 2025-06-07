import streamlit as st

def layout_title_and_input():
    st.title("🇫🇷 Générateur de transitions françaises")
    st.markdown("Remplace chaque `TRANSITION` par une phrase de 5 mots sans répétition de mots.")
    return st.text_area("📝 Collez le texte contenant des `TRANSITION`", height=300)

def show_output(title, chapo, text):
    """Display the article with title, chapo, and main content."""
    
    if not title and not chapo and not text:
        st.info("Aucun contenu à afficher.")
        return

    st.markdown("### 📰 Titre")
    st.markdown(f"**{title or 'Titre non défini'}**")

    st.markdown("### ✏️ Chapeau")
    st.markdown(chapo or "Chapeau non défini")

    st.markdown("### 🧾 Article")

    if text:
        # Preserve line breaks in markdown
        formatted_text = text.replace('\n', '  \n')
        with st.expander("📄 Voir l'article complet", expanded=True):
            st.markdown(formatted_text, unsafe_allow_html=True)
    else:
        st.warning("Aucun texte généré pour l'article.")

def show_warning_or_error(missing=False, not_enough=False):
    if missing:
        st.warning("⚠️ Aucune balise `TRANSITION` trouvée dans le texte.")
    if not_enough:
        st.error("🚫 Pas assez de transitions uniques. Veuillez en ajouter dans `transitions.json`.")

def show_version(version_hash):
    st.caption(f"🔄 Version de l'application : `{version_hash}`")
