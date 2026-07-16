FROM python:3.11-slim

RUN useradd --create-home --shell /usr/sbin/nologin executor
WORKDIR /app

COPY --chmod=755 requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chmod=755 . .

USER executor
EXPOSE 8010
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
