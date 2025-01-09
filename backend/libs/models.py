import os
from typing import List
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from libs.utils import get_config, benchmark
import logging

logger = logging.getLogger("uvicorn.error")


VECTOR_DIRECTORY = get_config("VECTOR_DIRECTORY")


@benchmark("Fetched LLM response")
async def get_llm_response(prompt: str) -> str:
    llm_conf = get_config("ai", "llm")
    if llm_conf["type"] == "gemini":
        logger.debug("Using Gemini")
        model = ChatGoogleGenerativeAI(
            model=llm_conf["model"], api_key=llm_conf["api_key"]
        )
        response = await model.ainvoke(prompt)
        return response.content
    elif llm_conf["type"] == "ollama":
        logger.debug("Using openhermes")
        model = OllamaLLM(model=llm_conf["model"], base_url=llm_conf["base_url"])
        response = await model.ainvoke(prompt)
        return response


@benchmark("Fetched pages")
async def fetch_relevant(
    text: str, k: int, threshold: float
) -> list[tuple[Document, float]]:
    model = get_embedding_model()
    try:
        vs = FAISS.load_local(
            VECTOR_DIRECTORY, model, allow_dangerous_deserialization=True
        )
    except Exception as e:
        return []
    res = await vs.asimilarity_search_with_relevance_scores(text, k=k)
    res = [x for x in res if x[1] >= threshold]
    return res


def get_embedding_model() -> Embeddings:
    emb_conf = get_config("ai", "embed")
    if emb_conf["type"] == "ollama":
        model = OllamaEmbeddings(model=emb_conf["model"], base_url=emb_conf["base_url"])
    else:
        # To be written for other providers
        pass
    return model


@benchmark("Generated and saved embeddings")
async def store_local(pages: List[Document]) -> None:
    model = get_embedding_model()
    newvs = await FAISS.afrom_documents(pages, model)

    if len(os.listdir(VECTOR_DIRECTORY)) != 0:
        vs = FAISS.load_local(
            VECTOR_DIRECTORY, model, allow_dangerous_deserialization=True
        )
        vs.merge_from(newvs)
        vs.save_local(VECTOR_DIRECTORY)
        logger.debug(f"Merged embeddings to existing")

    else:
        newvs.save_local(VECTOR_DIRECTORY)
        logger.debug(f"Created new vector store")
