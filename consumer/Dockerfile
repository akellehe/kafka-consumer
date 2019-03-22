FROM python:3

COPY main.py /
COPY requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python3.6", "-u", "main.py" ]

