import cv2
import numpy as np
import os

# === Dossier des images ===
image_folder = r'C:\Users\User\imagesTmp\acquisition_27_06_03_20'
image_files = sorted([
    os.path.join(image_folder, f)
    for f in os.listdir(image_folder)
    if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
])

fps = 25
mode = 'HSV'

def nothing(x):
    pass

# === Créer les trackbars ===
def create_trackbars(mode):
    cv2.namedWindow('Filter')
    cv2.createTrackbar('L - C1', 'Filter', 0, 255, nothing)
    cv2.createTrackbar('L - C2', 'Filter', 0, 255, nothing)
    cv2.createTrackbar('L - C3', 'Filter', 0, 255, nothing)
    cv2.createTrackbar('H - C1', 'Filter', 255, 255, nothing)
    cv2.createTrackbar('H - C2', 'Filter', 255, 255, nothing)
    cv2.createTrackbar('H - C3', 'Filter', 255, 255, nothing)

# === Appliquer le filtre (et retourner aussi le masque) ===
def apply_filter(img, mode):
    if mode == 'HSV':
        converted = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    else:
        converted = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    l1 = cv2.getTrackbarPos('L - C1', 'Filter')
    l2 = cv2.getTrackbarPos('L - C2', 'Filter')
    l3 = cv2.getTrackbarPos('L - C3', 'Filter')
    h1 = cv2.getTrackbarPos('H - C1', 'Filter')
    h2 = cv2.getTrackbarPos('H - C2', 'Filter')
    h3 = cv2.getTrackbarPos('H - C3', 'Filter')

    lower = np.array([l1, l2, l3])
    upper = np.array([h1, h2, h3])

    mask = cv2.inRange(converted, lower, upper)
    result = cv2.bitwise_and(img, img, mask=mask)

    return result, mask

# Initialiser les trackbars
create_trackbars(mode)

# === Boucle principale ===
i = 0
while True:
    image_path = image_files[i % len(image_files)]
    frame = cv2.imread(image_path)
    #rotate 180 degrees
    frame = cv2.rotate(frame, cv2.ROTATE_180)

    if frame is None:
        i += 1
        continue

    filtered, mask = apply_filter(frame, mode)

    # Mettre texte du mode en haut de l'image filtrée
    cv2.putText(filtered, f'Mode: {mode}', (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Convertir le masque en image 3 canaux pour affichage
    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    # Redimensionner toutes les images à la même taille (au cas où)
    height, width = frame.shape[:2]
    filtered = cv2.resize(filtered, (width, height))
    mask_color = cv2.resize(mask_color, (width, height))

    # Fusion horizontale
    combined = np.hstack((frame, filtered, mask_color))
    cv2.imshow('Video Filter | [Original | Filtré | Masque]', combined)

    key = cv2.waitKey(int(1000 / fps)) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('h') and mode != 'HSV':
        mode = 'HSV'
        create_trackbars(mode)
    elif key == ord('r') and mode != 'RGB':
        mode = 'RGB'
        create_trackbars(mode)

    i += 1

cv2.destroyAllWindows()
