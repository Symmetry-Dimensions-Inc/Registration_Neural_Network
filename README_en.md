# DCPCR
DCPCR: Deep Compressed Point Cloud Registration in Large-Scale Outdoor Environments
This work has been tested on Ubuntu using RTX 3060 GPU.

## How to get started

### Installation

Use `pip3 install -e .` to install dcpcr. All the dependencies can be found inside `requirements.txt` file.

The script can be simply run. Only the `dcpcr/config/pointcloud_similarity.yaml` might need to be updated according to data and model path.

More information about our data can be found later.

## Running the Code

### Building classification

For building classification script, we first have to create the config file with all the parameters.
An example of this can be found in `/dcpcr/config/pointcloud_similarity.yaml`.
To run the script:

```sh
python pointcloud_similarity.py -c [path_to_configfile] [optional: add other flags]
```
More details about flags will be explained later.

### Qualitative results

`pointcloud_similarity.py` will automatically store results in CSV format. The results will be reported in the below order:

| Building ID | Prediction      | Ground Truth       |
### Pretrained models

The pretrained weights of our models can be found [here](https://www.ipb.uni-bonn.de/html/projects/dcpcr/model_paper.ckpt)

## Pointcloud similarity (building classification)
`pointcloud_similarity.py` script is responsible for the building classification task. It relies on the DCPCR and GICP to perform this task. More details on how to run the code can be found [in this link](./documentation/README.md)
