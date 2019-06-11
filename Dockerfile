FROM python:3.7-alpine

# Create a user
RUN adduser -D quart
# Set working directory for the purpose of this Dockerfile
WORKDIR /home/quart

# Copy requirements to the app root
COPY requirements.txt /tmp
# Create a virtual environment and install the dependecies
RUN python3 -m venv venv && \
  venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt --upgrade && \
  chown -R quart:quart ./

# Copy the app into our user root
COPY app /home/quart/app
COPY start.sh /home/quart
# Make our entrypoint executable
RUN chmod +x boot.sh

# Set the user
USER quart
# Set the entrypoint
ENTRYPOINT ["sh", "./boot.sh"]