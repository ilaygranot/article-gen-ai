# AI ContentFactory
ContentFactory is a powerful and efficient content generation tool that leverages the capabilities of advanced AI language models to create high-quality, informative articles at scale. This project is designed for a wide range of topics and can be easily customized to cater to your specific content requirements.

## Overview
The ContentFactory tool utilizes the OpenAI GPT-4 language model to generate articles based on provided keywords and an outline. It offers a user-friendly interface through Streamlit, allowing users to configure the model settings and input the required information, such as API key, domain, and CSV file containing the topics and outlines.

Once the user has provided the necessary details and clicked the "Generate Articles" button, the tool generates articles, including definitions and related links, and saves them in a convenient .docx format, along with a CSV file containing the generated content. Finally, the generated files are packaged into a .zip file for easy download and usage.

## Requirements
To run ContentFactory, you'll need the following:

* Python 3.6 or later
* OpenAI API key (sign up at https://beta.openai.com/signup/)

The following Python libraries, which can be installed via requirements.txt:
* streamlit
* openai
* pandas
* python-docx
* html5lib

To install the required libraries, run:
pip install -r requirements.txt
 
## How to Run ContentFactory Locally

Clone this repository or download the project files.

Navigate to the project folder in your terminal or command prompt.

Run the following command:
streamlit run app.py

* Open your web browser and visit the URL displayed in the terminal (usually http://localhost:8501).
* Enter your API key, domain, and upload a CSV file containing your topics and outlines.
* Adjust the settings as needed, and click the "Generate Articles" button.
* Deploying ContentFactory to Streamlit Sharing

To deploy the ContentFactory app to Streamlit Sharing, follow the instructions in this guide.

## Customizing ContentFactory
ContentFactory can be easily customized to fit your specific content generation needs. You can modify the main.py and app.py files to adjust the user interface, model settings, or implement additional features.

## License
ContentFactory is an open-source project distributed under the MIT License. Feel free to use, modify, and distribute the project as needed.

## Acknowledgements
ContentFactory utilizes the OpenAI GPT-4 language model, which is developed and maintained by OpenAI. The project is also powered by Streamlit, an open-source app framework for Python.
