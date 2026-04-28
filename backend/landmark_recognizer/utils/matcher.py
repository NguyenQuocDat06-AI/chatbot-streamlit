import numpy as np
import cv2

def match_local_ransac(query_local, cand_local, num_patches=576, patch_grid=24):
    """ 
    Toán học để ánh xạ Patch Token 1D sang lưới 2D -> Sử dụng RANSAC tìm Inliers 
    """
    q_norm = query_local / (np.linalg.norm(query_local, axis=-1, keepdims=True) + 1e-8)
    c_norm = cand_local / (np.linalg.norm(cand_local, axis=-1, keepdims=True) + 1e-8)
    
    sim_matrix = np.dot(q_norm, c_norm.T) 
    
    best_match_q_to_c = np.argmax(sim_matrix, axis=1)
    best_match_c_to_q = np.argmax(sim_matrix, axis=0)
    
    pts_q = []
    pts_c = []
    
    for i in range(num_patches):
        j = best_match_q_to_c[i]          
        if best_match_c_to_q[j] == i:
            if sim_matrix[i, j] > 0.6:
                y1, x1 = divmod(i, patch_grid)
                y2, x2 = divmod(j, patch_grid)
                pts_q.append([x1, y1])
                pts_c.append([x2, y2])
                
    if len(pts_q) >= 4:
        pts_q = np.float32(pts_q)
        pts_c = np.float32(pts_c)
        H, mask = cv2.findHomography(pts_q, pts_c, cv2.RANSAC, 2.0)
        inliers = mask.ravel().tolist().count(1) if mask is not None else 0
        return inliers, len(pts_q)
    else:
        return 0, len(pts_q)
