import os
import shutil
from typing import List, Dict
import urllib.request
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

EMBED_MODEL = os.environ.get("EMBED_MODEL")
VECTOR_DIRECTORY = os.environ.get("VECTOR_DIRECTORY")
UPLOAD_DIRECTORY = os.environ.get("UPLOAD_DIRECTORY")
OLLAMA_SERVER = os.environ.get("OLLAMA_SERVER")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


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
        f"http://localhost:8000/fileserver/", urllib.request.pathname2url(path)
    )
    res = f"{file_url}#page={page_number}"
    print(f"{path} and {page_number} -> {res}")
    return res


async def handle_query(text: str) -> Dict[str, str]:
    print(f"handling query: {text}")

    relevant_docs = await fetch_relevant(text, 5, 0.4)  # list[tuple[Document, float]]

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

    # print(f"Invoking model: openhermes")
    # model = OllamaLLM(model="openhermes", base_url=OLLAMA_SERVER)
    print(f"Invoking model: {GEMINI_MODEL}")
    model = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)
    response = (await model.ainvoke(prompt)).content

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
        loader = PyPDFLoader(os.path.join(UPLOAD_DIRECTORY, docname).replace("\\", "/"))
        async for page in loader.alazy_load():
            page.metadata["source"] = page.metadata["source"][
                len(UPLOAD_DIRECTORY) + 1 :
            ]
            pages.append(page)

    print(f"Pages: {len(pages)}")

    model = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_SERVER)
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
    model = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_SERVER)
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
