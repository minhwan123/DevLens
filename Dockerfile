FROM python:3.12-slim

WORKDIR /app

# sentence-transformers pulls in torch, so this layer is heavy but stable — keep it
# separate from the app code so edits to devlens/ don't invalidate it.
COPY pyproject.toml ./
COPY devlens ./devlens
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "devlens.interface.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
