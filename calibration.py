import cv2
import numpy as np
import glob

# === PARAMETERS ===
chessboard_size = (9, 6)  # Number of inner corners per a chessboard row and column
square_size = 1.0         # Set this to your chessboard square size (e.g., in cm or inches)

# === PREPARE OBJECT POINTS ===
# Create a 3D array of points in real world space (z=0 for flat chessboard)
objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.indices(chessboard_size).T.reshape(-1, 2)
objp *= square_size

# Arrays to store object points and image points from all images
objpoints = []  # 3D points in real world space
imgpoints = []  # 2D points in image plane

# === LOAD IMAGES ===
images = glob.glob('/Users/youcefbaleh/Desktop/IoT/tmp/images/calib/images/acquisition_30_06_18_54/*.jpeg')

print(f"Found {len(images)} images for calibration.")

if len(images) == 0:
    print("No images found. Check the folder path!")
    exit(1)

# === PROCESS EACH IMAGE ===
for fname in images:
    img = cv2.imread(fname)
    if img is None:
        print(f"Failed to load image {fname}")
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
    print(f"Processing {fname}: Chessboard found? {ret}")

    # If found, add object points, image points
    if ret:
        objpoints.append(objp)
        # Refine corner locations to subpixel accuracy
        corners_refined = cv2.cornerSubPix(
            gray, corners, winSize=(11, 11), zeroZone=(-1, -1),
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        )
        imgpoints.append(corners_refined)

        # Draw and display corners
        cv2.drawChessboardCorners(img, chessboard_size, corners_refined, ret)
    else:
        print(f"Warning: Chessboard corners not found in {fname}")

    cv2.imshow('Calibration', img)
    key = cv2.waitKey(500)
    if key == 27:  # Press ESC to quit early
        print("Calibration interrupted by user.")
        break

cv2.destroyAllWindows()

# === CHECK IF SUFFICIENT DATA ===
if len(objpoints) == 0 or len(imgpoints) == 0:
    print("Error: No corners were detected in any image. Calibration failed.")
    exit(1)

# === CAMERA CALIBRATION ===
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)

print("\nCalibration successful:", ret)
print("\nCamera Matrix (intrinsics):\n", camera_matrix)
print("\nDistortion Coefficients:\n", dist_coeffs.ravel())

# === REPROJECTION ERROR CALCULATION ===
total_error = 0
for i in range(len(objpoints)):
    imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
    error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
    total_error += error

mean_error = total_error / len(objpoints)
print(f"\nMean reprojection error: {mean_error}")

# Optional: Save calibration parameters to a file
np.savez("camera_calibration_data.npz", camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)

print("\nCalibration data saved to camera_calibration_data.npz")
