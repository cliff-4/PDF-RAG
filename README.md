# README

Welcome to this PDF RAG application.

To start your own server, you need to have docker installed and running.

Next, you will need a gemini API key, which you will need to update at `backend/.env` and `docker-compose.yml`.

## Steps to run in Docker

1. Download the repository
2. `docker-compose up --build`
3. Access the web-app at `http://localhost:3000/upload`

## Steps to run without Docker

You will need three terminal instances. Make sure you have Ollama installed and running with `nomic-embed-text` already pulled. Thre three terminal instances will run the following:

1. `cd` to backend and `.\.venv\Scripts\uvicorn.exe main:app --reload`
2. `ollama serve`
3. `cd` to frontend and `npm run dev`
