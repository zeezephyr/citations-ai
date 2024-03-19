import argparse
import os
import streamlit

from chromadb import PersistentClient
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores.chroma import Chroma
from xdg_base_dirs import xdg_data_home

load_dotenv()
parser = argparse.ArgumentParser(description="Ask OpenAI a question")
parser.add_argument("-q", "--question", type=str, help="Specify a question to answer")
parser.add_argument("-w", "--web", action="store_true", help="Start the web interface")
parser.add_argument(
    "-c",
    "--collection",
    type=str,
    default="citations",
    help="The name of the vector collection",
)
data_path = os.path.join(xdg_data_home(), "citations-ai", "data")
parser.add_argument(
    "-d",
    "--data-path",
    type=str,
    default=data_path,
    help="The path to persist the ChromaDB directory",
)
args = parser.parse_args()


def query(question):

    prompt = """
    Answer the following research question. Answer it factually.
    If you do not know the answer say "I do not know the answer".
    If you need additional clarification from the user then ask the user to clarify.
    Use the following additional information to derive your answer:
    {docs}

    The question is: {question}
    """

    client = PersistentClient(
        path=args.data_path, settings=Settings(anonymized_telemetry=False)
    )
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    # collection = client.get_collection(name=args.collection)

    vectorstore = Chroma(
        client=client,
        collection_name=args.collection,
        embedding_function=embedding_function,
    )

    print("Running query")

    docs = vectorstore.similarity_search(question, k=3)
    prompt = ChatPromptTemplate.from_template(prompt)
    model = ChatOpenAI(model="gpt-4", api_key=os.environ["OPEN_AI_API_KEY"])
    output_parser = StrOutputParser()

    chain = prompt | model | output_parser

    result = chain.invoke({"question": question, "docs": docs})

    return result


if args.question:
    result = query(args.question)

    print(result)
    # print(f"Additional references: {[d.metadata['website'] for d in docs]}")

# TODO: Refactor to own module
if args.web:
    if "messages" not in streamlit.session_state:
        streamlit.session_state["messages"] = []

    for message in streamlit.session_state.messages:
        with streamlit.chat_message(message["role"]):
            streamlit.markdown(message["content"])

    with streamlit.chat_message("assistant"):
        streamlit.write("Do you have a question?")

    if question := streamlit.chat_input("Ask a question"):
        streamlit.session_state.messages.append({"role": "user", "content": question})
        with streamlit.chat_message("user"):
            streamlit.markdown(question)

        with streamlit.chat_message("assistant"):
            print(f"Web interface got question: {question}")
            result = query(question)
            response = streamlit.write(result)
            streamlit.session_state.messages.append(
                {"role": "assistant", "content": response}
            )
