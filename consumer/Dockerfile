FROM python:3.7

COPY requirements.txt /

RUN pip install -r requirements.txt

COPY main.py /

CMD [ "python3.7", "-u", "main.py" ]

