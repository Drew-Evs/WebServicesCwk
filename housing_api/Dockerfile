# a docker file to wrap the django project/python install and sqlite into a containor
# this should allow easy API boot

#official python language
FROM python:3.10-slim

#set environment - prevents pycahce files and stdout buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#working directory inside containor
WORKDIR /app

#copy and install req file
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

#copy django project to containor
COPY . /app/

#expose API port
EXPOSE 8000

#start Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]