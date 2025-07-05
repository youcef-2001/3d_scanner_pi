from reconstruction.utils import apply_filter, get_camera_coordinates, camerapoint_to_centerpoint, IMAGE_FOLDER, HSV_FILTRE, RGB_FILTRE, DISTANCE_CAMERA_ROTATION_CENTER
import os
import cv2
import numpy as np
import logging


def Build_3D_Cloud(AcquisitionDirectory,exportFileAbsolutePath,hsv_filter=HSV_FILTRE, rgb_filter=RGB_FILTRE,fps_on_acqu=15,distance =DISTANCE_CAMERA_ROTATION_CENTER ,logger=logging.getLogger(__name__)):
    """    Fonction pour construire un nuage de points 3D à partir d'images
    """
    # === Chemin du dossier contenant les images ===
    # === Vérifier si le dossier existe ===
    if not os.path.exists(AcquisitionDirectory):
        logger.error(f"❌ Le dossier {AcquisitionDirectory} n'existe pas.")
        exit(1)

        # === Lister les fichiers d'image dans le dossier ===
    image_files = sorted([
        os.path.join(AcquisitionDirectory, f)
        for f in os.listdir(AcquisitionDirectory)
        if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
    ])

    i = 0
    coords_per_image = []
    degree =0
    """ les coords de la camera fixe seront prochainement en fonction
    de la profondeur  , hauteur et angle de capture par rapport au 
    centre de rotation"""
    camera_coords = get_camera_coordinates(degree,0,0,-(float(distance)+6.6)/100)#transform distance to meters and 6.5 is the radius of the platform
    logger.info(f"📷 Coordonnées de la caméra : {camera_coords}")
    ''' notre plateforme tourne a 4 rotation par minute
    # donc 15 secondes pour une rotation complete
    # ayant 15.2 FPS
    # donc 13.6 secondes * 15.2 FPS =  207.2 images
    # donc 234 images pour une rotation de 360°'''
    fps_tour =int (fps_on_acqu * 14.1)  # Nombre d'images pour une rotation complète
    logger.info(f"⏱️ Nombre d'images pour une rotation complète : {  fps_tour}")
    while  i < len(image_files):
        image_path = image_files[i]
        # Calculer le degré de rotation pour chaque image
        # Supposons 234 images pour une rotation complète de 360°
        degree = (i * 360) / fps_tour
        # === Lire l'image ===
        frame = cv2.imread(image_path)
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        if frame is None:
            logger.error(f"❌ Impossible de lire l'image {image_path}.")
            i += 1
            continue
        # === Appliquer le filtre HSV ===
        hsv_result = apply_filter(frame, 'HSV', *hsv_filter)
        # === Appliquer le filtre RGB ===
        rgb_result = apply_filter(hsv_result, 'RGB', *rgb_filter)
        logger.info(f"✅ Image {image_path} traitée avec succès.")
        coords_per_pixel = []
        # taille de l'image
        height, width = frame.shape[:2]
        # les (x,y) des pixels non noirs
        ys, xs = np.where(np.any(rgb_result != [0, 0, 0], axis=-1))
        myzip = list(zip(xs, ys))  # Liste des pixel de l'image courante
        if myzip.__len__ == 0:
            logger.error(f"❌ Aucune coordonnée valide trouvée dans l'image {image_path}.")
            continue
        else:    
            for x,y in myzip :
                        x,y,z= camerapoint_to_centerpoint(camera_coords,x,y,width, height,degree)
                        coords_per_pixel.append((x, y, z))
            coords_per_image.append(coords_per_pixel)
        i += 1
        
    #Rotation Totale , translation totale
    # sauvegarder dans un fichier xyz pour visualiser avec open3d
    
    with open(exportFileAbsolutePath, 'w') as xyz_file:
        for img_coords in coords_per_image:
            for coord in img_coords:
                xyz_file.write(f"{coord[0]} {coord[1]} {coord[2]}\n")
                
    logger.info(f"✅ Fichier XYZ créé avec succès : {exportFileAbsolutePath}")
    

        
        

if __name__ == "__main__":
    # === Chemin du dossier contenant les images ===
    EXPORT_FILE_NAME = "3d_object.xyz"
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    
    # === Vérifier si le dossier existe ===
    if not os.path.exists(IMAGE_FOLDER):
        print(f"❌ Le dossier {IMAGE_FOLDER} n'existe pas.")
        exit(1)
    
    # === Construire le nuage de points 3D ===
    Build_3D_Cloud(IMAGE_FOLDER, EXPORT_FILE_NAME,logger = logger)
