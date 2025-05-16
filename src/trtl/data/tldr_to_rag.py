"""
This scripts reads all of the manual pages 
of a bunch of commandline tools that are in the tldr 
project. 

It expects the tldr dir to be in the same scope
as the agent dir. 
"""

import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# === CONFIG ===
TLDR_PATH = "../../../tldr/pages/common"  # Adjust if needed
PERSIST_DIR = "./tldr_rag_db"
COLLECTION_NAME = "tldr_manuals"

# === LOAD & CHUNK FILES ===
docs = []
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)

for file_path in Path(TLDR_PATH).glob("*.md"):
    tool = file_path.stem
    content = file_path.read_text(encoding="utf-8")

    # Extract the first quoted line as the tool description
    desc_match = re.search(r"> (.*?)\n", content)
    description = desc_match.group(1).strip() if desc_match else ""

    chunks = splitter.create_documents(
        [content], metadatas=[{"tool": tool, "description": description}]
    )
    docs.extend(chunks)

# === EMBED & PERSIST ===
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name=COLLECTION_NAME,
    persist_directory=PERSIST_DIR,
)
db.persist()
print(f"✅ RAG DB built with {len(docs)} chunks for {TLDR_PATH}")
