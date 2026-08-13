FROM python:3.14-slim


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install  --upgrade -r /code/requirements.txt


COPY . /code


CMD ["fastapi", "run", "app/main.py", "--port", "80"]