FROM python:3.9

# Install packages
RUN mkdir -p /var/app/
COPY requirements.txt /var/app/
RUN pip install -r /var/app/requirements.txt

# Add the script and supporting files
COPY . /var/app/

# Set the working directory
WORKDIR /var/app/

# Run script
ENTRYPOINT [ "python", "main.py" ]