# Use the official Python 3.9 slim image
FROM python:3.9-slim

# Install apache2-utils for the apache bench (ab) tool
RUN apt-get update && \
    apt-get install -y --no-install-recommends apache2-utils && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /seed

# Copy the current directory contents into the container
COPY . .

# Run the Python script to create POST data files in a format compatible with ab
RUN python make-data.py

# Run the shell script to generate votes
CMD ["/bin/bash", "/seed/generate-votes.sh"]
