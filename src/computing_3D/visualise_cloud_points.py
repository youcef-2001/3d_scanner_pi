import open3d as o3d
import numpy as np
import os
import utils


if __name__ == "__main__":
    
    
    # read the xyz file
    xyz_file_path = os.path.join('./', "3d_object.xyz")
    points = []
    with open(xyz_file_path, 'r') as xyz_file:
        for line in xyz_file:
            x, y, z = map(float, line.strip().split(','))
            points.append([x, y, z])
    points = np.array(points)
    
    # Create an Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    # Optionally, you can set colors for the points
    pcd.colors = o3d.utility.Vector3dVector(np.random.rand(len(points), 3))  # Random colors for each point

    # Create a coordinate frame at the origin
    camera_origin_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.01, origin=(0,0,-utils.DISTANCE_CAMERA_ROTATION_CENTER))
    center_origin_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.01, origin=(0, 0, 0))

    # Visualize the point cloud with the origin axes
    o3d.visualization.draw_geometries([pcd, camera_origin_frame,center_origin_frame ],
                                      window_name="3D Point Cloud",
                                      width=1200,
                                      height=800)