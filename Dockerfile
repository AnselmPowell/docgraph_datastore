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
    && rm -rf /var/lib/apt/lists/*

# Set up code directory
RUN mkdir -p /code
WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt /tmp/requirements.txt

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


########################################################






# # Dockerfile

# ARG PYTHON_VERSION=3.12-slim-bullseye
# FROM python:${PYTHON_VERSION}

# # Create a virtual environment
# RUN python -m venv /opt/venv
# ENV PATH=/opt/venv/bin:$PATH
# RUN pip install --upgrade pip

# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Install system dependencies - combining existing and new dependencies
# RUN apt-get update && apt-get install -y \
#     # Existing dependencies
#     libpq-dev \
#     libjpeg-dev \
#     libcairo2 \
#     gcc \
#     # New dependencies for document processing
#     poppler-utils \
#     tesseract-ocr \
#     libmagic1 \
#     libxml2-dev \
#     libxslt-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Rest of your existing setup
# RUN mkdir -p /code
# WORKDIR /code

# COPY requirements.txt /tmp/requirements.txt
# COPY ./src /code

# # Add the new Python packages to your requirements.txt:
# # python-magic-bin
# # unstructured[local-inference]

# RUN pip install -r /tmp/requirements.txt
# RUN pip install gunicorn

# ARG PROJ_NAME="core"

# # Your existing script creation
# RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
#     printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
#     printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
#     printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./paracord_runner.sh

# RUN chmod +x paracord_runner.sh

# # Clean up
# RUN apt-get remove --purge -y \
#     && apt-get autoremove -y \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# CMD ./paracord_runner.sh








#####################


# # Set the python version as a build-time argument
# # with Python 3.12 as the default
# ARG PYTHON_VERSION=3.12-slim-bullseye
# FROM python:${PYTHON_VERSION}

# # Create a virtual environment
# RUN python -m venv /opt/venv

# # Set the virtual environment as the current location
# ENV PATH=/opt/venv/bin:$PATH

# # Upgrade pip
# RUN pip install --upgrade pip

# # Set Python-related environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Install os dependencies for our mini vm
# RUN apt-get update && apt-get install -y \
#     # for postgres
#     libpq-dev \
#     # for Pillow
#     libjpeg-dev \
#     # for CairoSVG
#     libcairo2 \
#     # other
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# # Create the mini vm's code directory
# RUN mkdir -p /code

# # Set the working directory to that same code directory
# WORKDIR /code

# # Copy the requirements file into the container
# COPY requirements.txt /tmp/requirements.txt

# # copy the project code into the container's working directory
# COPY ./src /code

# # Install the Python project requirements
# RUN pip install -r /tmp/requirements.txt
# RUN pip install gunicorn

# # database isn't available during build
# # run any other commands that do not need the database
# # such as:
# # RUN python manage.py collectstatic --noinput

# # set the Django default project name
# ARG PROJ_NAME="core"

# # create a bash script to run the Django project
# # this script will execute at runtime when
# # the container starts and the database is available
# RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
#     printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
#     printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
#     printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./paracord_runner.sh

# # make the bash script executable
# RUN chmod +x paracord_runner.sh

# # Clean up apt cache to reduce image size
# RUN apt-get remove --purge -y \
#     && apt-get autoremove -y \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# # Run the Django project via the runtime script
# # when the container starts
# CMD ./paracord_runner.sh

