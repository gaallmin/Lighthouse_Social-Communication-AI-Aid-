from pydantic import BaseModel
from openai import OpenAI
import os


class Pointer(BaseModel):
    subtext: str
    advice: str
    reflection: str

def getPointer():
    # API Key in .env file
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # Current working directory
    CWD = os.getcwd()

    # Conversation data filepath
    CONVO_FILEPATH = os.path.join(CWD,"convo_data.csv")

    client = OpenAI(api_key=OPENAI_API_KEY)

    data = pd.read_csv(CONVO_FILEPATH)

    prompt= f""" I'm in the middle of a conversation with someone, some of their previous statements in table format are: {data}.\
            Their latest statement is the last line in the sheet. Considering the associated emotion and confidence level, give \
            maximum 50 characters on any subtext that is being conveyed and 50 more characters on any advice you would give on \
            how to act in this situation, finally give 150 characters on things to reflect on after the conversation is over, give full context for this."""

    pointer = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user", 
                "content": prompt
            }
        ],
        response_format=Pointer,
    )

    return pointer

pointer = getPointer()
print(pointer.choices[0].message.content)