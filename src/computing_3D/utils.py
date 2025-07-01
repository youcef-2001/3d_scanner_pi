import cv2
import numpy as np
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
DISTANCE_CAMERA_LASER = 7.4# in cm 
INITIAL_CAMERA_DEGREE = 90
INITIAL_LASER_DEGREE = 76.8

HORIZONTAL_FOV = 54 # in degree, horizontal field of view of the camera
VERTICAL_FOV = 54 # in degree, vertical field of view of the camera
HSV_FILTRE= (0, 0, 255, 255, 255, 255) # (l1,l2,l3,h1,h2,h3)
RGB_FILTRE = (190, 190, 113, 255, 255, 255) # (l1,l2,l3,h1,h2,h3)
FOCALE = 3.6 # in mm, focal length of the camera
PIXEL_SIZE=1.4e-6
DISTANCE_CAMERA_ROTATION_CENTER = 25.5 # in cm, distance between the camera and the rotation center of the platform

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
    longitude =  (px - (width/2) )* (HORIZONTAL_FOV / width) # Différence en pixels par rapport au centre de l'image
    laser_cam_obj_deg = INITIAL_CAMERA_DEGREE + longitude  # en degré
    # calculer le degré de l'angle Laser_Object_Camera
    # calculer le degré de l'angle Laser_Object_Camera
    laser_obj_cam_deg = 180 - laser_cam_obj_deg - INITIAL_LASER_DEGREE # en degré
    # ratio de triangulation 
    ratio = DISTANCE_CAMERA_LASER / math.sin(math.radians(laser_obj_cam_deg)) 
    # calculer la distance entre la caméra et l'objet sur axe x
    d = ratio * math.sin(math.radians(INITIAL_LASER_DEGREE)) 
    #print(f'distance {d}')
    # calculer la distance entre la caméra et l'objet sur axe y
    delta_pixels = py - (height / 2)
    latitude = (delta_pixels * VERTICAL_FOV / height)  # Différence en pixels par rapport au centre de l'image
    delta_real = abs(delta_pixels * d * PIXEL_SIZE / FOCALE)
    distance = math.sqrt(d**2 + delta_real**2)  # Distance totale
    #print(f"Distance: {distance:.2f} cm, Latitude: {latitude:.2f}°, Longitude: {longitude:.2f}°")
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
    # axe verticale est l'axe Y relation avec height de l'image
    # axe horizontale est le X relation avec width de l'image
    # axe de rotation est l'axe Y
    # l'axe de profondeur Z sera l'axe de la plateforme relation avec distance de la caméra au centre de rotation
    x = r * math.cos(lat_rad) * math.cos(long_rad)  # axe X
    y = r * math.sin(lat_rad)  # axe Y
    z = r * math.cos(lat_rad) * math.sin(long_rad)  # axe
    #print(x,y,z)
    return x, y, z



 # une platforme rotative tourne l'object de 360° en 15 secondes
def get_rotation_center_coordinates():
    """
    Retourne les coordonnées du centre de rotation de la plateforme.
    # La plateforme est supposée être sur le plan XY"""
    return 0,0,0  # Le centre de rotation est à l'origine du système de coordonnées (0, 0, 0)


def get_camera_coordinates(degree,init_x= 0, init_y=0, init_z=-DISTANCE_CAMERA_ROTATION_CENTER):
    """
    Retourne les coordonnées de la caméra.
    """
    # Rotation de la caméra autour de l'axe Y hauteur
    angle_rad = math.radians(degree)
    x = init_x * math.cos(angle_rad) + init_z * math.sin(angle_rad)
    y = init_y
    z = -init_x * math.sin(angle_rad) + init_z * math.cos(angle_rad)

    return x, y, z  # Retourne les coordonnées de la caméra dans le système de coordonnées du centre de rotation

def  camerapoint_to_centerpoint(cam_coords, px, py, width, height):
    """
    Transforme les coordonnées de l'objet détecté par la caméra en coordonnées du centre de rotation.
    degree : degré de la caméra
    px : coordonnée x de l'objet dans l'image
    py : coordonnée y de l'objet dans l'image
    width : largeur de l'image
    height : hauteur de l'image
    Retourne les coordonnées (x, y, z) de l'objet dans le système de coordonnées du centre de rotation.
    """
    distance, latitude, longitude = compute_spherique_coords(px, py, width, height)
    x, y, z = spherical_to_cartesian(distance, longitude, latitude)
    
    # pour transferer lescoords du la camera vers le centre de rotation
    #etant donner qu'il ya pas de rotation de la camera
    # la regle est   P' = P+C ou C est la camera  et 
    # P' est le point dans le systeme de coordonnees du centre de rotation
    x1, y1, z1 = cam_coords
    x_center = x + x1# axe horizontale
    y_center = y + y1 # axe verticale  et de rotation
    z_center = z + z1# axe profondeur
    
    return x_center, y_center, z_center


#le K donner par default est issue d'une precedente calibration de la camera
def estimate_camera_poses(image_paths, K=np.array([[305.83777934, 0, 316.16069303],
                                                   [0, 304.78118715, 229.49325219],
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


    

