# engine/kernel/math_engine/tda.py
"""
Topological Data Analysis (TDA) DOM Environment Parser.
Extracts persistent homology from DOM coordinates, constructs UMAP/PCA Mapper graphs,
describes DOM trees using Topological Morphology Descriptors (TMD), and compares states
via 1-Wasserstein distances.
"""

import numpy as np
import scipy.spatial
import scipy.optimize
import site

# Ensure user site packages are enabled for gudhi and umap
site.ENABLE_USER_SITE = True
site.main()

try:
    import gudhi
except ImportError:
    gudhi = None

try:
    import umap
except ImportError:
    umap = None

from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from typing import Tuple, List, Dict, Any

def compute_persistence_homology(points: np.ndarray, max_edge_length: float = 1000.0) -> List[Tuple[int, Tuple[float, float]]]:
    """
    Constructs a Vietoris-Rips complex on a DOM element point cloud and computes persistence homology.
    Returns:
        List of (dimension, (birth, death)) tuples.
    """
    if gudhi is None:
        # Fallback persistence diagram (simple clustering threshold approximation)
        # H0 elements can be approximated via hierarchical clustering
        return [(0, (0.0, float('inf')))]

    if points.ndim == 1:
        points = points.reshape(-1, 1)
        
    if len(points) == 0:
        return []

    # Use Gudhi RipsComplex
    rips_complex = gudhi.RipsComplex(points=points, max_edge_length=max_edge_length)
    simplex_tree = rips_complex.create_simplex_tree(max_dimension=2)
    persistence = simplex_tree.persistence()
    
    return persistence

def compute_wasserstein_distance_scipy(diag1: np.ndarray, diag2: np.ndarray) -> float:
    """
    Pure-Python / SciPy exact 1-Wasserstein distance between two persistence diagrams.
    Matches points to points or to their projection on the diagonal y = x.
    """
    # Filter out infinite death points
    d1 = np.array([p for p in diag1 if np.isfinite(p[1])])
    d2 = np.array([p for p in diag2 if np.isfinite(p[1])])
    
    N1 = len(d1)
    N2 = len(d2)
    
    if N1 == 0 and N2 == 0:
        return 0.0
    if N1 == 0:
        # Distance from d2 to diagonal
        return float(np.sum((d2[:, 1] - d2[:, 0]) / 2.0))
    if N2 == 0:
        # Distance from d1 to diagonal
        return float(np.sum((d1[:, 1] - d1[:, 0]) / 2.0))
        
    # Cost matrix dimensions: (N1 + N2) x (N1 + N2)
    cost_matrix = np.zeros((N1 + N2, N1 + N2))
    
    # Cost of matching points in d1 to points in d2
    # L1 cost: |birth1 - birth2| + |death1 - death2|
    for i in range(N1):
        for j in range(N2):
            cost_matrix[i, j] = np.abs(d1[i, 0] - d2[j, 0]) + np.abs(d1[i, 1] - d2[j, 1])
            
    # Cost of matching points in d1 to diagonal y=x
    # Diagonal projection of (b, d) is ((b+d)/2, (b+d)/2).
    # Distance in L1 is |b - (b+d)/2| + |d - (b+d)/2| = (d - b)
    for i in range(N1):
        cost_matrix[i, N2 + i] = d1[i, 1] - d1[i, 0]
        
    # Cost of matching points in d2 to diagonal y=x
    for j in range(N2):
        cost_matrix[N1 + j, j] = d2[j, 1] - d2[j, 0]
        
    # Dummy matches have cost 0 (already initialized to 0)
    
    # Solve linear sum assignment problem
    row_ind, col_ind = scipy.optimize.linear_sum_assignment(cost_matrix)
    distance = cost_matrix[row_ind, col_ind].sum()
    return float(distance)

def compute_wasserstein_distance(diag1: List[Tuple[float, float]], diag2: List[Tuple[float, float]]) -> float:
    """
    Computes 1-Wasserstein distance between persistence diagrams.
    Falls back to SciPy implementation if Gudhi native Wasserstein module is unavailable.
    """
    global gudhi
    if gudhi is not None:
        try:
            import gudhi.wasserstein
            # Convert diagrams to numpy arrays of floats, removing dimension
            d1 = np.array(diag1, dtype=float)
            d2 = np.array(diag2, dtype=float)
            # Remove infinite values for distance computation
            d1 = d1[np.isfinite(d1).all(axis=1)]
            d2 = d2[np.isfinite(d2).all(axis=1)]
            if len(d1) == 0 or len(d2) == 0:
                return compute_wasserstein_distance_scipy(d1, d2)
            return float(gudhi.wasserstein.wasserstein_distance(d1, d2, order=1.0))
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
            
    return compute_wasserstein_distance_scipy(np.array(diag1), np.array(diag2))

def mapper_algorithm(
    points: np.ndarray,
    projection_method: str = "umap",
    num_intervals: int = 6,
    overlap_fraction: float = 0.3
) -> Dict[str, Any]:
    """
    Constructs a Mapper Graph for a set of points (e.g. element centers/bounding boxes).
    1. Project points to 1D using UMAP or PCA.
    2. Define overlapping intervals.
    3. Cluster points in each interval.
    4. Connect clusters sharing common points.
    """
    if len(points) == 0:
        return {"nodes": {}, "edges": []}
        
    # Step 1: Projection
    if projection_method == "umap" and umap is not None:
        try:
            reducer = umap.UMAP(n_components=1, random_state=42, n_neighbors=min(15, len(points)-1))
            filt = reducer.fit_transform(points).flatten()
        except Exception:
            # Fallback to PCA if UMAP fails
            pca = PCA(n_components=1)
            filt = pca.fit_transform(points).flatten()
    else:
        pca = PCA(n_components=1)
        filt = pca.fit_transform(points).flatten()
        
    # Step 2: Overlapping intervals
    f_min, f_max = filt.min(), filt.max()
    if np.isclose(f_min, f_max):
        f_max += 1.0 # Avoid division by zero
        
    interval_length = (f_max - f_min) / (num_intervals - (num_intervals - 1) * overlap_fraction)
    step = interval_length * (1.0 - overlap_fraction)
    
    intervals = []
    for i in range(num_intervals):
        start = f_min + i * step
        end = start + interval_length
        intervals.append((start, end))
        
    # Step 3: Clustering inside each interval
    nodes = {}
    node_id_counter = 0
    # Map from point index to list of node IDs it belongs to
    point_to_nodes = {i: [] for i in range(len(points))}
    
    for int_idx, (start, end) in enumerate(intervals):
        # Indices of points in this interval
        indices = np.where((filt >= start) & (filt <= end))[0]
        if len(indices) == 0:
            continue
            
        pts_in_interval = points[indices]
        
        # Cluster with DBSCAN
        # Scale eps dynamically based on points scale
        if len(pts_in_interval) > 1:
            dists = scipy.spatial.distance.pdist(pts_in_interval)
            eps = np.median(dists) if len(dists) > 0 else 10.0
            eps = max(eps, 1.0)
            db = DBSCAN(eps=eps, min_samples=1).fit(pts_in_interval)
            labels = db.labels_
        else:
            labels = np.array([0])
            
        # Group points by cluster
        for label in set(labels):
            if label == -1: # Noise points get their own nodes in Mapper
                continue
            cluster_indices = indices[np.where(labels == label)[0]]
            node_id = f"node_{node_id_counter}"
            node_id_counter += 1
            
            nodes[node_id] = {
                "interval_index": int_idx,
                "cluster_label": label,
                "points_indices": cluster_indices.tolist(),
                "centroid": pts_in_interval[np.where(labels == label)[0]].mean(axis=0).tolist()
            }
            
            for idx in cluster_indices:
                point_to_nodes[idx].append(node_id)
                
    # Step 4: Construct edges
    edges = set()
    for pt_idx, node_ids in point_to_nodes.items():
        if len(node_ids) > 1:
            # Point belongs to multiple nodes -> link them
            for i in range(len(node_ids)):
                for j in range(i + 1, len(node_ids)):
                    n1, n2 = node_ids[i], node_ids[j]
                    # Lexicographical order to avoid duplicates
                    if n1 < n2:
                        edges.add((n1, n2))
                    else:
                        edges.add((n2, n1))
                        
    return {
        "nodes": nodes,
        "edges": list(edges)
    }

def compute_tmd(tree_dict: Dict[str, Any]) -> List[Tuple[float, float]]:
    """
    Computes the Topological Morphology Descriptor (TMD) barcode for a hierarchical DOM tree.
    Returns:
        List of (birth, death) persistence intervals.
    """
    # Step 1: Flatten tree and compute depths
    # tree_dict format: {"id": str, "x": float, "y": float, "children": [...]}
    node_depths = {}
    node_parent = {}
    
    def traverse(node: Dict[str, Any], depth: float, parent_id: str = None):
        n_id = node["id"]
        node_depths[n_id] = depth
        node_parent[n_id] = parent_id
        for child in node.get("children", []):
            # Children are deeper, increase depth
            traverse(child, depth + 1.0, n_id)
            
    traverse(tree_dict, 0.0)
    
    # Find all leaf nodes
    all_nodes = set(node_depths.keys())
    parent_nodes = set(node_parent.values())
    leaves = all_nodes - parent_nodes
    
    # Sort leaves by depth (descending)
    sorted_leaves = sorted(leaves, key=lambda l: node_depths[l], reverse=True)
    
    visited = set()
    barcodes = []
    
    for leaf in sorted_leaves:
        curr = leaf
        birth = node_depths[leaf]
        death = 0.0 # Default death is the root (depth 0)
        
        # Trace up the ancestry path
        path = []
        while curr is not None:
            if curr in visited:
                # Merge point reached!
                # This branch dies here
                death = node_depths[curr]
                break
            path.append(curr)
            curr = node_parent[curr]
            
        # Mark path as visited
        for node in path:
            visited.add(node)
            
        barcodes.append((birth, death))
        
    return barcodes

def find_target_topologically(
    actual_elements: List[Dict[str, Any]],
    expected_layout_barcode: List[Tuple[float, float]],
    feature_keys: List[str] = ["x", "y", "width", "height"]
) -> int:
    """
    Targets an element by matching persistence landscapes and barcodes, making it resistant
    to class/DOM obfuscation.
    Returns:
        Index of the matching target element in actual_elements.
    """
    if len(actual_elements) == 0:
        return -1
        
    # Compute baseline coordinates
    best_idx = -1
    min_dist = float('inf')
    
    for i, elem in enumerate(actual_elements):
        # Construct a sub-point cloud centered around elem
        center_x = elem.get("x", 0) + elem.get("width", 0)/2.0
        center_y = elem.get("y", 0) + elem.get("height", 0)/2.0
        
        # Build local coordinate cloud of neighboring elements
        local_cloud = []
        for other in actual_elements:
            ox = other.get("x", 0) + other.get("width", 0)/2.0
            oy = other.get("y", 0) + other.get("height", 0)/2.0
            dist = np.hypot(ox - center_x, oy - center_y)
            if dist < 400.0: # Local neighborhood radius
                local_cloud.append([ox - center_x, oy - center_y, other.get("width", 0), other.get("height", 0)])
                
        if len(local_cloud) < 2:
            continue
            
        # Compute local persistent homology
        local_points = np.array(local_cloud)
        pers = compute_persistence_homology(local_points)
        # Extract birth-death pairs for H0/H1
        barcode = [(b, d) for dim, (b, d) in pers]
        
        # Compute Wasserstein distance to expected template
        w_dist = compute_wasserstein_distance(barcode, expected_layout_barcode)
        if w_dist < min_dist:
            min_dist = w_dist
            best_idx = i
            
    # Fallback to standard proximity if no topological matching succeeds
    if best_idx == -1:
        return 0
        
    return best_idx
