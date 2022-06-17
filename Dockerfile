# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /dt-utils   
COPY . .
#COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
ENV FLASK_APP=dt_utils.py 
ENV DT_TOKEN=${DT_TOKEN}

# COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
#CMD ["./dt_utils.sh","--host=0.0.0.0"]


