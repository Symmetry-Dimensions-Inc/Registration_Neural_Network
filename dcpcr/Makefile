IMAGE_NAME=dcpcr
TAG=latest
CODE= $(shell pwd)

USER_ID= $(shell id -u)
GROUP_ID= $(shell id -g)
# CONFIG:=$(shell realpath ${CONFIG})
DATA=/home/ghailen/work/data/apollo-compressed# To be changed according to your own path
AGGREGATED=path/to/your/data/apollo-aggregated# To be changed if you would like to work on aggragated dataset
COMMAND="python3 train.py -dc config/data_config.yaml -c ${CONFIG}"
run:
	docker run --ipc=host --rm --gpus all -p 8888:8888 --user $(USER_ID):$(GROUP_ID) -it -v $(shell pwd)/../:/user/dev:rw -v ${DATA}:/data/apollo-compressed -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY -e  CUDA_VISIBLE_DEVICES -e NVIDIA_DRIVER_CAPABILITIES=all $(IMAGE_NAME) 
train:
	@echo config: ${CONFIG}
	@docker run --ipc=host --rm --gpus all -v $(shell pwd)/../:/user/dev:rw -e CUDA_VISIBLE_DEVICES -v ${DATA}:/data/apollo-compressed $(IMAGE_NAME) bash -c ${COMMAND}
execute:
	@echo execute: ${EXEC}
	@docker run --ipc=host --rm --gpus all -v $(shell pwd)/../:/user/dev:rw -e CUDA_VISIBLE_DEVICES -v ${DATA}:/data/apollo-compressed $(IMAGE_NAME) bash -c "${EXEC}" 

clean:
	@echo Removing docker image...
	-docker image rm --force $(IMAGE_NAME):$(TAG)
