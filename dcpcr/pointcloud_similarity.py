import open3d as o3d
import laspy as lp
import click
from os import listdir
from os.path import join, dirname, abspath
import yaml
import numpy as np
import torch
import dcpcr.models.models as models
from dcpcr.utils.utils import extractPc, transform, normalizePc, scaledLas, storeCsv
from dcpcr.utils import fine_tuner

@click.command()
# Add your options here
@click.option('--config',
              '-c',
              type=str,
              help='path to the config file (.yaml)',
              default=join(dirname(abspath(__file__)), 'config/pointcloud_similarity.yaml'))
@click.option('--fine_tune',
              '-ft',
              type=bool,
              help='Whether to fine tune with icp or not.',
              default=True)
@click.option('--voxel_size',
              '-vs',
              type=float,
              help='voxel size for downsampling.',
              default=0.03)
@click.option('--similarity_ratio',
              '-sr',
              type=float,
              help='ratio to define the similarity between two buildings',
              default=50)
@click.option('--point_threshold',
              '-t',
              type=int,
              help='minimun number of points per scan under which the building is considerated as destructed',
              default=20)
@click.option('--visualize',
              '-vis',
              type=bool,
              help='Whether to visualize the aligned pointcloud.',
              default=False)
@click.option('--building',
              '-b',
              type=str,
              help='Define the ground truth green or blue.',
              default='blue') 
            
def main(config, fine_tune, voxel_size, similarity_ratio, point_threshold, visualize, building):
    # Check device
    if torch.cuda.is_available(): 
        dev = "cuda:0" 
    else: 
        dev = "cpu"
    path = yaml.safe_load(open(config))

    model = models.DCPCR.load_from_checkpoint(
        path['checkpoint']).to(dev)
    
    model = model.eval()

    dir_path = path['pcd_path'] + building.upper()

    ground_truth, predictions, building_id = [], [], []

    if building.upper() == "BLUE":
        gt = "Modified"
    elif building.upper() == "GREEN":
        gt = "Reconstructed"
    elif building.upper() == "YELLOW":
        gt = "Newly Constructed"
    else:
        gt = "Destructed"
    
    for i, file in enumerate(listdir(dir_path)):
        try:
            source_dir = path['pcd_path'] + building.upper() + "/" + file
            target_dir = path['lod2_path'] + building.upper() + "/Newpcd/"+ file
            laz_source = lp.read(source_dir)
            try:
                laz_target = lp.read(target_dir)
            except Exception:
                print("This is a newly constructed building!")
                predictions.append("Newly constructed")
                ground_truth.append(gt)
                building_id.append(file[:len(file)-4])
                continue

            source_scale = scaledLas(laz_source)
            points_source = np.vstack([laz_source.X, laz_source.Y, laz_source.Z]).transpose().astype(np.float32)
            points_source = normalizePc(points_source)
            
            target_scale = scaledLas(laz_target)
            points_target = np.vstack([laz_target.X, laz_target.Y, laz_target.Z]).transpose().astype(np.float32)
            points_target = normalizePc(points_target)
            
            try:
                colors_source = np.vstack([laz_source.red, laz_source.green, laz_source.blue]).transpose()
                colors_target = np.vstack([laz_target.red, laz_target.green, laz_target.blue]).transpose()
            except AttributeError:
                colors_source = np.zeros(points_source.shape)
                colors_target = np.zeros(points_target.shape)

            geom_target = o3d.geometry.PointCloud()
            geom_target.points = o3d.utility.Vector3dVector(points_target)
            geom_target.colors = o3d.utility.Vector3dVector(colors_target)

            geom_source = o3d.geometry.PointCloud()
            geom_source.points = o3d.utility.Vector3dVector(points_source)
            geom_source.colors = o3d.utility.Vector3dVector(colors_source)
            # Downsample
            geom_source= geom_source.voxel_down_sample(voxel_size=voxel_size)
            geom_target = geom_target.voxel_down_sample(voxel_size=voxel_size)
            geom_source, _ = geom_source.remove_radius_outlier(nb_points=5, radius=voxel_size*10)
            
            if (len(geom_source.points) < point_threshold):
                print("This is a destructed building!")
                predictions.append("Destructed")
                ground_truth.append(gt)
                building_id.append(file[:len(file)-4])
                pass
            
            source = o3d.geometry.PointCloud()
            source.points = geom_source.points
            source.colors = geom_source.colors                     
            # ICP only test
            init_guess = np.identity(4)
            result = fine_tuner.refine_registration(source,
                                                    geom_target,
                                                    init_guess,
                                                    distance_threshold=voxel_size*5)

            source.transform(result)
            dists = np.asarray(source.compute_point_cloud_distance(geom_target))
            
            ind = np.where(dists <= voxel_size)[0]
            similar_points = source.select_by_index(ind)
            icp_similarity = len(similar_points.points)


            data_source, xyz_source, clr_source = extractPc(geom_source, normalize=False)   
            data_target, xyz_target, clr_target = extractPc(geom_target, normalize=False)
            
            data_source  = torch.tensor(data_source, device=dev).float()
            data_target  = torch.tensor(data_target, device=dev).float()

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
            

            dists = np.asarray(pcd_result.compute_point_cloud_distance(geom_target))
            
            ind = np.where(dists <= voxel_size)[0]
            similar_points = pcd_result.select_by_index(ind)
            dcpcr_similarity = len(similar_points.points)

            ratio = (max(dcpcr_similarity, icp_similarity)/len(geom_source.points)) * 100
            
            if ratio >= similarity_ratio:
                print("This building is updated!")
                predictions.append("Modified")
            else:
                print("This is a reconstructed building!")
                predictions.append("Reconstructed")
                
            print("Similarity ratio is : ", "{:.2f}".format(ratio),"%")
            ground_truth.append(gt)
            building_id.append(file[:len(file)-4])
            if (visualize): 
                vis_source = o3d.geometry.PointCloud()
                vis_source.points = geom_source.points
                vis_source.paint_uniform_color(np.array([1, 0, 0]))

                vis_target = o3d.geometry.PointCloud()
                vis_target.points = geom_target.points
                vis_target.paint_uniform_color(np.array([0, 1, 0]))
                
                if dcpcr_similarity < icp_similarity:
                    pcd_result.points = source.points

                o3d.visualization.draw_geometries([vis_target, vis_source, pcd_result])
                
        except Exception:
            pass
            
    storeCsv(building_id, predictions, ground_truth, gt + '_results.xlsx')
   
if __name__ == "__main__":
    main()
