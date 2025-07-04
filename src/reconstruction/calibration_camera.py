import cv2
import numpy as np
import glob

# Chessboard dimensions (number of inner corners)
chessboard_size = (7, 7)
square_size = 1.0  # Set to actual size of a square (e.g., 25mm or 1.0 if using arbitrary units)

# Prepare object points
objp = np.zeros((np.prod(chessboard_size), 3), np.float32)
objp[:, :2] = np.indices(chessboard_size).T.reshape(-1, 2)
objp *= square_size

# Arrays to store object points and image points
objpoints = []  # 3D points in real world
imgpoints = []  # 2D points in image

# Load images
images = glob.glob('/Users/youcefbaleh/Desktop/IoT/tmp/images/lundi/images/acquisition_30_06_18_54/*.jpeg')


for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)
        # Optional: draw and show
        cv2.drawChessboardCorners(img, chessboard_size, corners, ret)
        cv2.imshow('Corners', img)
        cv2.waitKey(100)

cv2.destroyAllWindows()

# Calibrate
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)

# Output
print("Camera Matrix (Intrinsics):\n", camera_matrix)
print("Distortion Coefficients:\n", dist_coeffs)
