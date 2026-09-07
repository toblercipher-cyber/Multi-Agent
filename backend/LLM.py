#importing LLms -> for our specific tasks .

#x----------------------x---------------------x-------------------------x-------------------------------x------------
import os
from dotenv import load_dotenv
from langchain_cerebras import ChatCerebras
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


load_dotenv()  # Load environment variables from .env file


#fallback_model:
llm_3= ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.4)

# analysis_model:
llm_1 = ChatGroq(model="openai/gpt-oss-20b", temperature=0.4, max_tokens=1000)

#reasoning_model:
llm_2 = ChatMistralAI(model="mistral-large-latest", temperature=0.4, max_tokens=1000)
