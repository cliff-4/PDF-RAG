FROM python:3.10-slim
WORKDIR /backend

# Installation
RUN pip install --upgrade pip setuptools wheel
COPY pyproject.toml pyproject.toml
RUN pip install -e .

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
