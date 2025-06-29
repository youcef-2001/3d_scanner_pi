import cv2
import numpy as np
import os

# === Dossier des images ===
image_folder = '/Users/youcefbaleh/Desktop/IoT/tmp/images/images/acquisition_27_06_03_20'
fichier_distances = '/Users/youcefbaleh/Desktop/IoT/tmp/images/images/acquisition_27_06_03_20/distance_data.csv'
image_files = sorted([
    os.path.join(image_folder, f)
    for f in os.listdir(image_folder)
    if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
])

fps = 25


def nothing(x):
    pass

# === Appliquer le filtre (et retourner aussi le masque) ===
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
# image frame is 5MP so 2592x1944
# Assuming the camera is at the origin (0, 0, 0)
# the distance detector is at (0, -1, 0) cm
# # The camera is looking at the object in the positive Z direction
# The image is in the XY plane, so we need to compute the 3D coordinates
# of the points in the image based on the distances from the distance detector
# and the pixel coordinates in the image.
# The pixel coordinates (u, v) in the image correspond to the 3D coordinates
#th image is already filtered, so we can compute the 3D coordinates directly
# avoid black pixels they are not useful for 3D reconstruction
def compute_3d_coordinates(distance, image):

    # Get non-black pixel coordinates
    ys, xs = np.where(np.any(image != [0, 0, 0], axis=-1))

    # Camera parameters
    img_h, img_w = image.shape[:2]
    cx, cy = img_w / 2, img_h / 2  # principal point at image center
    focal_length_px = 3.6  # Example value, adjust as needed
    
    points_3d = []

    for u, v in zip(xs, ys):
        # Convert pixel to normalized coordinates
        x_norm = (u - cx) / focal_length_px
        y_norm = (v - cy) / focal_length_px

        # Assume Z = distance (from sensor), X = x_norm * Z, Y = y_norm * Z
        Z =distance# Convert cm to meters for 3D coordinates minus 2 percent for better accuracy
        X = x_norm * Z
        Y = y_norm * Z

        points_3d.append((X, Y, Z))

    return np.array(points_3d)




def create_cloud_points(coordinates, output_file='point_cloud.ply'):
        """
        Create a PLY file from the 3D coordinates.
        """
        with open(output_file, 'w') as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(all_coordinates)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("end_header\n")

            for coords in coordinates:
                for point in coords:
                    f.write(f"{point[0]} {point[1]} {point[2]}\n")

        print(f"Point cloud saved to {output_file}")
# create a simple object from the 3D coordinates in stl format
def create_simple_object(coordinates,output_file='simple_object.stl'):
    """
    Create a simple STL file from the 3D coordinates.
    This is a very basic implementation that creates a cube-like object.
    """
    with open(output_file, 'w') as f:
        f.write("solid simple_object\n")
        for coords in coordinates:
            for point in coords:
                f.write(f"  facet normal 1,1,1\n")
                f.write(f"    outer loop\n")
                f.write(f"      vertex {point[0]} {point[1]} {point[2]}\n")
                f.write(f"      vertex {point[0]} {point[1]} {point[2]}\n")
                f.write(f"      vertex {point[0]} {point[1]} {point[2]}\n")
                f.write(f"    endloop\n")
                f.write(f"  endfacet\n")
        f.write("endsolid simple_object\n")

    print(f"Simple object saved to {output_file}")
# === Boucle principale ===
i = 0
# Charger les distances depuis le fichier CSV
# Index,Distance (cm),Amplitude,Temperature (°C),Ticks,Error
#00000,27,5986,4400,33380,0

distances = []
with open(fichier_distances, 'r') as f:
    next(f)  # Skip header
    for line in f:
        parts = line.strip().split(',')
        if len(parts) > 1:
            try:
                distance = float(parts[1])  # Distance is the second column
                distances.append(distance)
            except ValueError:
                continue  # Ignore lines with invalid data

all_coordinates = []
while i < len(image_files):
    image_path = image_files[i % len(image_files)]
    frame = cv2.imread(image_path)
    #rotate 180 degrees
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    distance 
    if frame is None:
        i += 1
        continue

    filtered = apply_filter(frame, 'HSV',99,0,75,165,185,255)#option peux etre rajouter 


    # Chaque image est associée à une distance et l'objet tourne devant la caméra à une vitesse de 360 degrés par minute.
    # La caméra prend 15 images par seconde, donc chaque image correspond à un angle de rotation.
    angle_per_image = 300 / len(image_files)  # 300 degrees en 10 secondes 
    current_angle_deg = (i * angle_per_image) % 360
    current_angle_rad = np.deg2rad(current_angle_deg)

    coords = compute_3d_coordinates(distances[i % len(distances)], filtered)
    # Appliquer la rotation autour de l'axe Y (vertical) pour chaque point
    if coords.size > 0:
        # Matrice de rotation autour de Y
        rotation_matrix = np.array([
            [np.cos(current_angle_rad), 0, np.sin(current_angle_rad)],
            [0, 1, 0],
            [-np.sin(current_angle_rad), 0, np.cos(current_angle_rad)]
        ])
        # Appliquer la rotation à chaque point
        rotated_coords = coords @ rotation_matrix.T
        all_coordinates.append(rotated_coords)
    else:
        all_coordinates.append(coords)



    cv2.imshow('Video Filter | [Original | Filtré | Masque]', filtered)

    key = cv2.waitKey(int(1000 / fps)) & 0xFF

    if key == ord('q'):
        break

    i += 1


cv2.destroyAllWindows()

# Créer le nuage de points à partir des coordonnées 3D
create_cloud_points(all_coordinates, output_file='point_cloud.ply')
# Créer un objet simple à partir des coordonnées 3D
create_simple_object(all_coordinates, output_file='simple_object.stl')


