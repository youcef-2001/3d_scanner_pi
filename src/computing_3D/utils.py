import cv2
import numpy as np
import math


# === Dossier des images ===
IMAGE_FOLDER = '/Users/youcefbaleh/Desktop/IoT/tmp/mardi/archive/acquisition_01_07_20_30'
DISTANCE_CAMERA_LASER = 0.073# in m
INITIAL_CAMERA_DEGREE = 90
INITIAL_LASER_DEGREE = 78.5
HORIZONTAL_FOV = 54 # in degree, horizontal field of view of the camera
VERTICAL_FOV = 41 # in degree, vertical field of view of the camera
HSV_FILTRE= (0, 0, 180, 255, 255, 255) # (l1,l2,l3,h1,h2,h3)
RGB_FILTRE = (150, 150, 150, 255, 255, 255) # (l1,l2,l3,h1,h2,h3)
FOCALE = 0.0036 # in m, focal length of the camera
PIXEL_SIZE=1.4e-6 # in m, size of a pixel in the camera sensor
DISTANCE_CAMERA_ROTATION_CENTER = 0.356 # in m, distance between the camera and the rotation center of the platform
DEGREE_CAMERA_ROTATION_AXES = 0 # in degree, the camera rotates around the Y axis of the platform
HEIGHT_CAMERA_ROTATION_CENTER = 0 # in m, height of the camera from the rotation center of the platform


# === Appliquer le filtre  HSV ou RGB ===
def apply_filter(img, mode,l1=0, l2=0, l3=0, h1=255, h2=255, h3=255):
    if mode == 'HSV':
        converted = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    else:
        converted = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    lower = np.array([l1, l2, l3])
    upper = np.array([h1, h2, h3])

    mask = cv2.inRange(converted, lower, upper)
    result = cv2.bitwise_and(img, img, mask=mask)

    return result






def compute_spherique_coords(px,py,width, height):
    """
    Calculates the distance between the camera and the object using triangulation with the laser beam.
    px: x-coordinate of the object's pixel in the image
    py: y-coordinate of the object's pixel in the image
    width: width of the image
    height: height of the image
    Returns the distance between the camera and the object, the latitude, and the longitude of the object in the spherical coordinate system.
    """
    #calculer le degré de l'angle  Laser_Camera_Object
    longitude =  (-px + (width/2) )* (HORIZONTAL_FOV / width) # Différence en pixels par rapport au centre de l'image
    laser_cam_obj_deg = INITIAL_CAMERA_DEGREE + longitude  # en degré
    # calculer le degré de l'angle Laser_Object_Camera
    laser_obj_cam_deg = 180 - laser_cam_obj_deg - INITIAL_LASER_DEGREE # en degré
    # ratio de triangulation 
    ratio = DISTANCE_CAMERA_LASER / math.sin(math.radians(laser_obj_cam_deg)) 
    # calculer la distance entre la caméra et l'objet sur axe x
    d = ratio * math.sin(math.radians(INITIAL_LASER_DEGREE)) 
    #print(f'distance {d}')
    # calculer la distance entre la caméra et l'objet sur axe y
    delta_pixels = -py + (height / 2)
    latitude = (delta_pixels * VERTICAL_FOV / height)  # Différence en pixels par rapport au centre de l'image
    delta_real = delta_pixels * d * PIXEL_SIZE / FOCALE
    distance = math.sqrt(d**2 + delta_real**2)  # Distance totale
    #print(f"Distance: {distance:.2f} cm, Latitude: {latitude:.2f}°, Longitude: {longitude:.2f}°")
    return distance,latitude,longitude





def spherical_to_cartesian(r, longitude, latitude):
    """
    Convertit les coordonnées sphériques (distance, longitude, latitude) en coordonnées cartésiennes (x, y, z).
    r : distance de l'objet
    longitude : longitude de l'objet
    latitude : latitude de l'objet
    Retourne les coordonnées cartésiennes (x, y, z).
    """
    # Convertir les angles en radians
    long_rad = math.radians(longitude)
    lat_rad = math.radians(latitude)

    # Calculer les coordonnées cartésiennes
    # axe verticale est l'axe Y relation avec height de l'image
    # axe horizontale est le X relation avec width de l'image
    # axe de rotation est l'axe Y
    # l'axe de profondeur Z sera l'axe de la plateforme relation avec distance de la caméra au centre de rotation
    x = r * math.sin(lat_rad) * math.sin(long_rad)  # axe X
    z = r * math.cos(lat_rad)  # axe Y
    y = r * math.sin(lat_rad) * math.cos(long_rad)  # axe Z
    
    return x, y, z





 # une platforme rotative tourne l'object de 360° en 15 secondes
def get_rotation_center_coordinates():
    """
    Retourne les coordonnées du centre de rotation de la plateforme.
    # La plateforme est supposée être sur le plan XY"""
    return 0,0,0  # Le centre de rotation est à l'origine du système de coordonnées (0, 0, 0)




def get_camera_coordinates(degree=0,init_x= 0, init_y=HEIGHT_CAMERA_ROTATION_CENTER, init_z=-DISTANCE_CAMERA_ROTATION_CENTER):
    """
    Retourne les coordonnées de la caméra.
    """
    
    # Convertir le degré en radians
    
    
    return init_x, init_y, init_z  # La caméra est supposée être à une distance fixe du centre de rotation sur l'axe Z






def camerapoint_to_centerpoint(cam_coords, px, py, width, height,theta):
    
    theta = np.deg2rad(theta)
    distance, latitude, longitude = compute_spherique_coords(px, py, width, height)
    x, y, z = spherical_to_cartesian(distance, longitude, latitude)     
    P_C = np.array([[x], [y], [z]])  # Point dans le repère de la caméra vecteur colonne
    xc, yc, zc = cam_coords  # Coordonnées de la caméra
    t_C_to_O = np.array([[xc],[yc],[zc]])# Translation de la caméra au centre de rotation, en vecteur colonne
    # Rotation autour de l'axe Y (repère O) 
    # rotation inverse pour revenir au moment 0
    # etant donner que la camera et fixe et seulement prend des capture a des moment t diffrent 
    
    R_y = np.array([
        [ np.cos(-theta), 0, np.sin(-theta)],
        [ 0,             1, 0            ],
        [-np.sin(-theta), 0, np.cos(-theta)]
    ])
    
    # la camera est legerement incliné par rapport a l'axe X de la plateforme
    # donc on applique une rotation autour de l'axe X pour corriger l'inclinaison
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(np.deg2rad(DEGREE_CAMERA_ROTATION_AXES)), -np.sin(np.deg2rad(DEGREE_CAMERA_ROTATION_AXES))],
        [0, np.sin(np.deg2rad(DEGREE_CAMERA_ROTATION_AXES)), np.cos(np.deg2rad(DEGREE_CAMERA_ROTATION_AXES))]
    ])
    # Calcul de la position dans le repère O
    # il translate puis le fait tourner
    P_O = R_y @ (R_x @ P_C + t_C_to_O)  # Appliquer la rotation et la translation
    # return un tuple x,y,z
    return P_O[0, 0], P_O[1, 0], P_O[2, 0]  # Retourne les coordonnées (x, y, z) dans le repère O





#le K donner par default est issue d'une precedente calibration de la camera
def estimate_camera_poses(image_paths, K=np.array([[302.83777934, 0, 320],
                                                   [0, 301.78118715, 240],
                                                   [0, 0, 1]])):
    poses = [np.eye(4)]  # première pose = identité (origine)
    sift = cv2.SIFT_create()
    FLANN_INDEX_KDTREE = 1
    flann = cv2.FlannBasedMatcher(dict(algorithm=FLANN_INDEX_KDTREE, trees=5), dict(checks=50))
    prev_img = cv2.imread(image_paths[0], cv2.IMREAD_GRAYSCALE)
    kp1, des1 = sift.detectAndCompute(prev_img, None)
    for idx in range(1, len(image_paths)):
        curr_img = cv2.imread(image_paths[idx], cv2.IMREAD_GRAYSCALE)
        kp2, des2 = sift.detectAndCompute(curr_img, None)

        matches = flann.knnMatch(des1, des2, k=2)
        good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

        pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])
        pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])

        # Matrice essentielle
        E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, threshold=1.0)

        # Rotation et translation relative
        _, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, K)

        # Construire la transformation homogène 4x4
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t.flatten()

        # Calculer la pose globale : pose_i = pose_{i-1} @ T
        pose_i = poses[-1] @ T
        poses.append(pose_i)

        # Mettre à jour
        kp1, des1 = kp2, des2
        prev_img = curr_img

    return poses  # Liste des matrices 4x4


    

