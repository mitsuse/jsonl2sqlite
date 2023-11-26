FROM python:3.12.0

ARG PIP_VERSION=23.2.1
ARG POETRY_VERSION=1.7.1

RUN pip3 install -U pip==${PIP_VERSION}
RUN pip3 install poetry==${POETRY_VERSION}

WORKDIR /app
COPY . /app
RUN poetry install

CMD ["python3", "--version"]
