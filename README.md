# DCPCR
DCPCR: Deep Compressed Point Cloud Registration in Large-Scale Outdoor Environments
This work has been tested on Ubuntu using RTX 3060 GPU.
## How to get started (with docker)

Install nvida-docker.

## Data

You can download the compressed apollo dataset from [here](https://www.ipb.uni-bonn.de/html/projects/dcpcr/apollo-compressed.zip) and link the dataset to the docker container by configuring the Makefile `/dcpcr/Makefile`

```sh
DATA=<path-to-your-data>
```

For visualization and finetuning on the uncompressed data, you first have to download the apollo data and use the script '/dcpcr/scripts/apollo_aggregation.py' to compute the dense point clouds. This requires around 500 GB, see compression is nice ;)
You can also visualize the registration on the compressed data, but it's hard to see stuff, due to the low resolution.

## Building the docker container

For building the Docker Container simply run

```sh
make build
```

in the root directory.

## Running the Code

The first step is to run the docker container inside `dcpcr/`:

```sh
make run
```
In case running docker container results in the following error (due to --gpu flag):
**docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]].**
A solution to that can be found [here](https://askubuntu.com/questions/1400476/docker-error-response-from-daemon-could-not-select-device-driver-with-capab).

The following commands assume to be run inside the docker container.

### Training

For training a network we first have to create the config file with all the parameters.
An example of this can be found in `/dcpcr/config/config.yaml`.
To train the network simply run

```sh
python3 trainer -c <path-to-your-config>
```

### Evaluation

Evaluating the network on the test set can be done by:

```sh
python3 test.py -ckpt <path-to-your-checkpoint>
```

All results will be saved in a dictonary in the `dcpcr/experiments`. When finetuning with the compressed data we used `-dt 1`, while `-dt 5` for the uncompressed.

### Qualitative results

In `dcpcr/scripts/qualitative` are some scripts to visualize the results.

### Pretrained models

The pretrained weights of our models can be found [here](https://www.ipb.uni-bonn.de/html/projects/dcpcr/model_paper.ckpt)

## How to get started (without Docker)

### Installation

A list of all dependencies and install instructions can be derived from the Dockerfile.
Use `pip3 install -e .` to install dcpcr.

### Running the code

The scripts can be run as before inside the docker container. Only the `dcpcr/config/data_config.yaml` might need to be updated.

## Inference on other pointcloud data

To test the model on data other that Apollo. You can run the following scripts.

If the data is in `.pcd` format:
```sh
python inference.py -ckpt [path_to_checkpoint] [optional] -ft False
```
If the data is in `.las` format:
```sh
python las_inference.py -ckpt [path_to_checkpoint] [optional] -ft False
```
We recommand to use the pretrained [model](https://www.ipb.uni-bonn.de/html/projects/dcpcr/model_paper.ckpt) for inference.

Inference script can not be fully run inside a docker container (because of open3d visualization). If you would like to visualize the registration results these scripts should be outside of the docker container.

## Pointcloud similarity (building classification)
`pointcloud_similarity.py` script is responsible for the building classification task. It relies on the DCPCR and GICP to perform this task. More details on how to run the code can be found [here](https://github.com/Symmetry-Dimensions-Inc/Registration_Neural_Network/tree/Feature/Pointcloud_similarity)