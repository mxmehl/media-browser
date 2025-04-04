FROM python:3.13-alpine

ENV PATH="$PATH:/root/.local/bin"
EXPOSE 8000

RUN apk --no-cache add uwsgi-python3

# Install required Python packages
RUN pip install --no-cache-dir pipx && \
    pipx install --global poetry && \
    pipx ensurepath

# Create a group and user
RUN addgroup -S app && adduser -S app -G app

COPY . /app
WORKDIR /app
RUN chown -R app:app /app
USER app

RUN poetry config virtualenvs.in-project true && \
    poetry install --only main

# RUN poetry run home-stream -c config.yaml --host 0.0.0.0

# docker run --rm -it -p 8000:8000 home-stream:latest sh
