import streamlit as st
import openai
import pandas as pd
import time
import re
import os
import zipfile
from io import BytesIO
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from html.parser import HTMLParser

# Helper functions and classes remain the same

def main():
    st.set_page_config(page_title="Article Generator", page_icon=None, layout='wide', initial_sidebar_state='expanded')

    st.title("Article Generator")
    st.write("This app generates articles based on prompts loaded from a CSV file. Provide the necessary details and click the button to generate articles.")

    with st.sidebar:
        st.header("Settings")

        api_key = st.text_input("API Key:", value="")
        uploaded_file = st.file_uploader("CSV File:", type=["csv"])

        domain = st.text_input("Domain Name:", value="")

        # Model and settings
        model = st.selectbox("Model:", ["gpt-3.5-turbo", "gpt-4"])
        top_p = st.slider("Top P:", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
        temperature = st.slider("Temperature:", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
        max_tokens = st.slider("Max Tokens:", min_value=1, max_value=4096, value=2048, step=1)
        presence_penalty = st.slider("Presence Penalty:", min_value=0.0, max_value=2.0, value=0.0, step=0.1)
        frequency_penalty = st.slider("Frequency Penalty:", min_value=0.0, max_value=2.0, value=0.0, step=0.1)

    if st.button("Generate Articles"):
        if not api_key or not domain or not uploaded_file:
            st.error("Please provide all required inputs (API Key, Domain Name, and CSV File).")
            return

        df = pd.read_csv(uploaded_file)
        df.columns = map(str.lower, df.columns)
        df["url path"] = df["keyword / h1"].apply(create_url_path)
        df["full path"] = df["url path"].apply(lambda x: create_full_path(domain, x))

        topics = df["topic"].tolist()
        h1_keywords = df["keyword / h1"].tolist()
        sections = df.iloc[:, 7:].values.tolist()

        definitions = []
        articles = []
        for topic, sec in zip(topics, sections):
            related_links = generate_related_links(df, topic)

            definition = generate_article(api_key, topic, sec, related_links, definition_only=True)
            definitions.append(definition)
            time.sleep(7)

            article = generate_article(api_key, topic, sec, related_links, definition_only=False)
            articles.append(article)
            time.sleep(7)

        df["definition"] = definitions
        df["article"] = articles

        os.makedirs("generated_articles", exist_ok=True)

        for idx, (topic, h1_keyword, definition, article) in enumerate(zip(topics, h1_keywords, definitions, articles)):
            docx_filename = f"generated_articles/{topic.replace(' ', '_')}_article.docx"
            save_article_as_docx(docx_filename, h1_keyword, definition, article)

        output_file = "generated_articles/generated_articles.csv"
        df.to_csv(output_file, index=False)

        with zipfile.ZipFile("generated_articles.zip", "w") as zipf:
            for folder, _, filenames in os.walk("generated_articles"):
                for filename in filenames:
                    file_path = os.path.join(folder, filename)
                    zipf.write(file_path, os.path.basename(file_path))

        st.success("Generated articles and definitions added to 'generated_articles.zip'.")

        with open("generated_articles.zip", "rb") as f:
            bytes = f.read()
            b = BytesIO(bytes)
            st.download_button("Download Generated Articles", b, "generated_articles.zip", "application/zip")

if __name__ == "__main__":
    main()