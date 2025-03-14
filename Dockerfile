# ARG PYTHON_VERSION=3.12-slim-bullseye
# FROM python:${PYTHON_VERSION}

# # Create a virtual environment
# RUN python -m venv /opt/venv
# ENV PATH=/opt/venv/bin:$PATH
# RUN pip install --upgrade pip

# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Install system dependencies for document processing
# RUN apt-get update && apt-get install -y \
#     libpq-dev \
#     libjpeg-dev \
#     libcairo2 \
#     gcc \
#     poppler-utils \
#     tesseract-ocr \
#     libmagic1 \
#     libxml2-dev \
#     libxslt-dev \
#     make \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Set up code directory
# RUN mkdir -p /code
# WORKDIR /code

# # Copy requirements and install dependencies
# COPY requirements.txt /tmp/requirements.txt

# # Modify requirements to use a pre-compiled version of PyMuPDF
# RUN sed -i 's/PyMuPDF==1.22.3/pymupdf-binary==1.22.3/g' /tmp/requirements.txt

# RUN apt-get update && apt-get install -y \
#     libgl1-mesa-glx \
#     libglib2.0-0

# # Install dependencies
# RUN pip install -r /tmp/requirements.txt
# RUN pip install gunicorn whitenoise

# # Copy project code
# COPY ./src /code

# # Create startup script
# RUN printf "#!/bin/bash\n" > ./start.sh && \
#     printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./start.sh && \
#     printf "python manage.py collectstatic --noinput\n" >> ./start.sh && \
#     printf "python manage.py migrate --no-input\n" >> ./start.sh && \
#     printf "gunicorn core.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./start.sh
    

# RUN chmod +x start.sh

# # Clean up
# RUN apt-get autoremove -y \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# CMD ./start.sh


ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION} as builder

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
RUN pip install --upgrade pip setuptools wheel

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
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /tmp/requirements.txt

# Modify requirements to use a pre-compiled version of PyMuPDF
RUN sed -i 's/PyMuPDF==1.22.3/pymupdf-binary==1.22.3/g' /tmp/requirements.txt

# Install dependencies
RUN pip install -r /tmp/requirements.txt
RUN pip install gunicorn whitenoise

# CRITICAL FIX: Force reinstall OpenAI package to ensure correct version
RUN pip uninstall -y openai && pip install openai==1.6.0

# Verify OpenAI version
RUN python -c "import openai; print(f'OpenAI version installed: {openai.__version__}')" 

# Final stage
FROM python:${PYTHON_VERSION}

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1
ENV HTTPX_PROXY=""
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    libcairo2 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set up code directory
WORKDIR /code

# Copy project code
COPY ./src /code

# Create and prepare log directory
RUN mkdir -p /var/log/app && chmod 777 /var/log/app

# Create startup script with OpenAI version verification
RUN printf "#!/bin/bash\n" > ./start.sh && \
    printf "set -e\n\n" >> ./start.sh && \
    printf "# Verify OpenAI version on startup\n" >> ./start.sh && \
    printf "python -c \"import openai; print('OpenAI version at runtime: ' + openai.__version__); assert openai.__version__.startswith('1.'), 'Wrong OpenAI version!'\"\n\n" >> ./start.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./start.sh && \
    printf "python manage.py collectstatic --noinput\n" >> ./start.sh && \
    printf "python manage.py migrate --no-input\n" >> ./start.sh && \
    printf "exec gunicorn core.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\" --workers 2 --timeout 120\n" >> ./start.sh

RUN chmod +x start.sh

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

CMD ["./start.sh"]