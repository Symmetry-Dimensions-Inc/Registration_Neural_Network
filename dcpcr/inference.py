import open3d as o3d
import laspy as lp
import click
from os.path import join, dirname, abspath
import numpy as np
import torch
import dcpcr.models.models as models
from dcpcr.utils.utils import extractPc, transform, normalizePc
from dcpcr.utils import fine_tuner

@click.command()
# Add your options here
@click.option('--checkpoint',
              '-ckpt',
              type=str,
              help='path to checkpoint file (.ckpt) to resume training.')
@click.option('--fine_tune',
              '-ft',
              type=bool,
              help='Whether to fine tune with icp or not.',
              default=True)
@click.option('--voxel_size',
              '-vs',
              type=float,
              help='voxel size for downsampling.',
              default=0.05)

def main(checkpoint, fine_tune, voxel_size):
    cfg = torch.load(checkpoint)['hyper_parameters']
    cfg['checkpoint'] = checkpoint

    source = o3d.io.read_point_cloud("./pcds/cloud_bin_0.pcd")
    #R = source.get_rotation_matrix_from_xyz((0, 0, 0.3 * np.pi))
    #source = source.rotate(R, center=(0,0,0))
    target = o3d.io.read_point_cloud("./pcds/cloud_bin_1.pcd")
    # Downsample
    downpcd_source = source.voxel_down_sample(voxel_size=voxel_size)
    downpcd_target = target.voxel_down_sample(voxel_size=voxel_size)
    
    data_source, xyz_source, clr_source = extractPc(downpcd_source, normalize=True)
    data_target, xyz_target, clr_target = extractPc(downpcd_target, normalize=True)

    # Visualize
    pcd_source = o3d.geometry.PointCloud()
    pcd_source.points = o3d.utility.Vector3dVector(xyz_source)
    pcd_source.paint_uniform_color(np.array([0, 1, 0]))

    pcd_target = o3d.geometry.PointCloud()
    pcd_target.points = o3d.utility.Vector3dVector(xyz_target)
    pcd_target.paint_uniform_color(np.array([1, 0, 0]))

    xyz_source  = torch.tensor(data_source, device=0).float()
    xyz_target  = torch.tensor(data_target, device=0).float()

    model = models.DCPCR.load_from_checkpoint(
        checkpoint).to(torch.device("cuda"))
    
    model = model.eval()
    with torch.no_grad():
        est_pose, _, _, _ = model(xyz_target, xyz_source)

    if fine_tune:
        init_guess = est_pose.detach().cpu().squeeze().numpy()
        est_pose = fine_tuner.refine_registration(  pcd_source,
                                                pcd_target,
                                                init_guess,
                                                distance_threshold=1/40)
        est_pose = torch.tensor(
                est_pose, device=0, dtype=torch.float)

    ps_t = transform(xyz_source, est_pose, device=0)
    ps_t = ps_t.cpu().detach().numpy()

    pcd_result = o3d.geometry.PointCloud()
    pcd_result.points = o3d.utility.Vector3dVector(ps_t[:, :3])
    pcd_result.paint_uniform_color(np.array([0, 0, 1]))
    #pcd_result.colors = o3d.utility.Vector3dVector(clr_target)

    o3d.visualization.draw_geometries([pcd_target, pcd_result, pcd_source])
if __name__ == "__main__":
    main()