FROM python:3.11-slim-buster
WORKDIR /python-docker
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY main.py main.py
COPY app/ app/
CMD ["python3.11", "-m", "main"]
