import cv2
import numpy as np
import os
import math


# === Dossier des images ===
IMAGE_FOLDER = '/Users/youcefbaleh/Desktop/IoT/tmp/images/jeudi/acquisition_26_06_12_38'
DISTANCE_CAMERA_LASER = 6.5# in cm 
DEGREE_CAMERA_CENTER_LASER = 14 # in degree
INITIAL_CAMERA_DEGREE = 90
INITIAL_LASER_DEGREE = 76
HORIZONTAL_FOV = 54 # in degree, horizontal field of view of the camera
VERTICAL_FOV = 42 # in degree, vertical field of view of the camera
HSV_FILTRE= (163, 130, 80, 185, 255, 255) # (l1,l2,l3,h1,h2,h3)
RGB_FILTRE = (41, 42, 36, 209, 255, 255) # (l1,l2,l3,h1,h2,h3)
FOCALE = 3.6 # in mm, focal length of the camera
PIXEL_SIZE=1.388e-6
# === Appliquer le filtre 
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
    Calcule la distance entre la caméra et l'objet grace a la triangulation avec le faisceaux du laser.'
    """
    #calculer le degré de l'angle  Laser_Camera_Object
    longitude =  (width/2 - px)* (HORIZONTAL_FOV / width) # Différence en pixels par rapport au centre de l'image
    degree_laser_camera_object = INITIAL_CAMERA_DEGREE +longitude  # en degré
    # calculer le degré de l'angle Laser_Object_Camera
    degree_laser_object_camera = 180 - degree_laser_camera_object- INITIAL_LASER_DEGREE # en degré
    # ratio de triangulation 
    ratio = DISTANCE_CAMERA_LASER / math.sin(math.radians(degree_laser_object_camera)) 
    # calculer la distance entre la caméra et l'objet sur axe x
    d = ratio * math.sin(math.radians(INITIAL_LASER_DEGREE)) 
    # calculer la distance entre la caméra et l'objet sur axe y
    delta_pixels = py - height / 2
    latitude = (delta_pixels * VERTICAL_FOV / height)  # Différence en pixels par rapport au centre de l'image
    delta_real = abs(delta_pixels * d * PIXEL_SIZE / FOCALE)
    distance = math.sqrt(d**2 + delta_real**2)  # Distance totale

    return distance,latitude,longitude



def spherical_to_cartesian(r, long, latitude):
    long = np.deg2rad(long)  # Longitude
    latitude = np.deg2rad(latitude)      # Latitude

    x = r * np.cos(long) * np.cos(latitude)
    y = r * np.cos(long) * np.sin(latitude)
    z = r * np.sin(long)
    return x, y, z



def repere_translation(path_img1,path_img2):

    # === Étape 1 : Charger les deux images ===
    img1 = cv2.imread(path_img1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(path_img2, cv2.IMREAD_GRAYSCALE)

    assert img1 is not None and img2 is not None, "Images non trouvées"

    # === Étape 2 : Détection SIFT + correspondances ===
    sift = cv2.SIFT_create()

    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # Utiliser FLANN matcher
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    # Filtrage de Lowe’s ratio
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    # Extraire les points correspondants
    pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])

    # === Étape 3 : Définir la matrice intrinsèque (à adapter à ta caméra) ===
    # Pour une caméra Raspberry Pi 5MP V1 typique (approximatif)
    fx = fy = 800  # focale en pixels (à adapter si calibré)
    cx, cy = img1.shape[1] / 2, img1.shape[0] / 2

    K = np.array([[fx, 0, cx],
                [0, fy, cy],
                [0,  0,  1]])

    # === Étape 4 : Calculer la matrice essentielle ===
    E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, threshold=1.0)

    # === Étape 5 : Récupérer la rotation et translation entre les deux vues ===
    _,R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, K)
    return R, t


def transform_point_to_repere2(point_3d, R, t):
    """
    Transfère un point du repère 1 vers le repère 2
    point_3d : np.array([X, Y, Z]) dans le repère 1
    R : matrice de rotation
    t : vecteur de translation
    """
    return R @ point_3d + t.flatten()


def translate_to_one_repere(list_R_t):
    """
    Transforme une liste de rotations et translations d'un repere n vers n-1 
    a une liste de translation de repere n vers le repere 0"""
    new_list_R_t = []
    R_total = np.eye(3)
    t_total = np.zeros((3, 1))
    for R, t in list_R_t:
        t_total += R_total @ t
        R_total = R @ R_total
        new_list_R_t.append((R_total, t_total))
    return new_list_R_t

    

