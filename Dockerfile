FROM python:3.10.1-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/main.py main.py
COPY src/shortcut.py shortcut.py

CMD ["python", "/app/main.py"]
