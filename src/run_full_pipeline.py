from services.acquisition import Scan_3D 
from  reconstruction.build3d import Build_3D_Cloud 
from reconstruction.utils import RGB_FILTRE ,HSV_FILTRE
from uploadstl.upload_stl import upload_stl_to_supabase
import os
import logging

def workflow(user_ID,distance,scan_status):
    
    logger = logging.getLogger(__name__)
    # 1. Acquisition & Build : génère 3d_object.xyz et 3d_object.stl bruts
    #modifier la valeur du pointer pour que la valeur change dans tout le programme 
    # et que l'on puisse suivre l'avancement du scan
    # et de la reconstruction 3D
    scan_status['step'] = 1
    
    AcquDirectory,csvFile,fps= Scan_3D(logger=logger)
    # 2. Construction du nuage de points 3D
    working_directory = os.path.dirname(os.path.abspath(__name__))
    #extract the last directory from scan directory
    signature= os.path.basename(AcquDirectory)
    absolute_path_export_file = os.path.join(working_directory,f"{signature}.xyz")
    ## a changer plus tard ///////////
    rgb_filter=  RGB_FILTRE
    # a changer plus tard ////////////
    hsv_filter= HSV_FILTRE
    scan_status['step'] += 1  # Increment step for tracking progress
    Build_3D_Cloud(AcquDirectory, absolute_path_export_file, 
                   rgb_filter=rgb_filter, hsv_filter=hsv_filter,fps_on_acqu=fps,
                   distance =distance , logger=logger)

    # 3. Upload vers Supabase
    scan_status['step'] += 1  # Increment step for tracking progress
    if True and os.path.exists(absolute_path_export_file):
        upload_stl_to_supabase(absolute_path_export_file,userid=user_ID,token=token)
        
    scan_status['step'] += 1  # Increment step for tracking progress

if __name__ == "__main__":
    workflow(1) # Remplacez 1 par l'ID utilisateur approprié
