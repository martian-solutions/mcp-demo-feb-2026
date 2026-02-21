FROM python:3.12-slim
WORKDIR /app
COPY python-client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY python-client/song_client.py .
ENV PYTHONUNBUFFERED=1
CMD ["python", "song_client.py"]
