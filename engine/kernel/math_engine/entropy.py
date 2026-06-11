# engine/kernel/math_engine/entropy.py
"""
Structural Entropy Management System.
Computes Average Information Content Classification (AICC), Class Design Entropy (CDE),
Spectral Graph/Laplacian Energy of dependencies, and 3D Coupling Between Objects (CBO).
"""

import os
import ast
import numpy as np
from typing import Dict, List, Tuple, Any

class DependencyGraphBuilder(ast.NodeVisitor):
    """AST visitor to find file dependencies (imports) and method definitions."""
    def __init__(self, current_file: str, base_dir: str):
        self.current_file = current_file
        self.base_dir = base_dir
        self.imports = []
        self.methods = []
        self.calls = 0

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.methods.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        self.calls += 1
        self.generic_visit(node)

def calculate_cde(file_path: str) -> float:
    """
    Computes Class Design Entropy (CDE) based on the size distribution of defined methods.
    CDE = -sum(p_m * log2(p_m)) where p_m is the proportion of lines in method m.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception:
        return 0.0

    methods_lines = []
    # Simple calculation of lines in functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            # Estimate end line using body nodes
            end = start
            for child in ast.walk(node):
                if hasattr(child, 'lineno'):
                    end = max(end, child.lineno)
            methods_lines.append(end - start + 1)
            
    if not methods_lines:
        return 0.0
        
    total_lines = sum(methods_lines)
    if total_lines == 0:
        return 0.0
        
    probs = np.array(methods_lines) / total_lines
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))

def calculate_aicc(file_path: str) -> float:
    """
    Computes Average Information Content Classification (AICC) of the raw text in the file.
    Normalized entropy based on character frequency distribution.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return 0.0
        
    if not content:
        return 0.0
        
    # Count character frequencies
    chars, counts = np.unique(list(content), return_counts=True)
    probs = counts / len(content)
    entropy = -np.sum(probs * np.log2(probs))
    
    # Normalize by log2 of file size (AICC indicator)
    return float(entropy / np.log2(len(content) + 1.0))

class StructuralEntropyMonitor:
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def scan_project(self) -> Dict[str, Any]:
        """Scans python files, builds adjacency matrix and computes metrics."""
        files = []
        for root, _, filenames in os.walk(self.root_dir):
            # Ignore hidden folders and virtual environments
            if any(p in root for p in [".git", ".venv", "node_modules", "__pycache__", "DELETED"]):
                continue
            for f in filenames:
                if f.endswith('.py'):
                    files.append(os.path.join(root, f))
                    
        file_to_idx = {f: i for i, f in enumerate(files)}
        n_files = len(files)
        
        if n_files == 0:
            return {}

        # Parse each file
        dependencies = {f: [] for f in files}
        rfc_dict = {} # Response For Class/Module (methods + external calls)
        cde_dict = {}
        aicc_dict = {}
        
        for f in files:
            aicc_dict[f] = calculate_aicc(f)
            cde_dict[f] = calculate_cde(f)
            
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    tree = ast.parse(fh.read())
                visitor = DependencyGraphBuilder(f, self.root_dir)
                visitor.visit(tree)
                
                rfc_dict[f] = len(visitor.methods) + visitor.calls
                
                # Filter dependencies matching our local project
                for imp in visitor.imports:
                    # Resolve module name to filename if possible
                    # E.g. "engine.kernel.heuristics" -> "engine/kernel/heuristics.py"
                    parts = imp.split('.')
                    potential_rel_path = os.path.join(self.root_dir, *parts)
                    potential_file = potential_rel_path + ".py"
                    if potential_file in file_to_idx:
                        dependencies[f].append(potential_file)
                    else:
                        # Check __init__.py package imports
                        potential_init = os.path.join(potential_rel_path, "__init__.py")
                        if potential_init in file_to_idx:
                            dependencies[f].append(potential_init)
            except Exception:
                rfc_dict[f] = 0

        # Build Adjacency Matrix for component dependencies
        adj = np.zeros((n_files, n_files))
        for f, deps in dependencies.items():
            u = file_to_idx[f]
            for dep in deps:
                v = file_to_idx[dep]
                adj[u, v] = 1.0 # Directed import edge

        # Compute Graph Energy: sum of absolute values of eigenvalues
        # Symmetric version of adjacency for undirected energy approximation
        adj_sym = 0.5 * (adj + adj.T)
        evals_adj = np.linalg.eigvalsh(adj_sym)
        graph_energy = float(np.sum(np.abs(evals_adj)))

        # Compute Laplacian matrix: L = D - A
        degrees = np.sum(adj_sym, axis=0)
        D = np.diag(degrees)
        L = D - adj_sym
        
        evals_lap = np.linalg.eigvalsh(L)
        # Laplacian Energy = sum(|mu_i - 2m/n|)
        n_vertices = n_files
        n_edges = float(np.sum(degrees) / 2.0)
        mean_degree = (2.0 * n_edges) / n_vertices if n_vertices > 0 else 0.0
        laplacian_energy = float(np.sum(np.abs(evals_lap - mean_degree)))

        # 3D CBO Analysis (Strength, Distance, Volatility)
        # We calculate CBO for each file node
        cbo_scores = {}
        refactoring_alerts = []
        
        for f in files:
            u = file_to_idx[f]
            strength = float(np.sum(adj[u, :]) + np.sum(adj[:, u]))
            
            # Distance metric: average directory distance to import targets
            distances = []
            for dep in dependencies[f]:
                # Relative path distance
                f_parts = os.path.relpath(f, self.root_dir).split(os.sep)
                dep_parts = os.path.relpath(dep, self.root_dir).split(os.sep)
                # Find common prefix length
                common = 0
                for p1, p2 in zip(f_parts, dep_parts):
                    if p1 == p2:
                        common += 1
                    else:
                        break
                dist = (len(f_parts) - common) + (len(dep_parts) - common)
                distances.append(dist)
            avg_distance = float(np.mean(distances)) if distances else 0.0
            
            # Volatility (tracked dynamically, default 1.0)
            volatility = 1.0
            
            # CBO 3D score
            cbo_val = strength * (1.0 + avg_distance) * volatility
            cbo_scores[f] = cbo_val
            
            # Check refactoring triggers: high CBO (>10) and high RFC (>20)
            rfc_val = rfc_dict.get(f, 0)
            if cbo_val > 10.0 and rfc_val > 20:
                refactoring_alerts.append({
                    "file": os.path.relpath(f, self.root_dir),
                    "cbo": cbo_val,
                    "rfc": rfc_val,
                    "reason": "High coupling (CBO) and response (RFC) detected. High risk of spaghetti code decay."
                })

        return {
            "files_count": n_files,
            "graph_energy": graph_energy,
            "laplacian_energy": laplacian_energy,
            "mean_aicc": float(np.mean(list(aicc_dict.values()))) if aicc_dict else 0.0,
            "mean_cde": float(np.mean(list(cde_dict.values()))) if cde_dict else 0.0,
            "cbo_scores": {os.path.relpath(k, self.root_dir): v for k, v in cbo_scores.items()},
            "refactoring_alerts": refactoring_alerts
        }

# =========================================================================
# Thermodynamic Entropy & Divergence Calculations (2026 Standards)
# =========================================================================

def calculate_tsallis_entropy(probs: Any, q: float = 2.0) -> float:
    """
    Computes Tsallis entropy of a probability distribution.
    S_q = (1 - sum(p_i^q)) / (q - 1)
    """
    p = np.array(probs, dtype=np.float64)
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    if abs(q - 1.0) < 1e-9:
        # Falls back to Shannon entropy as limit q -> 1
        return float(-np.sum(p * np.log(p)))
    return float((1.0 - np.sum(p ** q)) / (q - 1.0))

def calculate_renyi_entropy(probs: Any, alpha: float = 2.0) -> float:
    """
    Computes Renyi entropy of a probability distribution.
    H_alpha = log2(sum(p_i^alpha)) / (1 - alpha)
    """
    p = np.array(probs, dtype=np.float64)
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    if abs(alpha - 1.0) < 1e-9:
        return float(-np.sum(p * np.log2(p)))
    return float(np.log2(np.sum(p ** alpha)) / (1.0 - alpha))

def calculate_kl_divergence(p: Any, q: Any) -> float:
    """
    Computes Kullback-Leibler (KL) divergence between two probability distributions.
    D_KL(P || Q) = sum(p_i * log2(p_i / q_i))
    """
    p = np.array(p, dtype=np.float64)
    q = np.array(q, dtype=np.float64)
    # Ensure they are normalized
    if np.sum(p) > 0: p /= np.sum(p)
    if np.sum(q) > 0: q /= np.sum(q)
    
    # Avoid zero division and log of zero
    mask = (p > 0) & (q > 0)
    if not np.any(mask):
        return 0.0
    return float(np.sum(p[mask] * np.log2(p[mask] / q[mask])))

def calculate_js_divergence(p: Any, q: Any) -> float:
    """
    Computes Jensen-Shannon (JS) divergence between two probability distributions.
    D_JS(P || Q) = 0.5 * D_KL(P || M) + 0.5 * D_KL(Q || M) where M = 0.5 * (P + Q)
    """
    p = np.array(p, dtype=np.float64)
    q = np.array(q, dtype=np.float64)
    if np.sum(p) > 0: p /= np.sum(p)
    if np.sum(q) > 0: q /= np.sum(q)
    
    m = 0.5 * (p + q)
    return 0.5 * calculate_kl_divergence(p, m) + 0.5 * calculate_kl_divergence(q, m)

def verify_fingerprint_entropy(features: Dict[str, Any], reference: Dict[str, Any], max_kl_threshold: float = 0.5) -> Tuple[bool, float]:
    """
    Validates synthetic fingerprint parameters against an organic reference profile distribution.
    Calculates KL divergence. If it exceeds target threshold, returns False to trigger re-rotation.
    """
    # Convert feature counts/values to numeric list representations for distribution comparison
    feat_keys = sorted(list(set(features.keys()).union(reference.keys())))
    
    p_vals = []
    q_vals = []
    
    for k in feat_keys:
        # Map feature values to numeric signals
        v_p = hash(str(features.get(k, ""))) % 100 + 1
        v_q = hash(str(reference.get(k, ""))) % 100 + 1
        p_vals.append(v_p)
        q_vals.append(v_q)
        
    p_arr = np.array(p_vals, dtype=np.float64)
    q_arr = np.array(q_vals, dtype=np.float64)
    p_arr /= np.sum(p_arr)
    q_arr /= np.sum(q_arr)
    
    kl_div = calculate_kl_divergence(p_arr, q_arr)
    is_valid = kl_div <= max_kl_threshold
    return is_valid, kl_div
