import heapq
import copy
try:
    from _solver._utility import *
    try:
        from _utility import *
    except:
        pass
except:
    pass

class LargestGapCoordinator:
    def __init__(self, env):
        """
        Initialisiert den Koordinator für Largest-Gap-Routing.
        :param env: Instanz der WarehouseEnv-Umgebung.
        """
        self.methodName = "LargestGapCoordinator"
        self.env = env
        self.paths = [[] for _ in range(env.num_pickers)]  # Geplante Routen für jeden Picker

    def plan_picker_paths(self):
        """
        Plant die individuellen Pfade für jeden Picker basierend auf der Largest-Gap-Strategie.
        """
        ############################
        ### Step 1: Zusammenhängende Lagerflächen ermitteln
        ############################
        aisles = identify_aisles(self.env)
        #print("Horizontale Gänge:", aisles["horizontal"])
        #print("Vertikale Gänge:", aisles["vertical"])

        ############################
        ### Step 2: Zusammenhängende Lagerflächen Clustern
        ############################
        clusters = cluster_aisles(aisles)
        #print("Cluster:", clusters)

        ############################
        ### Step 3: Route Planen 
        ############################ 

        for picker_id, start_pos in enumerate(self.env.pickers):
            path = []
            s_path_start = self.env.get_accessible_position(clusters[0][0][-1])
            path += find_path(self.env, start_pos, s_path_start)
            current_pos = s_path_start
            
            for cluster in clusters:
                top_left = self.env.get_accessible_position(cluster[0][0])
                bottom_left = self.env.get_accessible_position(cluster[0][-1])
                bottom_right = self.env.get_accessible_position(cluster[1][-1])
                top_right = self.env.get_accessible_position(cluster[1][0])
                
                # Aufträge in diesem Gang identifizieren
                products_in_aisle = []
                for product in self.env.current_orders[picker_id]:
                    if product in cluster[0] or product in cluster[1]:
                        products_in_aisle.append(product)
                
                # Bestimme die größte Lücke zwischen zwei Produkten
                products_in_aisle.sort()
                largest_gap_start = None
                largest_gap_end = None
                max_gap = -1
                
                for i in range(len(products_in_aisle) - 1):
                    gap = products_in_aisle[i + 1][0] - products_in_aisle[i][0]
                    if gap > max_gap:
                        max_gap = gap
                        largest_gap_start = products_in_aisle[i]
                        largest_gap_end = products_in_aisle[i + 1]
                
                # Falls eine große Lücke existiert, beginne von dort aus
                if largest_gap_start and largest_gap_end:
                    path += find_path(self.env, current_pos, largest_gap_start)
                    current_pos = largest_gap_start
                
                # Produkte entlang des Gangs einsammeln
                for product in products_in_aisle:
                    if product not in path:
                        path += find_path(self.env, current_pos, product)
                        current_pos = product
                        self.env.current_orders[picker_id].remove(product)
                
                # Rückkehr zur Ablagestation
                drop_off = self.env.drop_offs[picker_id]
                path += find_path(self.env, current_pos, drop_off)
                current_pos = drop_off
                
            self.paths[picker_id] = path
        return self.paths
    
    def execute_step(self):
        """
        Führt einen Schritt aus, bei dem jeder Picker entlang seines individuellen Pfads bewegt wird.
        """
        execute_step(self.env, self.paths)
