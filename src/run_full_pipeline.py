from testAcquisition import main as acquisition_main
from mesh_speed import reconstruct_3d_mesh
from upload_stl import upload_stl_to_supabase
import os

def workflow():
    # 1. Acquisition & Build : génère 3d_object.xyz et 3d_object.stl bruts
    acquisition_main()  # ou build.main() selon ton organisation

    # 2. Mesh Creation STL (mesh amélioré)
    config = {
        'voxel_size': 0.0004,
        'nb_neighbors': 15,
        'std_ratio': 1.5,
        'normal_knn': 15,
        'poisson_depth': 12,
        'density_threshold': 0.15,
        'smooth_iterations': 5
    }
    xyz_file = "./3d_object.xyz"
    stl_file = "./3d_object_final.stl"
    mesh = reconstruct_3d_mesh(xyz_file, stl_file, config)

    # 3. Upload vers Supabase
    if mesh and os.path.exists(stl_file):
        upload_stl_to_supabase(stl_file)

if __name__ == "__main__":
    workflow()
