import os
import aiofiles
from pathlib import Path
import logging

# Linting
from pydantic import BaseModel
from typing import List

# FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Custom definitions
from libs.helpers import handle_query, embed_and_save_pdf
from libs.utils import get_config, empty_folder

logger = logging.getLogger("uvicorn.error")

UPLOAD_DIRECTORY = get_config("UPLOAD_DIRECTORY")
VECTOR_DIRECTORY = get_config("VECTOR_DIRECTORY")
BACKEND_DIR = Path("./uploaded_files").resolve()

logger.debug(f"UPLOAD_DIRECTORY = {UPLOAD_DIRECTORY}")
logger.debug(f"VECTOR_DIRECTORY = {VECTOR_DIRECTORY}")
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

if not os.path.exists(VECTOR_DIRECTORY):
    os.makedirs(VECTOR_DIRECTORY)

app = FastAPI()

# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)
):
    try:
        docnames = []
        for file in files:
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only PDF files are accepted.",
                )

            file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
            if os.path.exists(file_path):  # hehe
                raise HTTPException(status_code=403, detail="File already exists")

            async with aiofiles.open(file_path, "wb") as out_file:
                content = await file.read()  # Read file content in chunks
                await out_file.write(content)  # Write chunks to the file system
            docnames.append(file.filename)
            logger.debug(f"Saved {file.filename}")

        background_tasks.add_task(embed_and_save_pdf, docnames)

        return JSONResponse(
            status_code=200,
            content={"message": f"Successfully uploaded {len(files)} file(s)"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/count")
async def count_files():
    files = os.listdir(UPLOAD_DIRECTORY)
    pdf_files_count = len([name for name in files if name.lower().endswith(".pdf")])
    return JSONResponse(content={"pdf_files_count": pdf_files_count})


@app.get("/files/size")
async def get_total_size():
    total_size = sum(
        os.path.getsize(os.path.join(UPLOAD_DIRECTORY, f))
        for f in os.listdir(UPLOAD_DIRECTORY)
        if f.lower().endswith(".pdf")
    )
    return JSONResponse(content={"total_size_bytes": total_size})


class QueryRequest(BaseModel):
    inputValue: str


@app.post("/ask")
async def ask_query(request: QueryRequest):
    res = await handle_query(request.inputValue)
    return JSONResponse(content=res)


class ClearFileRequest(BaseModel):
    password: str


@app.post("/clearfiles")
async def clear_files(request: ClearFileRequest):
    if request.password != "poopybutthole":
        raise HTTPException(
            status_code=403, detail=f"{request.password} is incorrect password"
        )
    try:
        empty_folder(UPLOAD_DIRECTORY)
        empty_folder(VECTOR_DIRECTORY)
        return JSONResponse(content={"msg": "Successfully cleared all files!"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fileserver", response_class=HTMLResponse)
async def list_directory():
    """
    Lists all files and subdirectories in the `backend/` folder.
    """
    if not BACKEND_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    # Create an HTML listing for the directory
    files = os.listdir(BACKEND_DIR)
    html_content = "<html><body><h2>Uploaded Files</h2>"
    if files:
        html_content += "<ul>"
        for file in files:
            file_path = f"/fileserver/{file}"  # Use endpoint to link to the file
            html_content += f'<li><a href="{file_path}" target="_blank">{file}</a></li>'
        html_content += "</ul>"
    else:
        html_content += "<p><i>Directory is empty</i></p>"
    html_content += "</body></html>"

    return HTMLResponse(content=html_content)


@app.get("/fileserver/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serves files from the specified backend directory.
    """
    file = BACKEND_DIR / file_path

    # Resolve the file path to avoid directory traversal attacks
    try:
        file = file.resolve(strict=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    # Check if the file is within the backend directory
    if not str(file).startswith(str(BACKEND_DIR)):
        raise HTTPException(status_code=403, detail="Access forbidden")

    # If it's a directory, list its contents
    if file.is_dir():
        files = os.listdir(file)
        html_content = f"<html><body><h2>Directory: {file_path}</h2><ul>"
        for subfile in files:
            subfile_path = f"/{file_path}/{subfile}".replace(
                "//", "/"
            )  # Fix double slashes
            html_content += f'<li><a href="{subfile_path}">{subfile}</a></li>'
        html_content += "</ul></body></html>"
        return HTMLResponse(content=html_content)

    # If it's a file, serve it
    if file.is_file():
        return FileResponse(file)

    # If the file does not exist
    raise HTTPException(status_code=404, detail="File not found")
