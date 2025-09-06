# Makefile targets to build the container and mount the current directory

IMAGE_NAME = "arxiv_filter"
CONTAINER_NAME = "arxiv_filter"
SERVING_PORT = 8000
PWD = $(shell pwd)
LOCAL_MODEL_PATH =$(shell cat .env | grep LOCAL_MODEL_PATH | cut -d= -f2)

build:
	@docker build -f Dockerfile -t $(IMAGE_NAME) .

build-no-cache:
	@docker build --no-cache -f Dockerfile -t $(IMAGE_NAME) .

run_bash:
	@docker run -it --rm --name $(CONTAINER_NAME) --env-file .env --runtime=nvidia --gpus all -v $(PWD):/app -v $(LOCAL_MODEL_PATH):/app/llm_search/models $(IMAGE_NAME) bash

run_server:
	@docker run -it --rm --name $(CONTAINER_NAME) --env-file .env -p 127.0.0.1:$(SERVING_PORT):$(SERVING_PORT) --runtime=nvidia --gpus all -v $(PWD):/app -v $(LOCAL_MODEL_PATH):/app/llm_search/models $(IMAGE_NAME) sh -c 'python manage.py runserver 0.0.0.0:$(SERVING_PORT)'

run_jupyter:
	@docker run -it --rm --name $(CONTAINER_NAME) --env-file .env -p $(SERVING_PORT):$(SERVING_PORT) --runtime=nvidia --gpus all -v $(PWD):/app -v $(LOCAL_MODEL_PATH):/app/llm_search/models $(IMAGE_NAME) sh -c 'jupyter notebook --ip=0.0.0.0 --port=$(SERVING_PORT) --allow-root --no-browser --NotebookApp.token="" --NotebookApp.password=""'

clean:
	@rm -rf .venv;
	@find . -type d -name "__pycache__" -exec rm -rf {} +;

install_python_env:
	python3 -m venv .venv
	source .venv/bin/activate; pip install --upgrade pip; pip install --no-cache-dir -r requirements.txt