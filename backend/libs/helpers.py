import os
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from libs.utils import pdf_to_url, get_config
import logging

logger = logging.getLogger("uvicorn.error")


UPLOAD_DIRECTORY = get_config("UPLOAD_DIRECTORY")


async def handle_query(text: str) -> Dict[str, str]:
    """Handle a query coming in from the frontend

    Args:
        text (str): Query string

    Returns:
        Dict[str, str]: Dictionary containing response string and List[Dict] of source URLs
    """
    logger.debug(f"Handling query: {(text if len(text) <= 20 else text[:17]+'...')}")

    relevant_docs = await libs.models.fetch_relevant(text, 5, 0.4)

    def concat(docs):
        formatted_docs = []
        for i, page_probability in enumerate(docs):
            page = page_probability[0]
            formatted_page = f"""
Reference {i+1}
Source: {page.metadata['source']} (Page {page.metadata['page']+1})
Content: {page.page_content}
""".strip()
            formatted_docs.append(formatted_page)
        context = "\n\n".join(formatted_docs).strip()
        return context

    ctx = (
        concat(relevant_docs)
        if relevant_docs
        else "[No context is given. Answer without context.]"
    )

    prompt = f"""
The user has the following query: {text}
Following is information to help answer this query. If using information from a reference, quote it like (Ref 1) or (Ref 2) etc:
{ctx}
""".strip()

    response = await libs.models.get_llm_response(prompt)

    return {
        "response": response,
        "sources": [
            pdf_to_url(x[0].metadata["source"], x[0].metadata["page"] + 1)
            for x in relevant_docs
        ],
    }


# Paths used
async def embed_and_save_pdf(docnames: List[str]) -> None:
    """Given a list of pdf paths, convert to embeddings and store them in a vectore store

    Args:
        docnames (List[str]): List of file paths
    """

    logger.debug(f"Loading {len(docnames)} doc(s)")

    pages: List[Document] = []
    try:
        for i, docname in enumerate(docnames):
            logger.debug(f"Doc {i+1} of {len(docnames)}")

            loader = PyPDFLoader(
                os.path.join(UPLOAD_DIRECTORY, docname).replace("\\", "/")
            )
            async for page in loader.alazy_load():
                page.metadata["source"] = page.metadata["source"][
                    len(UPLOAD_DIRECTORY) + 1 :
                ]
                pages.append(page)

        logger.debug(f"Embedding {len(pages)} pages")

        await libs.models.store_local(pages)
    except Exception as e:
        logger.error(f"An error occured: {e}")
