FROM python:3.12-slim
RUN pip install --no-cache-dir confluent-kafka==2.5.3
WORKDIR /app
COPY generate.py .
USER nobody
CMD ["python", "generate.py"]
