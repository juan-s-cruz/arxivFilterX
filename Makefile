# Makefile targets to build the container and mount the current directory

IMAGE_NAME = "arxiv_filter"
CONTAINER_NAME = "arxiv_filter"

build:
	@docker build -f Dockerfile -t $(IMAGE_NAME) .

run_bash:
	@docker run -it --rm --name $(CONTAINER_NAME) --env-file .env -v $(PWD):/app $(IMAGE_NAME) bash

run_server:
	@docker run -it --rm --name $(CONTAINER_NAME) --env-file .env -p 127.0.0.1:8000:8000 -v $(PWD):/app $(IMAGE_NAME) sh -c 'python manage.py runserver 0.0.0.0:8000'

run_jupyter:
	@docker run -it --rm --name $(CONTAINER_NAME) --env-file .env -p 127.0.0.1:8888:8000 -v $(PWD):/app $(IMAGE_NAME) sh -c 'jupyter notebook --ip=0.0.0.0 --port=8000 --allow-root'