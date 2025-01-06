FROM ollama/ollama

COPY ollama_server_start.sh /tmp/ollama_server_start.sh

WORKDIR /tmp

RUN chmod +x ollama_server_start.sh
RUN ./ollama_server_start.sh

EXPOSE 11434
