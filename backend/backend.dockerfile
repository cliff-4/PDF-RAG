FROM python:3.10-slim
WORKDIR /backend

# Install Python build tools
RUN pip install --upgrade pip setuptools wheel

# Copy the backend code into the container
COPY pyproject.toml pyproject.toml

# Install Python dependencies
RUN pip install .

COPY . .

# Expose the backend port
EXPOSE 8000

# Start the services
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
