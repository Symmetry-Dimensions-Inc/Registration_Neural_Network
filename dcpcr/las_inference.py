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


def main(checkpoint, fine_tune):
    cfg = torch.load(checkpoint)['hyper_parameters']
    cfg['checkpoint'] = checkpoint
    laz_source = lp.read("./pcds/hotel.las")
    laz_target = lp.read("./pcds/hotel.las")

    scaledLas(laz_source)
    points_source = np.vstack([laz_source.X, laz_source.Y, laz_source.Z]).transpose().astype(np.float32)
    points_source = normalizePc(points_source)
    points_source[:,2] += 1.5
    colors_source = np.vstack([laz_source.red, laz_source.green, laz_source.blue]).transpose()/65535
    #colors_source = colors_source[::2,:]
    
    scaledLas(laz_target)
    points_target = np.vstack([laz_target.X, laz_target.Y, laz_target.Z]).transpose().astype(np.float32)
    points_target = normalizePc(points_target)
    colors_target = np.vstack([laz_target.red, laz_target.green, laz_target.blue]).transpose()/65535
    #colors_target = colors_target[1::2,:]

    geom_target = o3d.geometry.PointCloud()
    geom_target.points = o3d.utility.Vector3dVector(points_target)
    geom_target.colors = o3d.utility.Vector3dVector(colors_target)

    geom_source = o3d.geometry.PointCloud()
    geom_source.points = o3d.utility.Vector3dVector(points_source)
    geom_source.colors = o3d.utility.Vector3dVector(colors_source)
    #R = geom_source.get_rotation_matrix_from_xyz((0, 0, 0.2 * np.pi))
    #geom_source = geom_source.rotate(R, center=(0,0,0))
    # Downsample
    #geom_source= geom_source.voxel_down_sample(voxel_size=0.01)
    #geom_target = geom_target.voxel_down_sample(voxel_size=0.01)
    
    geom_source= geom_source.uniform_down_sample(500)
    geom_target = geom_target.uniform_down_sample(500)

    data_source, xyz_source, clr_source = extractPc(geom_source, normalize=False)   
    data_target, xyz_target, clr_target = extractPc(geom_target, normalize=False)
    print(xyz_source.shape, xyz_target.shape)

    data_source  = torch.tensor(data_source, device=0).float()
    data_target  = torch.tensor(data_target, device=0).float()

    model = models.DCPCR.load_from_checkpoint(
        checkpoint).to(torch.device("cuda"))
    
    model = model.eval()
    with torch.no_grad():
        est_pose, _, _, _ = model(data_target, data_source)
    
    if fine_tune:
        init_guess = est_pose.detach().cpu().squeeze().numpy()
        est_pose = fine_tuner.refine_registration(  geom_source,
                                                geom_target,
                                                init_guess,
                                                distance_threshold=1.0)
        est_pose = torch.tensor(
                est_pose, device=0, dtype=torch.float)

    print(est_pose)
    ps_t = transform(data_source, est_pose, device=0)
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