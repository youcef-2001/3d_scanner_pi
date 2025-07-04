import open3d as o3d
import numpy as np
import time

def reconstruct_3d_mesh(input_file, output_file, config=None):
    """
    Reconstruction 3D améliorée avec paramètres configurables
    
    Args:
        input_file: Chemin vers le fichier XYZ
        output_file: Chemin de sortie STL
        config: Dictionnaire des paramètres (optionnel)
    """
    
    # Configuration par défaut
    default_config = {
        'voxel_size': 0.005,
        'nb_neighbors': 10,
        'std_ratio': 2.0,
        'normal_knn': 20,
        'orient_knn': 9,
        'poisson_depth': 9,
        'density_threshold': 0.1,
        'smooth_iterations': 1
    }
    
    if config:
        default_config.update(config)
    cfg = default_config
    
    print("🔄 Début de la reconstruction 3D...")
    start_time = time.time()
    
    # 1. Chargement avec vérification
    print("📁 Chargement du nuage de points...")
    try:
        pcd = o3d.io.read_point_cloud(input_file, format='xyz')
        print(f"✅ {len(pcd.points)} points chargés")
    except Exception as e:
        print(f"❌ Erreur de chargement: {e}")
        return None
    
    if len(pcd.points) == 0:
        print("❌ Nuage de points vide !")
        return None
    
    # 2. Downsampling intelligent
    print("🔹 Downsampling...")
    original_count = len(pcd.points)
    pcd = pcd.voxel_down_sample(voxel_size=cfg['voxel_size'])
    print(f"📊 Points après downsampling: {len(pcd.points)} (réduction: {(1-len(pcd.points)/original_count)*100:.1f}%)")
    
    # 3. Nettoyage des outliers
    print("🧹 Nettoyage des outliers...")
    pcd_clean, ind = pcd.remove_statistical_outlier(
        nb_neighbors=cfg['nb_neighbors'], 
        std_ratio=cfg['std_ratio']
    )
    outliers_removed = len(pcd.points) - len(pcd_clean.points)
    print(f"🗑️  {outliers_removed} outliers supprimés")
    pcd = pcd_clean
    
    # 4. Estimation des normales
    print("🧭 Estimation des normales...")
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamKNN(knn=cfg['normal_knn'])
    )
    
    # 5. Orientation cohérente des normales
    print("↗️  Orientation des normales...")
    pcd.orient_normals_consistent_tangent_plane(k=cfg['orient_knn'])
    
    # 6. Reconstruction Poisson
    print("🏗️  Reconstruction du mesh (Poisson)...")
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=cfg['poisson_depth']
    )
    
    print(f"📐 Mesh créé: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
    
    # 7. Filtrage par densité (NOUVEAU!)
    print("🔍 Filtrage par densité...")
    densities = np.asarray(densities)
    density_threshold = np.quantile(densities, cfg['density_threshold'])
    
    # Garder seulement les triangles avec densité suffisante
    vertices_to_remove = densities < density_threshold
    mesh.remove_vertices_by_mask(vertices_to_remove)
    
    # 8. Découpage aux limites du nuage original (CORRIGÉ!)
    print("✂️  Découpage aux limites...")
    bbox = pcd.get_axis_aligned_bounding_box()
    mesh = mesh.crop(bbox)
    
    # 9. Lissage optionnel
    if cfg['smooth_iterations'] > 0:
        print(f"🪄 Lissage ({cfg['smooth_iterations']} itérations)...")
        mesh = mesh.filter_smooth_simple(number_of_iterations=cfg['smooth_iterations'])
    
    # 10. Calcul des normales du mesh
    print("🧮 Calcul des normales du mesh...")
    mesh.compute_vertex_normals()
    
    # 11. Validation du mesh
    print("🔍 Validation du mesh...")
    if not mesh.is_watertight():
        print("⚠️  Le mesh n'est pas étanche (watertight)")
    
    if not mesh.is_orientable():
        print("⚠️  Le mesh n'est pas orientable")
    
    # 12. Export avec gestion d'erreur
    print("💾 Export du mesh...")
    try:
        success = o3d.io.write_triangle_mesh(output_file, mesh)
        if success:
            print(f"✅ Mesh STL exporté: {output_file}")
        else:
            print("❌ Erreur lors de l'export")
            return None
    except Exception as e:
        print(f"❌ Erreur d'export: {e}")
        return None
    
    # 13. Statistiques finales
    total_time = time.time() - start_time
    print(f"\n📊 RÉSULTATS:")
    print(f"   ⏱️  Temps total: {total_time:.2f}s")
    print(f"   📍 Points finaux: {len(pcd.points)}")
    print(f"   🔺 Triangles: {len(mesh.triangles)}")
    print(f"   📦 Taille mesh: {len(mesh.vertices)} vertices")
    
    return mesh

if __name__ == "__main__":
    # Configuration personnalisable
    config = {
        'voxel_size': 0.0004,      # Plus petit = plus de détails
        'nb_neighbors': 15,       # Plus élevé = nettoyage plus strict
        'std_ratio': 1.5,         # Plus bas = nettoyage plus agressif
        'normal_knn': 15,         # Plus élevé = normales plus lisses
        'poisson_depth': 12,      # Plus élevé = plus de détails
        'density_threshold': 0.15, # Plus élevé = plus de filtrage
        'smooth_iterations': 5     # Lissage final
    }
    
    # Exécution
    mesh = reconstruct_3d_mesh("./3d_object.xyz", "./3d_object.stl", config)
    
    # Test de différentes configurations
    # configs = test_parameters()
    # mesh = reconstruct_3d_mesh("./3d_object.xyz", "./3d_object_hq.stl", configs['haute_qualité'])