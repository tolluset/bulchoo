# Use a base image of python:3.13
FROM python:3.13

# Set the working directory
WORKDIR /app

# Copy the project files into the Docker image
COPY . .

# Install Poetry
RUN pip install poetry

# Install the dependencies using poetry
RUN poetry install

# Set the entry point to run the collector.py script
ENTRYPOINT ["poetry", "run", "python", "collector.py"]
