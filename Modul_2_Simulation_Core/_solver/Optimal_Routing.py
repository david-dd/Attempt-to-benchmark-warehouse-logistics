import itertools
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

class OptimalRoutingCoordinator:
    def __init__(self, env):
        """
        Initialisiert den Koordinator für das Optimal Routing.
        :param env: Instanz der WarehouseEnv-Umgebung.
        """
        self.env = env
        self.paths = [[] for _ in range(env.num_pickers)]  # Geplante Routen für jeden Picker

    def plan_picker_paths(self):
        """
        Plant die optimalen individuellen Pfade für jeden Picker basierend auf der Permutation aller möglichen Routen.
        """
        for picker_id, start_pos in enumerate(self.env.pickers):
            best_path = None
            min_distance = float('inf')
            best_permutation = None
            drop_off = self.env.drop_offs[picker_id]
            orders = copy.deepcopy(self.env.current_orders[picker_id])
            
            all_permutations = list(itertools.permutations(orders))
            
            for perm in all_permutations:
                path_distance = 0
                current_pos = start_pos
                temp_path = []
                valid = True
                
                for target in perm:
                    accessible_pos = self.env.get_accessible_position(target)
                    if not accessible_pos:
                        valid = False
                        break

                    path = find_path(self.env, current_pos, accessible_pos)
                    if not path:
                        valid = False
                        break

                    path_distance += len(path)
                    temp_path.extend(path)
                    current_pos = accessible_pos
                
                if not valid:
                    continue

                path_to_drop_off = find_path(self.env, current_pos, drop_off)
                if not path_to_drop_off:
                    continue

                path_distance += len(path_to_drop_off)
                temp_path.extend(path_to_drop_off)
                
                if path_distance < min_distance:
                    min_distance = path_distance
                    best_path = temp_path
                    best_permutation = perm
            
            self.paths[picker_id] = best_path if best_path else []
        return self.paths

