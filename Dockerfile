ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
RUN pip install --upgrade pip

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libjpeg-dev \
    libcairo2 \
    gcc \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    libxml2-dev \
    libxslt-dev \
    make \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up code directory
RUN mkdir -p /code
WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt /tmp/requirements.txt

# Modify requirements to use a pre-compiled version of PyMuPDF
RUN sed -i 's/PyMuPDF==1.22.3/pymupdf-binary==1.22.3/g' /tmp/requirements.txt

# Install dependencies
RUN pip install -r /tmp/requirements.txt
RUN pip install gunicorn whitenoise

# Copy project code
COPY ./src /code

# Create startup script
RUN printf "#!/bin/bash\n" > ./start.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./start.sh && \
    printf "python manage.py collectstatic --noinput\n" >> ./start.sh && \
    printf "python manage.py migrate --no-input\n" >> ./start.sh && \
    printf "gunicorn core.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./start.sh

RUN chmod +x start.sh

# Clean up
RUN apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ./start.sh