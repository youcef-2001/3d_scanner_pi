import os
import cv2
import numpy as np
import open3d as o3d
from scipy.ndimage import gaussian_filter1d

# === CONFIGURATION ===
IMAGE_DIR = r"C:\Users\User\Desktop\Projet\reconstruction3D\acquisition_19_06_23_24"
MODE = "libre"  # "rotation" ou "libre"
PIXEL_SIZE_MM = 0.2
IMAGE_WIDTH, IMAGE_HEIGHT = 640, 480
CX, CY = IMAGE_WIDTH // 2, IMAGE_HEIGHT // 2
Z_STEP_LIBRE = 5.0
VOXEL_SIZE = 0.5
SMOOTH_ITERATIONS = 3

# === DÉTECTION DU LASER ===
def detect_laser_points(image):
    image = cv2.convertScaleAbs(image, alpha=1.5, beta=20)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower1 = np.array([0, 70, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([160, 70, 50])
    upper2 = np.array([179, 255, 255])

    mask = cv2.bitwise_or(cv2.inRange(hsv, lower1, upper1), cv2.inRange(hsv, lower2, upper2))
    margin = IMAGE_WIDTH // 6
    mask[:, :margin] = 0
    mask[:, -margin:] = 0

    points = cv2.findNonZero(mask)
    return points[:, 0, :] if points is not None else np.empty((0, 2), dtype=np.int32)

# === EXTRACTION & SMOOTH Z ===
def compute_smooth_z(image_count, z_step, z_corrections):
    z_list = np.arange(image_count) * z_step + np.array(z_corrections)
    z_smooth = gaussian_filter1d(z_list, sigma=2)
    return z_smooth

# === CONSTRUCTION DU NUAGE 3D ===
def compute_point_cloud(image_dir):
    files = sorted(f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg')))
    print(f"[INFO] {len(files)} images détectées.")
    all_points = []
    z_corrections = []

    for idx, fname in enumerate(files):
        path = os.path.join(image_dir, fname)
        img = cv2.imread(path)
        if img is None:
            print(f"[⚠️] Image illisible : {fname}")
            continue

        laser_pts = detect_laser_points(img)

        if MODE == "rotation":
            angle_deg = idx * (360 / len(files))
            angle_rad = np.radians(angle_deg)

            for x, y in laser_pts:
                r = (x - CX) * PIXEL_SIZE_MM
                z = (CY - y) * PIXEL_SIZE_MM
                X = np.cos(angle_rad) * r
                Y = np.sin(angle_rad) * r
                Z = z
                all_points.append([X, Y, Z])

        elif MODE == "libre":
            y_mean = np.mean(laser_pts[:, 1]) if laser_pts.shape[0] > 0 else CY
            z_offset = (CY - y_mean) * 0.1
            z_corrections.append(z_offset)
        else:
            raise ValueError("MODE doit être 'rotation' ou 'libre'")

    # Refaire un deuxième passage pour le mode libre avec Z lissé
    if MODE == "libre":
        z_smoothed = compute_smooth_z(len(files), Z_STEP_LIBRE, z_corrections)
        for idx, fname in enumerate(files):
            path = os.path.join(image_dir, fname)
            img = cv2.imread(path)
            laser_pts = detect_laser_points(img)
            z = z_smoothed[idx]

            for x, y in laser_pts:
                X = (x - CX) * PIXEL_SIZE_MM
                Y = (CY - y) * PIXEL_SIZE_MM
                Z = z
                all_points.append([X, Y, Z])

    return np.array(all_points, dtype=np.float32)

# === EXPORT STL & PLY ===
def export_mesh(points, base_filename="output_model"):
    print("[INFO] Reconstruction du maillage 3D...")

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd = pcd.voxel_down_sample(voxel_size=VOXEL_SIZE)
    pcd.estimate_normals()

    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)
    mesh = mesh.filter_smooth_simple(number_of_iterations=SMOOTH_ITERATIONS)
    mesh = mesh.remove_degenerate_triangles()
    mesh = mesh.remove_duplicated_triangles()
    mesh = mesh.remove_non_manifold_edges()
    mesh.compute_vertex_normals()

    o3d.io.write_triangle_mesh(f"{base_filename}.stl", mesh)
    o3d.io.write_triangle_mesh(f"{base_filename}.ply", mesh)
    print(f"[✅] Fichiers exportés : {base_filename}.stl & .ply")

# === MAIN ===
if __name__ == "__main__":
    print("🔧 Reconstruction du modèle 3D...")
    pts3D = compute_point_cloud(IMAGE_DIR)

    if pts3D.shape[0] < 100:
        print("[❌] Trop peu de points détectés. Vérifie la visibilité du laser.")
    else:
        export_mesh(pts3D)
