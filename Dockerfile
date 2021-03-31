From python:alpine

COPY ./ ./
RUN apk add gcc
RUN apk add musl-dev
RUN pip install -r requirements.txt
RUN python -m nltk.downloader stopwords

CMD ["uvicorn", "scPlMongo:app","--host","0.0.0.0"]
