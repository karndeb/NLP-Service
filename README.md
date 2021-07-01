# NLP As A Service

![NLP As A Service Demo](demo/animation.gif)

This project is a sample demo of NLP as a service platform built using FastAPI and Hugging Face.
The use cases are related to chatbot automation services


## Features

- Next Query Recommendation
- Query Expansion
- Fallback Reduction

## Requirement

See requirements.txt.

## Installation & Usage

```bash
$ git clone https://github.com/karndeb/NLP-Service.git
# change the directory
$ cd NLP-Service
# install packages
$ pip install -r requirements.txt
# start the server
$ uvicorn app.main:app --reload --port 8000
```

