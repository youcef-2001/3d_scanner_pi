# script pour la reconstruction des fichiers 3D // premier test avec photo contenant le laser



# lire les photo 
# traitement d'images pour refaire sortir le laser 
# methodes de calcul pour associer des coordonness au points 
#On va estimer que toutes les photos ont ete prises a une distance moyenne de 15 cm

import os
import cv2
import numpy as np
import open3d as o3d

# === PARAMÈTRES ===
IMAGE_DIR = "/Users/youcefbaleh/Desktop/IoT/tmp/images"     # Dossier contenant les photos
DISTANCE_CM = 15         # Distance moyenne en cm (entre caméra et objet)
LASER_COLOR = 'red'      # Couleur du laser : 'red' ou 'green' etc.

# === FONCTIONS ===

def detect_laser_line(image):
    """ Détecte la ligne laser rouge dans une image """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Plage HSV pour laser rouge (ajuste si besoin)
    lower_red1 = np.array([0, 120, 120])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 120, 120])
    upper_red2 = np.array([179, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    coords = cv2.findNonZero(mask)
    if coords is not None:
        return coords[:, 0, :]  # shape (N, 2)
    else:
        return np.empty((0, 2), dtype=np.int32)

def images_to_point_cloud(image_dir):
    """ Génère un nuage de points à partir des images du scan """
    images = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(('.jpeg', '.png'))])
    print(f"{len(images)} images détectées.")

    all_points = []

    for idx, filename in enumerate(images):
        path = os.path.join(image_dir, filename)
        image = cv2.imread(path)
        laser_points = detect_laser_line(image)

        for pt in laser_points:
            x, y = pt
            z = idx * (DISTANCE_CM / len(images))  # Approx. déplacement caméra
            all_points.append([float(x), float(y), float(z)])

    return np.array(all_points, dtype=np.float32)

def export_point_cloud_to_stl(points, output_filename):
    """ Enregistre un maillage STL à partir d’un nuage de points """
    print("[INFO] Génération du fichier STL...")
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    # Filtrage et estimation surface
    pcd = pcd.voxel_down_sample(voxel_size=2.0)
    pcd.estimate_normals()

    # Reconstruction de surface par Poisson
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)
    mesh.compute_vertex_normals()

    # Export STL
    o3d.io.write_triangle_mesh(output_filename, mesh)
    print(f"[OK] Fichier STL enregistré : {output_filename}")

# === SCRIPT PRINCIPAL ===
if __name__ == "__main__":
    print("[INFO] Début de la reconstruction...")

    pts3D = images_to_point_cloud(IMAGE_DIR)

    if pts3D.shape[0] < 100:
        print("[ERREUR] Trop peu de points détectés. Vérifie la visibilité du laser.")
        exit(1)

    export_point_cloud_to_stl(pts3D, "output_model.stl")
