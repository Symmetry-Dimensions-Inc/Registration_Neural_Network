import open3d as o3d
import click
from os.path import join, dirname, abspath
import numpy as np
import torch
import dcpcr.models.models as models

@click.command()
# Add your options here
@click.option('--data_config',
              '-dc',
              type=str,
              help='path to the config file (.yaml) for the dataloader',
              default=join(dirname(abspath(__file__)), 'config/data_config.yaml'))
@click.option('--checkpoint',
              '-ckpt',
              type=str,
              help='path to checkpoint file (.ckpt) to resume training.')
@click.option('--fine_tune',
              '-ft',
              type=bool,
              help='Whether to fine tune with icp or not.',
              default=True)
@click.option('--distance_threshold',
              '-dt',
              type=float,
              help='icp robust kernel distance threshold',
              default=1)
@click.option('--compressed',
              '-c',
              type=bool,
              help='Whether to fine tune on compressed or input data',
              default=True)


def main(checkpoint, data_config, fine_tune, distance_threshold, compressed):

    def normalize_pc(points):
        centroid = np.mean(points, axis=0)
        points -= centroid
        furthest_distance = np.max(np.sqrt(np.sum(abs(points)**2,axis=-1)))
        points /= furthest_distance

        return points
    cfg = torch.load(checkpoint)['hyper_parameters']
    cfg['checkpoint'] = checkpoint

    #data = np.load("/data/apollo-compressed/TrainData/ColumbiaPark/2018-10-03/submaps/019417.npy")
    source = o3d.io.read_point_cloud("./pcds/cloud_bin_0.pcd")
    target = o3d.io.read_point_cloud("./pcds/cloud_bin_1.pcd")
    # Downsample
    downpcd_source = source .voxel_down_sample(voxel_size=0.05)
    downpcd_target = target.voxel_down_sample(voxel_size=0.05)

    length = min(len(downpcd_target.points), len(downpcd_source.points))
    # Extract the xyz points from source
    xyz_source = np.asarray(downpcd_source.points)
    clr_source = np.asarray(downpcd_source.colors)
    # Normalize
    xyz_source = normalize_pc(xyz_source)
    data_source = np.zeros((1,length, 6))

    data_source[0,:,:3] = xyz_source[:length,:]
    data_source[0,:,3:6] = clr_source[:length,:]
    
    # Extract the xyz points from target
    xyz_target = np.asarray(downpcd_target.points)
    clr_target = np.asarray(downpcd_target.colors)
    # Normalize
    xyz_target = normalize_pc(xyz_target)

    data_target = np.zeros((1,length, 6))

    data_target[0,:,:3] = xyz_target[:length,:]
    data_target[0,:,3:6] = clr_target[:length,:]

    # Prepare result
    result = np.ones((length, 4))
    result[:,:3] = data_target[0,:,:3]

    # Visualize
    pcd_source = o3d.geometry.PointCloud()
    pcd_source.points = o3d.utility.Vector3dVector(xyz_source)
    pcd_source.colors = o3d.utility.Vector3dVector(clr_source)

    pcd_target = o3d.geometry.PointCloud()
    pcd_target.points = o3d.utility.Vector3dVector(xyz_target)
    pcd_target.colors = o3d.utility.Vector3dVector(clr_target)

    xyz_source  = torch.tensor(data_source, device=0).float()
    xyz_target  = torch.tensor(data_target, device=0).float()

    model = models.DCPCR.load_from_checkpoint(
        checkpoint).to(torch.device("cuda"))
    
    model.eval()
    est_pose, w, target_corr, weights = model(xyz_target, xyz_source)
    
    # transform
    est_pose = (est_pose.cpu()).detach().numpy()
    result = np.matmul(result, est_pose)
    print(est_pose)
    pcd_result = o3d.geometry.PointCloud()
    pcd_result.points = o3d.utility.Vector3dVector(result[0, :, :3])
    pcd_result.colors = o3d.utility.Vector3dVector(clr_target)
    #print(est_pose)
    o3d.visualization.draw_geometries([pcd_target, pcd_source, pcd_result])
if __name__ == "__main__":
    main()