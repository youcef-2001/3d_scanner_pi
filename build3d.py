from functions import *



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
    repere_translations = []# images - 1
    previous_image_path = None
    while  i < 400:
        image_path = image_files[i ]
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"❌ Impossible de lire l'image {image_path}.")
            i += 1
            continue
        # === Appliquer le filtre HSV ===
        hsv_result = apply_filter(frame, 'HSV', *HSV_FILTRE)
        # === Appliquer le filtre RGB ===
        rgb_result = apply_filter(hsv_result, 'RGB', *RGB_FILTRE)
        print(f"✅ Image {image_path} traitée avec succès.")

        # === Calculer les coordonnées cylindriques pour chaque pixel non noir de l'image ===
        coords_per_pixel = []
        height, width = frame.shape[:2]
        
        
        ys, xs = np.where(np.any(rgb_result != [0, 0, 0], axis=-1))
        myzip = list(zip(xs, ys))  # Liste des coordonnées (x, y) des pixels non noirs
        if myzip.__len__ == 0:
            print(f"❌ Aucune coordonnée valide trouvée dans l'image {image_path}.")
            i += 1
            continue
        else:    
            for x,y in myzip :
                        distance, latitude, longitude = compute_spherique_coords(x, y, width, height)
                        x_cartesian, y_cartesian, z_cartesian = spherical_to_cartesian(distance, longitude, latitude)
                        coords_per_pixel.append((x_cartesian, y_cartesian, z_cartesian))
            coords_per_image.append(coords_per_pixel)
            if previous_image_path is not None:
                R, t = repere_translation(previous_image_path, image_path)
                if repere_translations.__len__() != 0:
                    last_R = repere_translations[-1][0]
                    last_t = repere_translations[-1][1]
                    t = last_R @ t + last_t  # Translation relative to the previous image
                    R = last_R @ R  # Rotation relative to the previous image    
                repere_translations.append((R, t))
            previous_image_path = image_path
            i += 1
        
    #Rotation Totale , translation totale
    repere_translations = translate_to_one_repere(repere_translations)
    #  transformer les coords de chaque repere (image) vers le repere 0 de la premiere image
    coords_per_image_transformed = []
    for img_num, coords in enumerate(coords_per_image):
        if img_num != 0:
            R, t = repere_translations[img_num-1]
            coords_transformed = [transform_point_to_repere2(np.array(coord), R, t) for coord in coords]
            coords_per_image_transformed.append(coords_transformed)
            
        else:
            coords_per_image_transformed.append(coords)
            
    # cree un fichier stl pour lire avec blender
    stl_file_path = os.path.join('./', "3d_object.stl")
    coords_list = [pt for img in coords_per_image_transformed for pt in img]
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
        for img_coords in coords_per_image_transformed:
            for coord in img_coords:
                xyz_file.write(f"{coord[0]} {coord[1]} {coord[2]}\n")
    print(f"✅ Fichier XYZ créé avec succès : {xyz_file_path}")
    
    
    

