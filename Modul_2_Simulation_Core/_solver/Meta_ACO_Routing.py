import numpy as np
import heapq
import copy
import itertools
import pickle


import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


try:
    from _solver._utility import *
    try:
        from _utility import *
    except:
        pass
except:
    pass

def save_pheromones(aco_coordinator, filename="aco_pheromones.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(aco_coordinator.pheromones, f)

def load_pheromones(aco_coordinator, filename="aco_pheromones.pkl"):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            aco_coordinator.pheromones = pickle.load(f)

class ACORoutingCoordinator:
    def __init__(self, env, num_ants=3, alpha=0.5, beta=4.0, evaporation=0.5, iterations=15):
        """
        Initialisiert den Koordinator für ACO-Routing.
        :param env: Instanz der WarehouseEnv-Umgebung.
        :param num_ants: Anzahl der simulierten Ameisen.
        :param alpha: Einfluss der Pheromone.
        :param beta: Einfluss der Heuristik (kürzester Weg).
        :param evaporation: Pheromon-Verdunstungsrate.
        :param iterations: Anzahl der Optimierungsiterationen.
        """
        self.env = env
        self.num_ants = num_ants
        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation
        self.iterations = iterations
        self.pheromones = {}
        self.paths = [[] for _ in range(env.num_pickers)]

    def initialize_pheromones(self, orders):
        """
        Initialisiert die Pheromonwerte für alle möglichen Verbindungen.
        """
        for picker_orders in orders:
            for a, b in itertools.combinations(picker_orders, 2):
                self.pheromones[(a, b)] = 0.5
                self.pheromones[(b, a)] = 0.5

    def plan_picker_paths(self):
        """
        Plant die optimalen individuellen Pfade für jeden Picker mit Ant Colony Optimization (ACO).
        """
        for picker_id, start_pos in enumerate(self.env.pickers):
            drop_off = self.env.drop_offs[picker_id]
            orders = copy.deepcopy(self.env.current_orders[picker_id])
            if not orders:
                continue
            
            self.initialize_pheromones([orders])
            best_path, best_cost = None, float('inf')
            
            for _ in range(self.iterations):
                all_paths = []
                all_costs = []
                
                for _ in range(self.num_ants):
                    current_pos = start_pos
                    path = []
                    visited = set()
                    
                    while len(visited) < len(orders):
                        probabilities = self.calculate_probabilities(current_pos, orders, visited)
                        next_order = self.roulette_wheel_selection(probabilities)
                        visited.add(next_order)
                        accessible_pos = self.env.get_accessible_position(next_order)
                        if not accessible_pos:
                            continue
                        path_segment = find_path(self.env, current_pos, accessible_pos)
                        path.extend(path_segment)
                        current_pos = accessible_pos
                    
                    path.extend(find_path(self.env, current_pos, drop_off))
                    cost = len(path)
                    all_paths.append((path, cost))
                    all_costs.append(cost)
                
                # Update Pheromone
                self.update_pheromones(all_paths, all_costs)
                
                # Beste gefundene Lösung übernehmen
                min_cost = min(all_costs)
                if min_cost < best_cost:
                    best_cost = min_cost
                    best_path = all_paths[all_costs.index(min_cost)][0]
            
            self.paths[picker_id] = best_path if best_path else []
        return self.paths
    
    def calculate_probabilities(self, current, orders, visited):
        """
        Berechnet die Wahrscheinlichkeiten für die Auswahl des nächsten Ziels basierend auf Pheromonen und Heuristik.
        """
        probabilities = {}
        total = 0.0
        for order in orders:
            if order in visited:
                continue
            pheromone = self.pheromones.get((current, order), 1.0) ** self.alpha
            heuristic = (1.0 / (len(find_path(self.env, current, order)) + 1e-6)) ** self.beta
            probabilities[order] = pheromone * heuristic
            total += probabilities[order]
        for key in probabilities:
            probabilities[key] /= total
        return probabilities
    
    def roulette_wheel_selection(self, probabilities):
        """
        Wählt das nächste Ziel basierend auf den Wahrscheinlichkeiten.
        """
        rand = np.random.rand()
        cumulative = 0.0
        for key, prob in probabilities.items():
            cumulative += prob
            if rand <= cumulative:
                return key
        return list(probabilities.keys())[-1]  # Falls numerische Ungenauigkeiten auftreten
    
    def update_pheromones(self, all_paths, all_costs):
        """
        Aktualisiert die Pheromonwerte basierend auf den gefundenen Lösungen.
        """
        for key in self.pheromones:
            self.pheromones[key] *= (1 - self.evaporation)
        
        for path, cost in zip(all_paths, all_costs):
            for i in range(len(path[0]) - 1):
                a, b = path[0][i], path[0][i + 1]
                if (a, b) not in self.pheromones:
                    self.pheromones[(a, b)] = 1.0  # Standardwert setzen
                if (b, a) not in self.pheromones:
                    self.pheromones[(b, a)] = 1.0  # Standardwert setzen
                
                self.pheromones[(a, b)] += 1.0 / cost
                self.pheromones[(b, a)] += 1.0 / cost
    

