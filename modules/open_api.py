from pydantic import BaseModel
from openai import OpenAI
import pandas as pd
import os
import json

class Pointer(BaseModel):
    subtext: str
    advice: str
    reflection: str

def getPointer(user_subtext=None):
    # Retrieve API key from environment
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    
    # Set current working directory and conversation file path
    CWD = os.getcwd()
    CONVO_FILEPATH = os.path.join(CWD, "convo_data.csv")

    # Initialize the OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Read conversation history from CSV
    data = pd.read_csv(CONVO_FILEPATH)

    # Construct the prompt including conversation history and optional subtext
    prompt = (
        f"I'm in the middle of a conversation with someone, some of their previous statements in table format are: {data}.\n"
        f"The latest statement is the last line in the sheet."
    )
    if user_subtext:
        prompt += f" The user's new subtext is: {user_subtext}.\n"
    prompt += (
        " Considering the associated emotion and confidence level, give a maximum of 50 characters on any subtext being conveyed, "
        "50 more characters on any advice on how to act in this situation, and finally 150 characters on things to reflect on after the conversation is over. "
        "Provide full context for this."
    )

    # Generate the pointer via the OpenAI client using our Pointer model as the response format
    pointer = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=Pointer,
    )
    
    # Try to convert the pointer to a dictionary
    try:
        pointer_dict = pointer.dict()
    except Exception:
        try:
            raw = pointer.choices[0].message.content
            if isinstance(raw, str):
                pointer_dict = json.loads(raw)
            else:
                pointer_dict = raw
        except Exception:
            pointer_dict = {}

    # Ensure the dictionary contains the expected keys with empty string fallback if necessary.
    for key in ["subtext", "advice", "reflection"]:
        if key not in pointer_dict:
            pointer_dict[key] = ""
    
    return pointer_dict
