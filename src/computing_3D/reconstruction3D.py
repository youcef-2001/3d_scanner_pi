import cv2
import numpy as np
import os

# === Dossier des images ===
IMAGE_FOLDER = '/Users/youcefbaleh/Desktop/IoT/tmp/images/lundi/images/acquisition_30_06_19_28'
image_files = sorted([
    os.path.join(IMAGE_FOLDER, f)
    for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
])

fps = 30  # Frames per second for the video playback

def nothing(x):
    pass

# === Créer les trackbars pour chaque mode ===
def create_trackbars(window_name):
    cv2.namedWindow(window_name)
    cv2.createTrackbar('L - C1', window_name, 0, 255, nothing)
    cv2.createTrackbar('L - C2', window_name, 0, 255, nothing)
    cv2.createTrackbar('L - C3', window_name, 0, 255, nothing)
    cv2.createTrackbar('H - C1', window_name, 255, 255, nothing)
    cv2.createTrackbar('H - C2', window_name, 255, 255, nothing)
    cv2.createTrackbar('H - C3', window_name, 255, 255, nothing)

def get_trackbar_values(window_name):
    l1 = cv2.getTrackbarPos('L - C1', window_name)
    l2 = cv2.getTrackbarPos('L - C2', window_name)
    l3 = cv2.getTrackbarPos('L - C3', window_name)
    h1 = cv2.getTrackbarPos('H - C1', window_name)
    h2 = cv2.getTrackbarPos('H - C2', window_name)
    h3 = cv2.getTrackbarPos('H - C3', window_name)
    lower = np.array([l1, l2, l3])
    upper = np.array([h1, h2, h3])
    return lower, upper

def apply_filter(img, mode, lower, upper):
    if mode == 'HSV':
        converted = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    else:
        converted = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mask = cv2.inRange(converted, lower, upper)
    result = cv2.bitwise_and(img, img, mask=mask)
    return result, mask

# Initialiser les trackbars pour HSV et RGB
create_trackbars('HSV Filter')
create_trackbars('RGB Filter')

i = 0
origin_point = (0, 0)  # Initial origin point of the camera
while True:
    image_path = image_files[i % len(image_files)]
    frame = cv2.imread(image_path)
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    if frame is None:
        i += 1
        continue

    # HSV
    lower_hsv, upper_hsv = get_trackbar_values('HSV Filter')
    hsv_result, hsv_mask = apply_filter(frame, 'HSV', lower_hsv, upper_hsv)
    hsv_mask_color = cv2.cvtColor(hsv_mask, cv2.COLOR_GRAY2BGR)

    # RGB
    lower_rgb, upper_rgb = get_trackbar_values('RGB Filter')
    rgb_result, rgb_mask = apply_filter(hsv_result, 'RGB', lower_rgb, upper_rgb)
    rgb_mask_color = cv2.cvtColor(rgb_mask, cv2.COLOR_GRAY2BGR)
    # add the origin point of the camera
    
    cv2.circle(rgb_result, (origin_point[0],origin_point[1]), 5, (0, 255, 0), -1)  # Green circle at the center
    
    # Resize all images to the same size
    height, width = frame.shape[:2]
    hsv_result = cv2.resize(hsv_result, (width, height))
    hsv_mask_color = cv2.resize(hsv_mask_color, (width, height))
    rgb_result = cv2.resize(rgb_result, (width, height))
    rgb_mask_color = cv2.resize(rgb_mask_color, (width, height))

    # Add text
    cv2.putText(hsv_result, 'HSV Result', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(hsv_mask_color, 'HSV Mask', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(rgb_result, 'RGB Result', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
    cv2.putText(rgb_mask_color, 'RGB Mask', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
    cv2.putText(frame, 'Original', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # First row: Original | HSV Result | HSV Mask
    row1 = np.hstack((frame, hsv_result, hsv_mask_color))
    # Second row: Original | RGB Result | RGB Mask
    row2 = np.hstack((hsv_result, rgb_result, rgb_mask_color))
    # Stack vertically
    combined = np.vstack((row1, row2))

    cv2.imshow(f'3D Scanner Filters [Origin center  {origin_point}]', combined)


    key = cv2.waitKey(int(1000 / fps)) & 0xFF
    if key == ord('q'):
        break
    # if the arrows keys are pressed, change the origin point of the camera
    elif key == ord('a'):
        # Move left
        origin_point = (origin_point[0] - 10, origin_point[1])
    elif key == ord('d'):
        # Move right
        origin_point = (origin_point[0] + 10, origin_point[1])
    elif key == ord('w'):
        # Move up
        origin_point = (origin_point[0], origin_point[1] - 10)
    elif key == ord('s'):
        # Move down
        origin_point = (origin_point[0], origin_point[1] + 10)  
    elif key == ord('r'):
        # Reset origin point to center
        origin_point = (frame.shape[1] // 2, frame.shape[0] // 2)

    i += 1

cv2.destroyAllWindows()
