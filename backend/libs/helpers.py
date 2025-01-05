import os
import shutil
from typing import List, Dict
import urllib.request
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from dotenv import load_dotenv
import json
import urllib.parse
import logging

logger = logging.getLogger("main")
load_dotenv()

EMBED_MODEL = os.environ.get("EMBED_MODEL")
LLM_MODEL = os.environ.get("LLM_MODEL")
VECTOR_DIRECTORY = os.environ.get("VECTOR_DIRECTORY")
UPLOAD_DIRECTORY = os.environ.get("UPLOAD_DIRECTORY")


def fn(res):
    toret = []
    for i, y in enumerate(res):
        x = y[0]
        ret = f"Reference {i+1}\nSource: {x.metadata['source']} (Page {x.metadata['page']+1})\nContent: {x.page_content}"
        toret.append(ret)
    toret = "\n\n\n".join(toret).strip()
    return toret


def pdf_to_url(path: str, page_number: int):
    file_url = urllib.parse.urljoin(
        "http://localhost:8000/fileserver", urllib.request.pathname2url(path)
    )
    return f"{file_url}#page={page_number}"


async def handle_query(text: str) -> Dict[str, str]:
    print(f"handling query: {text}")

    relevant_docs = await fetch_relevant(text, 5, 0.5)  # list[tuple[Document, float]]

    ctx = (
        fn(relevant_docs)
        if relevant_docs
        else "[No context is given. Answer without context.]]"
    )

    prompt = f"""
The user has the following query: {text}
Following is information to help answer this query. If using information from a reference, quote it like (Ref 1) or (Ref 2) etc:
{ctx}
""".strip()

    print(f"Invoking model: {LLM_MODEL}")

    model = OllamaLLM(model=LLM_MODEL)
    response = await model.ainvoke(prompt)

    return {
        "response": response,
        "sources": [
            pdf_to_url(x[0].metadata["source"], x[0].metadata["page"] + 1)
            for x in relevant_docs
        ],
    }


async def embed_and_save_pdf(docnames: List[str]) -> None:
    """Given a path of pdf file, convert to embeddings and store them in a vectore store

    Args:
        path (str): Path to the pdf file
    """

    print(f"loading: {len(docnames)} doc(s)")

    pages = []
    for docname in docnames:
        loader = PyPDFLoader(os.path.join(UPLOAD_DIRECTORY, docname))
        async for page in loader.alazy_load():
            pages.append(page)

    print(f"Pages: {len(pages)}")

    model = OllamaEmbeddings(model=EMBED_MODEL)
    newvs = await FAISS.afrom_documents(pages, model)

    if len(os.listdir(VECTOR_DIRECTORY)) != 0:
        vs = FAISS.load_local(
            VECTOR_DIRECTORY, model, allow_dangerous_deserialization=True
        )
        vs.merge_from(newvs)
        vs.save_local(VECTOR_DIRECTORY)
        print(f"Merged to {VECTOR_DIRECTORY}")

    else:
        newvs.save_local(VECTOR_DIRECTORY)
        print(f"Saved to {VECTOR_DIRECTORY}")


async def fetch_relevant(text: str, k, threshold) -> list[tuple[Document, float]]:
    model = OllamaEmbeddings(model=EMBED_MODEL)
    vs = FAISS.load_local(VECTOR_DIRECTORY, model, allow_dangerous_deserialization=True)
    if k is None:
        k = 100
    res = await vs.asimilarity_search_with_relevance_scores(text, k=k)
    res = [x for x in res if x[1] >= threshold]
    print(
        f"Fetched {len(res)} pages [{', '.join(str(int(x[1]*100)/100) for x in res)}]"
    )
    return res


def empty_folder(folder: str):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            print(f"Deleted '{file_path}'")
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))
