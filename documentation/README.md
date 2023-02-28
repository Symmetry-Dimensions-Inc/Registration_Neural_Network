# Point Cloud Similarity documentation
The goal of this work is to report similarities between a source and a target pointcloud of a building with high accuracy. Using this building similarity we aim to be able to classify the {Source, Target} set into one of these 4 categories:
1. Modified
2. Reconstructed
3. Newly constructed
4. Destructed

To do that, we will be using `pointcloud_similarity.py`. In this document we will be explaining the details about our script.

## How it works
Steps:
1. The scipts takes as input a set of source (scans) and target LOD2 pointclouds.
2. For each {Source, Target} we perform a preprocessing phase which includes: normalization and subsampling using voxelization.
3. For each {Source, Target} we perform parallarily GICP and [DCPCR](https://drive.google.com/file/d/1-91ym2ue35wtUK1WhG1rwxbdZrSa2Gow/view) + GICP combined together.
4. For each technique mentioned in step 3, we allign the source to target and we calculate the similarity. The similarity is the ratio (%) of points from the source that are within a threshold euclidean distance from points from the target pointcloud.
5. We get the transformation matrix that results in higher similarity between the two techniques in step 3
6. We classify the {Source, Target} set accordingly:
    * If the LOD2 doesn't exist = Category 3: Building is newly constructed
    * If the source scan is empty (or too sparse) = Category 4: Building destructed
    * If similarity ratio between source and target is above 50% = Category 1: Building modified
    * If similarity ratio between source and target is below 50% = Category 2: Building reconstructed

## How to run
The user has full control on the how to run the scripts using flags:
* `-c`: path to config yaml file (default: 'config/pointcloud_similarity.yaml')
* `-ft`: Whether to fine tune the dcpcr results with icp or not. (default=True)
* `-vs`: voxel size for pointcloud downsampling. (default=0.03)
* `-sr`: % ratio threshold to define the similarity between two buildings. (default=50)
* `-t`: minimun number of points per scan under which the building is considerated as destructed. (default=20)
* `-b`: Define the ground truth green, blue, red or yellow. (default='blue')
* `vis`: Whether to visualize the aligned pointcloud. (default=False)

Please update `config/pointcloud_similarity.yaml` with the correct paths:
* `checkpoint`: Path to [pretrained](https://www.ipb.uni-bonn.de/html/projects/dcpcr/model_paper.ckpt) checkpoint file (.ckpt)
* `lod2_path`: Path to LOD2 data folder
* `pcd_path`: Path to pointcloud data folder
To run the script, please copy the command bellow:
```
python pointcloud_similarity.py -c [path_to_configfile] [optional: add other flags]
```

## Results
We report results on our sendai private data. The source data represent scans taken for the building while the target is the pointcloud generated from LOD2. Data can be found [here](https://drive.google.com/drive/folders/1bphqSdg1_73WYpi0Pr1dDfn5TJdzIjM8).

Results
| Ground truth/Prediction | Modified       | Reconstructed       | Destructed      | Newly constructed       | Accuracy       |
|----------|-------------|-------------|-------------|-------------|-------------|
| Modified (16 scan)  | 11        | 4    | 1       | 0 | 68.75% |
| Reconstructed (39 scan) | 0         | 36     | 3         | 0 | 92.3% |
| Destructed  (65 scan) | 4       | 54   | 7        | 0 | 10.8% |
| Newly constructed (30 scan) | 0       | 0    | 0       | 30 | 100% |

### Results discussion
* For modified and reconstructed buildings, we notice that the quality of the pointcloud may be poor for a number of scans. These scans may be empty which explains the prediction of destructed category instead.
* It is very hard to differentiate between fully reconstructed and under reconstruction buildings.
* For destructed building, some constructions have already started when the scans were captured. For our algorithm, these constructions are enough to deceive the model to predict a reconstructed category instead.
* Our DCPCR currently works well for predicting initial pose guess. It can work better if we can include r,g,b colors for each point. (This requires also LOD2 to have colors as well)
* Currently GICP + DCPCR gives the best pose estimation. However, We need to explore what other ICP methods we can use in the future.

## Visualization
We can visualize the source to target alignment by setting `vis` flag to `True`. Visualization are done using open3d.
* Green points: target building pointcloud
* Red points: source captured scan
* Blue points: aligned source scan with the target building

Below is an example of a captured scan of a modified building (category 1)
![Project Image](../images/blue.png)