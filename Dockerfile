FROM python:3.11-buster

RUN mkdir app
WORKDIR /app

#ENV PATH="${PATH}:/root/.local/bin"
#ENV PYTHONPATH=/app

COPY README.md /app
COPY pyproject.toml /app
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
