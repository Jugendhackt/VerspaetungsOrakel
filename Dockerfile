FROM python:3.11-alpine AS run

WORKDIR /app

COPY requirements.lock ./
RUN sed '/-e/d' requirements.lock > requirements.txt && \
    pip install -r requirements.txt
COPY static/ static/
COPY templates/ templates/
COPY verspaetungsorakel/ verspaetungsorakel/
COPY entrypoint.sh pyproject.toml ./
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ./entrypoint.sh
