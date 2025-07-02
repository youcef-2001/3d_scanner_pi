from utils import *
import os
import cv2
import numpy as np


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
    # notre plateforme tourne a 4 rotation par minute
    # donc 15 secondes pour une rotation complete
    # ayant 15.5 FPS
    # donc 15 secondes * 15.6 FPS = 234 images par rotation
    # donc 234 images pour une rotation de 360°
    while  i < len(image_files):
        image_path = image_files[i]
        degree = (i % 223) * (360 / 223)  # Calculer le degré de rotation pour chaque image
        # === Calculer les coordonnées de la caméra ===
        camera_coords = get_camera_coordinates(degree)
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
                        x,y,z= camerapoint_to_centerpoint(camera_coords,x,y,width, height)
                        coords_per_pixel.append((x, y, z))
            coords_per_image.append(coords_per_pixel)
            # transformer les points de chaque image a un origin commun
        i += 1
        
    #Rotation Totale , translation totale


            
    # cree un fichier stl pour lire avec blender
    stl_file_path = os.path.join('./', "3d_object.stl")
    coords_list = [pt for img in coords_per_image for pt in img]
    # faire des triangles avec 3 points de 3 images consécutives
    with open(stl_file_path, 'w') as stl_file:
        # Écrire les triangles dans le fichier STL
        for i in range(len(coords_list) - 2):
            p1 = coords_list[i]
            p2 = coords_list[i + 1]
            p3 = coords_list[i + 2]
            # Ajouter les triangles au fichier STL
            # Remplacer ceci par la fonction d'écriture STL appropriée
            stl_file.write(f"facet normal 0 0 0\n")
            stl_file.write(f"  outer loop\n")
            stl_file.write(f"    vertex {p1[0]} {p1[1]} {p1[2]}\n")
            stl_file.write(f"    vertex {p2[0]} {p2[1]} {p2[2]}\n")
            stl_file.write(f"    vertex {p3[0]} {p3[1]} {p3[2]}\n")
            stl_file.write(f"  endloop\n")
            stl_file.write(f"endfacet\n")
            
            
    print(f"✅ Fichier STL créé avec succès : {stl_file_path}")
    
    # sauvegarder dans un fichier xyz pour visualiser avec open3d
    xyz_file_path = os.path.join('./', "3d_object.xyz")
    with open(xyz_file_path, 'w') as xyz_file:
        for img_coords in coords_per_image:
            for coord in img_coords:
                xyz_file.write(f"{coord[0]} {coord[1]} {coord[2]}\n")
    print(f"✅ Fichier XYZ créé avec succès : {xyz_file_path}")
    
    
    

