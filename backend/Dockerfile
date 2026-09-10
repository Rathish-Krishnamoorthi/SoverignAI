FROM python:3.11-slim
WORKDIR /app
COPY . /app/backend
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
EXPOSE 8001
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
