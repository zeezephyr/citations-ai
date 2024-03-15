import os
import argparse
from dotenv import load_dotenv

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import docarray
from langchain_community.vectorstores.chroma import Chroma

load_dotenv()
parser = argparse.ArgumentParser(description="Ask OpenAI a question")
parser.add_argument('prompt', type=str)
args = parser.parse_args()

# vectorstore = Chroma.from_documents()
# vectorstore = docarray.DocArrayHnswSearch.from_documents()
prompt = ChatPromptTemplate.from_template("{topic}")
model = ChatOpenAI(model="gpt-4", api_key=os.environ['OPEN_AI_API_KEY'])
output_parser = StrOutputParser()

chain = prompt | model | output_parser

result = chain.invoke({"topic": args.prompt})

print(result)