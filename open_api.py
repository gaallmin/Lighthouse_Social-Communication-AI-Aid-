from openai import OpenAI
import os
import pandas as pd

# API Key in .env file
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Current working directory
CWD = os.getcwd()

# Conversation data filepath
CONVO_FILEPATH = os.path.join(CWD,"convo_data.csv")

client = OpenAI(api_key=OPENAI_API_KEY)

data = pd.read_csv(CONVO_FILEPATH)

prompt= f""" I'm speaking to someone, some of their previous statements in table format are: {data}. Their latest statement\
        is the last line in the sheet. Considering the associated emotion and confidence level, give maximum 8 words on any\
        subtext that is being conveyed and 8 more on any advice you would give on how to act in this situation."""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user", 
            "content": prompt
        }
    ]
)

print(response.choices[0].message.content)