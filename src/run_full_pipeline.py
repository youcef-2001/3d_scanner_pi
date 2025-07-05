from services.acquisition import Scan_3D 
from  reconstruction.build3d import Build_3D_Cloud 
from reconstruction.utils import RGB_FILTRE ,HSV_FILTRE
from uploadstl.upload_stl import upload_stl_to_supabase
from reconstruction.mesh_speed import reconstruct_3d_mesh
import os
import logging

def workflow(user_ID,distance,scan_status, token,rgb_filter=RGB_FILTRE, hsv_filter=HSV_FILTRE):
    
    logger = logging.getLogger(__name__)
    # 1. Acquisition & Build : génère 3d_object.xyz et 3d_object.stl bruts
    #modifier la valeur du pointer pour que la valeur change dans tout le programme 
    # et que l'on puisse suivre l'avancement du scan
    # et de la reconstruction 3D
    scan_status['step'] = 1
    
    AcquDirectory,csvFile,fps= Scan_3D(scan_status,logger=logger)
    # 2. Construction du nuage de points 3D
    working_directory = os.path.dirname(os.path.abspath(__name__))
    #extract the last directory from scan directory
    signature= os.path.basename(AcquDirectory)
    absolute_path_export_file = os.path.join(working_directory,f"{signature}.xyz")
    
    scan_status['step'] += 1  # Increment step for tracking progress
    Build_3D_Cloud(AcquDirectory, absolute_path_export_file, 
                   rgb_filter=rgb_filter, hsv_filter=hsv_filter,fps_on_acqu=fps,
                   distance =distance , logger=logger)

    # step additionnel test du mesh 
    config = {
        'voxel_size': 0.0004,      # Plus petit = plus de détails
        'nb_neighbors': 15,       # Plus élevé = nettoyage plus strict
        'std_ratio': 2.0,         # Plus bas = nettoyage plus agressif
        'normal_knn': 16,         # Plus élevé = normales plus lisses
        'poisson_depth': 10,      # Plus élevé = plus de détails
        'density_threshold': 0.15, # Plus élevé = plus de filtrage
        'smooth_iterations': 2     # Lissage final
    }
    scan_status['step'] += 1  # Increment step for tracking progress
    stl_absolute_path = absolute_path_export_file.replace('.xyz', '.stl')
    reconstruct_3d_mesh(absolute_path_export_file, 
                           stl_absolute_path, 
                           config=config, logger=logger)
    
    # 3. Upload vers Supabase
    scan_status['step'] += 1  # Increment step for tracking progress
    if True and os.path.exists(stl_absolute_path):
        upload_stl_to_supabase(stl_absolute_path,userid=user_ID,token=token)
        
    scan_status['step'] += 1  # Increment step for tracking progress

if __name__ == "__main__":
    #workflow(1) # Remplacez 1 par l'ID utilisateur approprié
    pass