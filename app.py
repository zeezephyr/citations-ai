import argparse
import os

from chromadb import PersistentClient
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings
)
from langchain_community.vectorstores.chroma import Chroma
from xdg_base_dirs import xdg_data_home

load_dotenv()
parser = argparse.ArgumentParser(description="Ask OpenAI a question")
parser.add_argument('question', type=str)
parser.add_argument("-c", "--collection", type=str, default="citations")
data_path = os.path.join(xdg_data_home(), "citations-ai", "data")
parser.add_argument("-d", "--data-path", type=str, default=data_path)
args = parser.parse_args()

prompt = """
Answer the following research question. Answer it factually.
If you do not know the answer say "I do not know the answer".
Use the following additional information to derive your answer:
{docs}

The question is: {question}
"""

client = PersistentClient(path=args.data_path, settings=Settings(anonymized_telemetry=False))
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name=args.collection)

vectorstore = Chroma(
    client=client,
    collection_name=args.collection,
    embedding_function=embedding_function
)

docs = vectorstore.similarity_search(args.question, k=3)
prompt = ChatPromptTemplate.from_template(prompt)
model = ChatOpenAI(model="gpt-4", api_key=os.environ['OPEN_AI_API_KEY'])
output_parser = StrOutputParser()

chain = prompt | model | output_parser

result = chain.invoke({"question": args.question, "docs": docs})

print(result)