FROM python:3.11.9-alpine3.20
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PORT=8000
ENV DOCKER=1
ENV DEBUG=0
CMD [ "sh", "start.sh" ]