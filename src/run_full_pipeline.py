from services.acquisition import Scan_3D 
from reconstruction.mesh_speed import reconstruct_3d_mesh
from  reconstruction.build3d import Build_3D_Cloud 
from reconstruction.utils import RGB_FILTRE ,HSV_FILTRE
from uploadstl.upload_stl import upload_stl_to_supabase
import os
import logging

def workflow():
    
    logger = logging.getLogger(__name__)
    # 1. Acquisition & Build : génère 3d_object.xyz et 3d_object.stl bruts
    AcquDirectory,csvFile= Scan_3D(logger=logger)
    # 2. Construction du nuage de points 3D
    working_directory = os.path.dirname(os.path.abspath(__name__))
    #extract the last directory from scan directory
    signature= os.path.basename(AcquDirectory)
    absolute_path_export_file = os.path.join(working_directory,f"{signature}.xyz")
    ## a changer plus tard ///////////
    rgb_filter=  RGB_FILTRE
    # a changer plus tard ////////////
    hsv_filter= HSV_FILTRE
    Build_3D_Cloud(AcquDirectory, absolute_path_export_file, 
                   rgb_filter=rgb_filter, hsv_filter=hsv_filter, logger=logger)

    # 3. Mesh Creation STL (mesh amélioré)
    config = {
        'voxel_size': 0.0004,
        'nb_neighbors': 15,
        'std_ratio': 1.5,
        'normal_knn': 15,
        'poisson_depth': 12,
        'density_threshold': 0.15,
        'smooth_iterations': 5
    }
    #absolutepath_stl_file = os.path.join(working_directory,f"{signature}.stl")
    #mesh = reconstruct_3d_mesh(absolute_path_export_file, absolutepath_stl_file, config)
    # changer le workflow car le mesh est tres Couteux au CPU cause crash
    # 4. Upload vers Supabase
    if True and os.path.exists(absolute_path_export_file):
        upload_stl_to_supabase(absolute_path_export_file)

if __name__ == "__main__":
    workflow()
