FROM python:3.7-slim
ADD . /app
WORKDIR /app

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

RUN pip install -r requirements.txt
EXPOSE 80

CMD flask run