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

def create_url_path(keyword):
    url_path = keyword.lower()
    url_path = re.sub(r"[^a-z0-9\s]+", "", url_path)  # Remove non-alphanumeric and non-space characters
    url_path = url_path.replace(" ", "-")  # Replace spaces with hyphens

    # Remove trailing hyphen if present
    if url_path[-1] == "-":
        url_path = url_path[:-1]

    return f"/{url_path}"


def create_full_path(domain, url_path):
    return f"https://{domain}{url_path}"


def generate_content(api_key, prompt, sections):
    openai.api_key = api_key

    system_message = (
        """

You are an AI language model. Your task is to follow the provided outline and ensure that the content is well-structured, SEO-friendly, and addresses the key points in each section.
Make sure to use clear, concise language and provide practical advice, examples, and tips where applicable.

""" )
    
    print(f"Generated prompt:\n{prompt}\n")

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=3200,
        messages=messages
    )

    response = completion.choices[0].message.content.strip()
    return response


def generate_related_links(df, current_topic):
    current_category = df.loc[df['topic'] == current_topic, 'category'].values[0]
    current_full_path = df.loc[df['topic'] == current_topic, 'full path'].values[0]
    related_links = df[df['category'] == current_category][['topic', 'full path']]
    
    # Filter out the self-link by comparing the full paths
    related_links = related_links[related_links['full path'] != current_full_path]

    return related_links.to_dict('records')


def generate_article(api_key, topic, sections, related_links, definition_only=False):
    if definition_only:
        prompt = (
            "Please provide a short, clear and concise definition for the marketing term '{}'."
        ).format(topic)
    else:
        if related_links:
            related_links_prompt = (
    """

    In your HTML output, incorporate the following related links into the article text by using relevant anchor text when applicable. 
    If a link is not directly relevant to the text, include it in the 'related terms' section. Here are the related links to incorporate:\n\n{}.

    """
            ).format(", ".join([f"{rl['topic']} ({rl['full path']})" for rl in related_links]))
        else:
            related_links_prompt = ""

        prompt = (
            """

Please write an informative article about the marketing term '{}' following the given outline:\n\n{}\n
Please provide the output in semantic HTML format (there is no need for the H1). {}"""
        ).format(topic, "\n".join(str(sec) for sec in sections), related_links_prompt)

    article = generate_content(api_key, prompt, sections)
    return article


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.current_tag = None
        self.parent_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in ["ul", "ol"]:
            self.parent_tag = tag

    def handle_endtag(self, tag):
        if tag == self.parent_tag:
            self.parent_tag = None
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag in ["h2", "h3", "h4", "p"]:
            self.text.append({"type": self.current_tag, "content": data.strip()})
        elif self.current_tag == "li":
            self.text.append({"type": self.current_tag, "content": data.strip(), "parent": self.parent_tag})

def save_article_as_docx(filename, title, definition, content):
    # Parse the HTML content
    parser = MyHTMLParser()
    parser.feed(content)
    parsed_content = parser.text

    # Create a new DOCX document
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(definition)

    # Add parsed content to the DOCX document
    for item in parsed_content:
        if item["type"] in ["h2", "h3", "h4"]:
            level = int(item["type"][1])
            doc.add_heading(item["content"], level=level)
        elif item["type"] == "p":
            doc.add_paragraph(item["content"])
        elif item["type"] == "li":
            style = "ListBullet" if item["parent"] == "ul" else "ListNumber"
            doc.add_paragraph(item["content"], style=style)

    # Save the document to a file
    doc.save(filename)

def main():
    st.set_page_config(page_title="AI Content Factory", page_icon=None, layout='centered', initial_sidebar_state='expanded')

    st.title("AI Content Factory")
    st.write("A powerful AI-driven content generation tool for creating high-quality articles at scale.")
    
    # Add an expander to provide a detailed overview, benefits, and step-by-step instructions
    with st.expander("About Content Factory"):
        st.markdown("""
Content Factory is an advanced content generation tool that leverages the capabilities of the OpenAI GPT-4 language model to create high-quality, informative articles at scale. Designed for a wide range of topics, this tool can be easily customized to cater to your specific content requirements.

**Overview:**

The Content Factory tool offers a user-friendly interface through Streamlit, allowing users to:

1. Configure the model settings
2. Input the required information, such as API key, domain, and CSV file containing the topics and outlines
3. Generate articles, including definitions and related links
4. Save the generated content in a convenient `.docx` format and a CSV file
5. Download the generated files as a `.zip` package for easy usage

**Benefits:**

- Efficient content generation at scale
- High-quality, AI-generated content tailored to your specific requirements
- User-friendly interface for seamless interaction
- Easy customization to fit a wide range of content generation needs

**Step-by-step guide:**

1. Run the Content Factory app locally or deploy it on a cloud service
2. Enter your API key, domain, and upload a CSV file containing your topics and outlines
3. Adjust the settings as needed, including model, temperature, max tokens, and other options
4. Click the "Generate Articles" button
5. Download the generated `.zip` file containing the articles in `.docx` format and a CSV file with the generated content
6. Review, edit, and utilize the generated content as needed
""")

    with st.sidebar:
        st.header("Settings")

        api_key = st.text_input("API Key:", value="", type="password")
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

        domain = st.text_input("Domain Name:", value="https://www.your-domain.com")

        # Model and settings
        model = st.selectbox("Model:", ["gpt-3.5-turbo", "gpt-4"])
        # top_p = st.slider("Top P:", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
        temperature = st.slider("Temperature:", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
        max_tokens = st.slider("Max Tokens:", min_value=1, max_value=8000, value=2048, step=1)
        presence_penalty = st.slider("Presence Penalty:", min_value=-2.0, max_value=2.0, value=0.2, step=0.1)
        frequency_penalty = st.slider("Frequency Penalty:", min_value=-2.0, max_value=2.0, value=0.2, step=0.1)

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
