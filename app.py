import streamlit as st
from utils.io import load_examples, load_all_transitions
from utils.processing import get_transition_from_gpt
from utils.layout import rebuild_article_with_transitions
from utils.display import layout_title_and_input, show_output, show_version
from utils.version import compute_version_hash
from utils.title_blurb import generate_title_and_blurb
from utils.logger import save_output_to_file, logger
from utils.validate_prompt_compliance import validate_batch, display_validation_results
from datetime import datetime
import pandas as pd
import io

def process_uploaded_files(uploaded_files):
    """Process multiple uploaded files and return a list of (filename, transitions) tuples."""
    results = []
    
    for uploaded_file in uploaded_files:
        try:
            # Read the file content
            content = uploaded_file.getvalue().decode('utf-8')
            
            # Split into lines and process
            lines = content.strip().split('\n')
            transitions = []
            
            # Extract transitions from the content
            for line in lines:
                line = line.strip()
                if line.startswith("Transitions générées:"):
                    continue
                if line and line[0].isdigit() and ". " in line:
                    # Extract transition text after the number and period
                    transition = line.split(". ", 1)[1].strip()
                    transitions.append(transition)
            
            if transitions:
                filename = uploaded_file.name
                results.append((filename, transitions))
                
        except Exception as e:
            logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
            continue
            
    return results

def main():
    # Compute version hash for traceability
    VERSION = compute_version_hash([
        "app.py",
        "transitions.json",
        "utils/io.py",
        "utils/processing.py",
        "utils/layout.py",
        "utils/display.py",
        "utils/version.py",
        "utils/title_blurb.py",
        "utils/logger.py"
    ])

    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✨ Générer les transitions", 
        "📝 Résultat", 
        "✅ Validation",
        "💾 Sauvegarde",
        "📤 Upload par lot"
    ])

    with tab1:
        # Display input UI
        text_input = layout_title_and_input()

        if st.button("✨ Générer les transitions"):
            if "TRANSITION" not in text_input:
                st.warning("Aucune balise `TRANSITION` trouvée.")
                return
            try:
                # Load few-shot examples
                examples = load_examples()
                logger.info("Successfully loaded examples")

                # Split input into paragraph pairs
                parts = text_input.split("TRANSITION")
                pairs = list(zip(parts[:-1], parts[1:]))
                logger.info(f"Processing {len(pairs)} paragraph pairs")

                # Generate title and blurb from the first paragraph
                title_blurb = generate_title_and_blurb(parts[0])
                logger.info("Generated title and blurb")

                # Generate transitions for each paragraph pair
                generated_transitions = []
                for i, (para_a, para_b) in enumerate(pairs, 1):
                    transition = get_transition_from_gpt(para_a, para_b, examples)
                    generated_transitions.append(transition)
                    logger.info(f"Generated transition {i}/{len(pairs)}")

                # Rebuild the full article
                rebuilt_text, error = rebuild_article_with_transitions(text_input, generated_transitions)
                if error:
                    logger.error(f"Error rebuilding article: {error}")
                    st.error(error)
                    return

                # Store results in session state
                if isinstance(title_blurb, dict):
                    st.session_state['title_text'] = title_blurb.get('title', 'Titre non défini')
                    st.session_state['chapo_text'] = title_blurb.get('chapo', 'Chapeau non défini')
                else:
                    st.session_state['title_text'] = 'Titre non défini'
                    st.session_state['chapo_text'] = 'Chapeau non défini'
                
                st.session_state['rebuilt_text'] = rebuilt_text
                st.session_state['generated_transitions'] = generated_transitions

            except Exception as e:
                error_msg = f"Une erreur est survenue: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)

    with tab2:
        if 'rebuilt_text' in st.session_state:
            show_output(
                st.session_state['title_text'],
                st.session_state['chapo_text'],
                st.session_state['rebuilt_text']
            )

    with tab3:
        if 'generated_transitions' in st.session_state:
            # Get current timestamp for filename
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"article_{current_time}.txt"
            
            # Validate transitions with filename
            validation_results = validate_batch([(filename, st.session_state['generated_transitions'])])
            logger.info(f"Validation results: {validation_results}")
            display_validation_results(validation_results)

    with tab4:
        if 'rebuilt_text' in st.session_state:
            # Save output to file and upload to GoogleDrive
            filepath = save_output_to_file(
                st.session_state['title_text'],
                st.session_state['chapo_text'],
                st.session_state['rebuilt_text'],
                st.session_state['generated_transitions']
            )
            if filepath:
                st.success(f"✅ L'article a été sauvegardé dans `{filepath}` et uploadé sur GoogleDrive")
                logger.info(f"Successfully saved and uploaded article to {filepath}")
                
                # Add Google Drive folder link
                st.markdown("### 📁 Accès aux fichiers")
                st.markdown(f"""
                Vous pouvez accéder à tous les fichiers générés dans le dossier Google Drive :
                - [Ouvrir le dossier Google Drive](https://drive.google.com/drive/folders/{st.secrets.get("gdrive_folder_id")})
                """)
            else:
                st.warning("⚠️ L'article a été sauvegardé localement mais l'upload sur GoogleDrive a échoué")
                logger.warning("Article saved locally but GoogleDrive upload failed")

    with tab5:
        st.markdown("### 📤 Upload par lot")
        st.markdown("""
        Vous pouvez uploader un fichier texte contenant des transitions à valider.
        Le fichier doit être formaté comme suit:
        ```
        nom_du_fichier.txt
        transition1
        transition2
        transition3
        ```
        """)
        
        uploaded_files = st.file_uploader("Choisir des fichiers depuis Google Drive", type=['txt'], accept_multiple_files=True, key="gdrive_uploader")
        st.markdown(f"""
        Ou accédez directement au dossier Google Drive :
        [Ouvrir le dossier Google Drive](https://drive.google.com/drive/folders/{st.secrets.get("gdrive_folder_id")})
        """)
        if uploaded_files is not None:
            # Process the uploaded file
            batch_results = process_uploaded_files(uploaded_files)
            if batch_results:
                # Validate the batch
                validation_results = validate_batch(batch_results)
                display_validation_results(validation_results)
            else:
                st.warning("⚠️ Le fichier n'a pas pu être traité. Vérifiez le format.")

    # Always display version hash
    show_version(VERSION)

if __name__ == "__main__":
    main()
