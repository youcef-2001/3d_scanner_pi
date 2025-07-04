from utils import *
import os
import cv2
import numpy as np
import open3d as o3d


if __name__ == "__main__":
    # === Vérifier si le dossier existe ===
    if not os.path.exists(IMAGE_FOLDER):
        print(f"❌ Le dossier {IMAGE_FOLDER} n'existe pas.")
        exit(1)

        # === Lister les fichiers d'image dans le dossier ===
    image_files = sorted([
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
    ])

    i = 0
    coords_per_image = []
    degree =0
    """ les coords de la camera fixe seront prochainement en fonction
    de la profondeur  , hauteur et angle de capture par rapport au 
    centre de rotation"""
    
    camera_coords = get_camera_coordinates(degree)
    
    
    ''' notre plateforme tourne a 4 rotation par minute
    # donc 15 secondes pour une rotation complete
    # ayant 15.2 FPS
    # donc 13.6 secondes * 15.2 FPS =  207.2 images
    # donc 234 images pour une rotation de 360°'''
    while  i < len(image_files):
        image_path = image_files[i]
        # Calculer le degré de rotation pour chaque image
        # Supposons 234 images pour une rotation complète de 360°
        degree = (i * 360) / 224# 223 images etablie lors des test =/= 234 images
        # === Lire l'image ===
        frame = cv2.imread(image_path)
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        if frame is None:
            print(f"❌ Impossible de lire l'image {image_path}.")
            i += 1
            continue
        # === Appliquer le filtre HSV ===
        hsv_result = apply_filter(frame, 'HSV', *HSV_FILTRE)
        # === Appliquer le filtre RGB ===
        rgb_result = apply_filter(hsv_result, 'RGB', *RGB_FILTRE)
        print(f"✅ Image {image_path} traitée avec succès.")
        coords_per_pixel = []
        # taille de l'image
        height, width = frame.shape[:2]
        # les (x,y) des pixels non noirs
        ys, xs = np.where(np.any(rgb_result != [0, 0, 0], axis=-1))
        myzip = list(zip(xs, ys))  # Liste des pixel de l'image courante
        if myzip.__len__ == 0:
            print(f"❌ Aucune coordonnée valide trouvée dans l'image {image_path}.")
            continue
        else:    
            for x,y in myzip :
                        x,y,z= camerapoint_to_centerpoint(camera_coords,x,y,width, height,degree)
                        coords_per_pixel.append((x, y, z))
            coords_per_image.append(coords_per_pixel)
            
        i += 1
        
    #Rotation Totale , translation totale

    
    # sauvegarder dans un fichier xyz pour visualiser avec open3d
    xyz_file_path = os.path.join('./', "3d_object.xyz")
    with open(xyz_file_path, 'w') as xyz_file:
        for img_coords in coords_per_image:
            for coord in img_coords:
                xyz_file.write(f"{coord[0]} {coord[1]} {coord[2]}\n")
                
    ## add normals  in the point cloud 
    
    
    
    print(f"✅ Fichier XYZ créé avec succès : {xyz_file_path}")
    
    # cree un fichier STL
    
 

    # 1. Charger le nuage de points depuis un fichier .xyz
    pcd = o3d.io.read_point_cloud("./3d_object.xyz", format='xyz')

    # 2. (Optionnel) Downsampling et nettoyage
    pcd = pcd.voxel_down_sample(voxel_size=0.0045)
    pcd.remove_statistical_outlier(nb_neighbors=10, std_ratio=2.2)

    # 3. Estimer les normales pour la reconstruction
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=10))
    pcd.orient_normals_consistent_tangent_plane(k=8)

    # 4. Reconstruction du mesh avec Poisson
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=10)

    # 5. Découper le mesh aux limites du nuage de points
    bbox = pcd.get_axis_aligned_bounding_box()
    mesh = mesh.crop(bbox)
    mesh.compute_vertex_normals()
    # 6. Exporter au format STL (⚠️: STL ne gère pas la couleur ou texture)
    o3d.io.write_triangle_mesh("./3d_object.stl", mesh)

    print("✅ Mesh STL exporté avec succès !")

        
        

