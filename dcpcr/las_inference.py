import open3d as o3d
import laspy as lp
import click
from os.path import join, dirname, abspath
import numpy as np
import torch
import dcpcr.models.models as models
from dcpcr.utils.utils import extractPc, transform, normalizePc, scaledLas
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
              default=0.01)

def main(checkpoint, fine_tune, voxel_size):
    # Check device
    if torch.cuda.is_available(): 
        dev = "cuda:0" 
    else: 
        dev = "cpu"

    cfg = torch.load(checkpoint)['hyper_parameters']
    cfg['checkpoint'] = checkpoint
    
    laz_source = lp.read("/mnt/ssd1n1/Similarity/Data/Point_clouds/GREEN/building_0_points.las")
    laz_target = lp.read("/mnt/ssd1n1/Similarity/Data/LOD2/GREEN/Point_clouds/building_0.las")

    source_scale = scaledLas(laz_source)
    points_source = np.vstack([laz_source.X, laz_source.Y, laz_source.Z]).transpose().astype(np.float32)
    points_source = normalizePc(points_source)
    colors_source = np.vstack([laz_source.red, laz_source.green, laz_source.blue]).transpose()
    
    target_scale = scaledLas(laz_target)
    points_target = np.vstack([laz_target.X, laz_target.Y, laz_target.Z]).transpose().astype(np.float32)
    points_target = normalizePc(points_target)
    colors_target = np.vstack([laz_target.red, laz_target.green, laz_target.blue]).transpose()
    # Check whether source and target have the same scale
    if source_scale >= target_scale:
        points_source /= (source_scale/target_scale)
    else:
        points_target /= (target_scale/source_scale)

    geom_target = o3d.geometry.PointCloud()
    geom_target.points = o3d.utility.Vector3dVector(points_target)
    geom_target.colors = o3d.utility.Vector3dVector(colors_target)

    geom_source = o3d.geometry.PointCloud()
    geom_source.points = o3d.utility.Vector3dVector(points_source)
    geom_source.colors = o3d.utility.Vector3dVector(colors_source)
    # Downsample
    geom_source= geom_source.voxel_down_sample(voxel_size=voxel_size)
    geom_target = geom_target.voxel_down_sample(voxel_size=voxel_size)

    data_source, xyz_source, clr_source = extractPc(geom_source, normalize=False)   
    data_target, xyz_target, clr_target = extractPc(geom_target, normalize=False)
    
    data_source  = torch.tensor(data_source, device=dev).float()
    data_target  = torch.tensor(data_target, device=dev).float()

    model = models.DCPCR.load_from_checkpoint(
        checkpoint).to(dev)
    
    model = model.eval()
    with torch.no_grad():
        est_pose, _, _, _ = model(data_target, data_source)
    
    if fine_tune:
        init_guess = est_pose.detach().cpu().squeeze().numpy()
        est_pose = fine_tuner.refine_registration(  geom_source,
                                                geom_target,
                                                init_guess,
                                                distance_threshold=voxel_size*5)
        est_pose = torch.tensor(
                est_pose, device=dev, dtype=torch.float)

    ps_t = transform(data_source, est_pose, device=dev)
    ps_t = ps_t.cpu().detach().numpy()

    pcd_result = o3d.geometry.PointCloud()
    pcd_result.points = o3d.utility.Vector3dVector(ps_t[:, :3])
    pcd_result.paint_uniform_color(np.array([0, 0, 1]))

    vis_source = o3d.geometry.PointCloud()
    vis_source.points = geom_source.points
    vis_source.paint_uniform_color(np.array([1, 0, 0]))

    vis_target = o3d.geometry.PointCloud()
    vis_target.points = geom_target.points
    vis_target.paint_uniform_color(np.array([0, 1, 0]))
    
    o3d.visualization.draw_geometries([vis_target, vis_source, pcd_result])
if __name__ == "__main__":
    main()