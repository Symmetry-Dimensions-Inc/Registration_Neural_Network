# Point Cloud Similarity documentation
The goal of this work is to report similarities between a source and a target pointcloud of a building with high accuracy. Using this building similarity we aim to be able to classify the {Source, Target} set into one of these 4 categories:
1. Modified
2. Reconstructed
3. Newly constructed
4. Destructed
To do that, we will be using `pointcloud_similarity.py`. In this document we will be explaining the details about our script.

## How it works
Step 1:
1. The scipts takes as input a set of source (scans) and target LOD2 pointclouds.
2. For each {Source, Target} we perform a preprocessing phase which includes: normalization and subsampling using voxelization.
3. For each {Source, Target} we perform parallarily GICP and [DCPCR](https://drive.google.com/file/d/1ka5awEEzqkGs9xQQ6SJW3ZFWdNAWJyWu/view) + GICP combined together.
4. For each technique mentioned in step 4, we calculate the source to target similarity. The similarity is the ratio (%) of points from the source that are within a threshold euclidean distance from points from the target pointcloud.
5. We get the transformation matrix that results in higher similarity between the two techniques in step 4
6. We classify the {Source, Target} set according:
* If the LOD2 doesn't exist = Category 3: Building is newly constructed
* If the source scan is empty (or too sparse) = Category 4: Building destructed
* If similarity ratio between source and target is above 50% = Category 1: Building modified
* If similarity ratio between source and target is below 50% = Category 1: Building reconstructed