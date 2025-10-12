FROM python:3.13-alpine

WORKDIR /app

COPY src/ requirements.txt /app/
RUN pip install -r requirements.txt --no-cache-dir

RUN mkdir /data

EXPOSE 8000

ENV PELIT_CONFIG "/config/pelit.toml"

CMD [ "gunicorn", "--config", "/config/gunicorn.conf.py", "wsgi:app" ]
