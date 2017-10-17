FROM python:2
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /code
ENTRYPOINT ["python", "xss.py"]