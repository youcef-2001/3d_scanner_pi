import cv2
import numpy as np
import os
import math
"""First test with paper  chessboard calibration
Camera Matrix (Intrinsics):
[[283.52584547   0.         317.4817892 ]
 [  0.         285.4622619  221.27073088]
 [  0.           0.           1.        ]]
Distortion Coefficients:
 [[ 0.04365984 -0.01581748  0.00112492  0.00088643  0.00136511]]
"""
""" Second test with screen Macbook calibration
Camera Matrix (Intrinsics):
 [[305.83777934   0.         316.16069303]
 [  0.         304.78118715 229.49325219]
 [  0.           0.           1.        ]]
Distortion Coefficients:
 [[ 0.05471393 -0.36118367 -0.00134342 -0.00132277  0.72260052]]
"""

# === Dossier des images ===
IMAGE_FOLDER = '/Users/youcefbaleh/Desktop/IoT/tmp/mardi/images/acquisition_01_07_11_07'
DISTANCE_CAMERA_LASER = 6.8# in cm 
DEGREE_CAMERA_CENTER_LASER = 12 # in degree
INITIAL_CAMERA_DEGREE = 90
INITIAL_LASER_DEGREE = 78
HORIZONTAL_FOV = 54 # in degree, horizontal field of view of the camera
VERTICAL_FOV = 42 # in degree, vertical field of view of the camera
HSV_FILTRE= (0, 0, 255, 255, 229, 255) # (l1,l2,l3,h1,h2,h3)
RGB_FILTRE = (169, 205, 205, 255, 255, 255) # (l1,l2,l3,h1,h2,h3)
FOCALE = 3.6 # in mm, focal length of the camera
PIXEL_SIZE=1.388e-6


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
    longitude =  (px - width/2 )* (HORIZONTAL_FOV / width) # Différence en pixels par rapport au centre de l'image
    laser_cam_obj_deg = INITIAL_CAMERA_DEGREE + longitude  # en degré
    # calculer le degré de l'angle Laser_Object_Camera
    # calculer le degré de l'angle Laser_Object_Camera
    laser_obj_cam_deg = 180 - laser_cam_obj_deg - INITIAL_LASER_DEGREE # en degré
    # ratio de triangulation 
    ratio = DISTANCE_CAMERA_LASER / math.sin(math.radians(laser_obj_cam_deg)) 
    # calculer la distance entre la caméra et l'objet sur axe x
    d = ratio * math.sin(math.radians(INITIAL_LASER_DEGREE)) 
    # calculer la distance entre la caméra et l'objet sur axe y
    delta_pixels = py - height / 2
    latitude = (delta_pixels * VERTICAL_FOV / height)  # Différence en pixels par rapport au centre de l'image
    delta_real = abs(delta_pixels * d * PIXEL_SIZE / FOCALE)
    distance = math.sqrt(d**2 + delta_real**2)  # Distance totale

    return distance,latitude,longitude



def spherical_to_cartesian(r, long, latitude):
    """
    Convertit les coordonnées sphériques (distance, longitude, latitude) en coordonnées cartésiennes (x, y, z).
    r : distance de l'objet
    long : longitude de l'objet
    latitude : latitude de l'objet
    Retourne les coordonnées cartésiennes (x, y, z).
    """
    # Convertir les angles en radians
    long_rad = math.radians(long)
    lat_rad = math.radians(latitude)

    # Calculer les coordonnées cartésiennes
    x = r * math.cos(lat_rad) * math.cos(long_rad)
    y = r * math.cos(lat_rad) * math.sin(long_rad)
    z = r * math.sin(lat_rad)

    return x, y, z



 # une platforme rotative tourne l'object de 360° en 15 secondes
    # les image sont prise a une frequence de 15,5 par seconde 
    # la duree de la capture est de 20 secondes
    # donc il y a environ  310 images
    # je dois trouver le nouveau repere de la camera et assembler tout mes points a un repere dont l'origine sera le centre de tout les points 
    
    
def compute_origin_coords(coords_per_image):
    """
    Computes the average coordinates of all points in the list of coordinates per image.
    coords_per_image: List of lists of coordinates per image
    Returns the average coordinates as a tuple (x, y, z).
    """
    total_x = 0
    total_y = 0
    total_z = 0
    count = 0

    for coords in coords_per_image:
        for coord in coords:
            total_x += coord[0]
            total_y += coord[1]
            total_z += coord[2]
            count += 1

    if count == 0:
        return (0, 0, 0)

    return (total_x / count, total_y / count, total_z / count)






    

