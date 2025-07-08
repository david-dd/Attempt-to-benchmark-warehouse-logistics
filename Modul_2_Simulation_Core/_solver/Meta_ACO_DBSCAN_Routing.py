import numpy as np
import heapq
import copy
import itertools
from sklearn.cluster import DBSCAN

try:
    from _solver._utility import *
    try:
        from _utility import *
    except:
        pass
except:
    pass

class ACODbscanRoutingCoordinator:
    def __init__(self, env, num_ants=10, alpha=1.0, beta=2.0, evaporation=0.5, iterations=50, eps=3, min_samples=2):
        """
        Initialisiert den Koordinator für ACO-Routing mit Clustering.
        :param env: Instanz der WarehouseEnv-Umgebung.
        :param num_ants: Anzahl der simulierten Ameisen.
        :param alpha: Einfluss der Pheromone.
        :param beta: Einfluss der Heuristik (kürzester Weg).
        :param evaporation: Pheromon-Verdunstungsrate.
        :param iterations: Anzahl der Optimierungsiterationen.
        :param eps: DBSCAN-Parameter für die maximale Distanz eines Clusters.
        :param min_samples: Minimale Anzahl an Punkten für einen Cluster.
        """
        self.env = env
        self.num_ants = num_ants
        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation
        self.iterations = iterations
        self.eps = eps
        self.min_samples = min_samples
        self.pheromones = {}
        self.paths = [[] for _ in range(env.num_pickers)]

    def cluster_orders(self):
        """
        Clustert die aktuellen Bestellungen mit DBSCAN.
        """
        orders = []
        for picker_id, picker_orders in enumerate(self.env.current_orders):
            orders.extend(picker_orders)
        
        if not orders:
            return []
        
        orders = np.array(orders)
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric='manhattan').fit(orders)
        clusters = {}
        
        for i, label in enumerate(clustering.labels_):
            if label == -1:
                continue  # Noise ignorieren
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(tuple(orders[i]))
        
        return list(clusters.values())  # Rückgabe als Liste von Cluster-Listen

    def plan_picker_paths(self):
        """
        Plant die optimalen individuellen Pfade für jeden Picker mit ACO auf Cluster-Ebene.
        """
        clusters = self.cluster_orders()
        if not clusters:
            self.paths = [[] for _ in range(self.env.num_pickers)]  # Sicherstellen, dass self.paths nicht None ist
            return self.paths
        
        cluster_sequence = self.plan_cluster_routes(clusters)
        
        for picker_id, start_pos in enumerate(self.env.pickers):
            path = []
            current_pos = start_pos
            
            for cluster in cluster_sequence:
                path += self.plan_routes_within_cluster(cluster, current_pos)
                current_pos = path[-1] if path else current_pos
            
            drop_off = self.env.drop_offs[picker_id]
            path += find_path(self.env, current_pos, drop_off)
            self.paths[picker_id] = path
        return self.paths
    
    def plan_cluster_routes(self, clusters):
        """
        Nutzt ACO, um die optimale Besuchsreihenfolge der Cluster zu bestimmen.
        """
        pheromones = {(i, j): 1.0 for i in range(len(clusters)) for j in range(len(clusters)) if i != j}
        best_order = None
        best_cost = float('inf')
        
        for _ in range(10):
            order = [0]
            while len(order) < len(clusters):
                last = order[-1]
                next_cluster = min(
                    [i for i in range(len(clusters)) if i not in order],
                    key=lambda i: pheromones[(last, i)] / np.linalg.norm(np.array(clusters[last][0]) - np.array(clusters[i][0])),
                )
                order.append(next_cluster)
            cost = sum(np.linalg.norm(np.array(clusters[order[i]][0]) - np.array(clusters[order[i+1]][0])) for i in range(len(order)-1))
            if cost < best_cost:
                best_cost = cost
                best_order = order
            
            for i in range(len(order) - 1):
                pheromones[(order[i], order[i+1])] += 1.0 / cost
                pheromones[(order[i+1], order[i])] += 1.0 / cost
        
        return [clusters[i] for i in best_order]
    
    def plan_routes_within_cluster(self, cluster, current_pos):
        """
        Nutzt eine heuristische Methode, um eine Route innerhalb eines Clusters zu planen.
        """
        path = []
        for target in sorted(cluster, key=lambda x: np.linalg.norm(np.array(current_pos) - np.array(x))):
            accessible_pos = self.env.get_accessible_position(target)
            if not accessible_pos:
                continue
            path += find_path(self.env, current_pos, accessible_pos)
            current_pos = accessible_pos
        return path