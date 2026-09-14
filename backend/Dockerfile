FROM python:3.12-slim
WORKDIR /app
COPY backend /app/backend
COPY alembic.ini /app/alembic.ini
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
ENV AIR_GAPPED_MODE=true \
    OCR_ENABLED=true \
    OCR_MODEL_DIR=/app/backend/ocr_models \
    OCR_LANGUAGE=en \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
EXPOSE 8001
CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port 8001"]
