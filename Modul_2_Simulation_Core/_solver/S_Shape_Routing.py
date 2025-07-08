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
        

class SShapeCoordinator:
    def __init__(self, env):
        """
        Initialisiert den Koordinator für S-Shape-Routing.
        :param env: Instanz der WarehouseEnv-Umgebung.
        :param s_path_start: Startpunkt des S-Pfads (x, y).
        """
        self.env = env
        self.paths = [[] for _ in range(env.num_pickers)]  # Geplante Routen für jeden Picker

   

    def plan_picker_paths(self):
        """
        Plant die individuellen Pfade für jeden Picker basierend auf den Clustern und dem S-Pfad.
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

            # Startpunkt auf untere linke ecke des erstennClusters festlegen!
            s_path_start = self.env.get_accessible_position(clusters[0][0][-1])  # Unterer linker Punkt des ersten Clusters


            # 1. Finde den kürzesten Weg vom Picker-Startpunkt zum S-Pfad-Startpunkt
            path += find_path(self.env, start_pos, s_path_start)
            current_pos = s_path_start

            # Pfad zum Startpunkt:
            #print("Picker:", picker_id , "Pfad zum Startpunkt:", path)
            
            # 2. Plane den S-Pfad entlang der Cluster
            direction = "up"  # Startet mit der Bewegung von unten nach oben
            for i, cluster in enumerate(clusters):
                # Markante Punkte definieren
                top_left = self.env.get_accessible_position(cluster[0][0])  # Oberer linker Punkt des Clusters
                bottom_left = self.env.get_accessible_position(cluster[0][-1])  # Unterer linker Punkt des Clusters
                bottom_right = self.env.get_accessible_position(cluster[1][-1])  # Unterer rechter Punkt des Clusters
                top_right = self.env.get_accessible_position(cluster[1][0])  # Oberer rechter Punkt des Clusters
                
                products_in_aisle = []


                if direction == "up":
                    # Optionaler Schirtt
                    # Prüfe vorherigen Cluster für Übergang zur Rückseite
                    if i > 0:
                        path += find_path(self.env, current_pos, bottom_left)  # Bottom-Left des Clusters
                        current_pos = bottom_left


                    # Alle Produkte in diesem Gang sammeln
                    products_in_aisle =  []
                    for product in self.env.current_orders[picker_id]:
                        # Linker Teil des aktuellen Clusters
                        for p in clusters[i][0]:
                            if p == product:
                                products_in_aisle.append(product)
                        if i > 0:
                            # rechter Teil des vorherigen Clusters
                            for p in clusters[i-1][1]:
                                if p == product:
                                    products_in_aisle.append(product)

                    products_in_aisle.sort(key=lambda x: -x[0])  # Sortierung nach Zeilen (von unten nach oben)
                    #print("Picker:", picker_id , "Cluster=", i, "HOCH", "Produkte zum einsammeln", products_in_aisle)


                    # Nun noch die Produkte auf dem Weg einsammeln
                    for tempPaths in products_in_aisle:
                        tempPaths = self.env.get_accessible_position(tempPaths) 
                        if tempPaths not in path:  
                            # checken, ob wir den zusätzlichen weg überhaupt brauchen, oder ib wir bereits an der stelle waren
                            path += find_path(self.env, current_pos, tempPaths)  # Bottom-Left des vorherigen Clusters
                            current_pos = tempPaths


                    # Bewegung nach Oben 
                    path += find_path(self.env, current_pos, top_left)
                    current_pos = top_left


                    # Wenn es kein nachvolgendes Cluster gibt:
                    if i == len(clusters)-1:
                        # RUNTER #
                        # Wir befinden uns im letzten Cluster, wir müssen also nochmal runter gehen

                        # Oben Rechts
                        path += find_path(self.env, current_pos, top_right)
                        current_pos = top_right

                        # Unten Rechts
                        path += find_path(self.env, current_pos, bottom_right)
                        current_pos = bottom_right

                    # Fahrtrichtungswechsel
                    direction = "down"  # Nächster Cluster wird von oben nach unten bearbeitet
                else:
                    prev_cluster = clusters[i - 1]
                    prev_top_right = self.env.get_accessible_position(prev_cluster[1][0])       # Oberer rechter Punkt des Clusters
                    prev_bottom_right = self.env.get_accessible_position(prev_cluster[1][-1])   # Unterer rechter Punkt des Clusters


                    # Alle Produkte in diesem Gang sammeln
                    products_in_aisle =  []
                    for product in self.env.current_orders[picker_id]:
                        # Linker Teil des aktuellen Clusters
                        for p in clusters[i][0]:
                            if p == product:
                                products_in_aisle.append(product)
                                #print("Picker:", picker_id , "Cluster=", i, "Rechts",  "Produkte zum einsammeln", product)
                        if i > 0:
                            # Rechter Teil des vorherigen Clusters
                            for p in clusters[i-1][1]:
                                if p == product:
                                    products_in_aisle.append(product)
                                    #print("Picker:", picker_id , "Cluster=", i-1, "Links",  "Produkte zum einsammeln", product)

                    products_in_aisle.sort(key=lambda x: x[0])  # Sortierung nach Zeilen (von oben nach unten)
                    #print("Picker:", picker_id , "Cluster=", i, "RUNTER",  "Produkte zum einsammeln", products_in_aisle)


                    # Runter
                    # Oben Rechts
                    path += find_path(self.env, current_pos, prev_top_right)  # Bottom-Left des vorherigen Clusters
                    current_pos = prev_top_right

                    # Nun noch die Produkte auf dem Weg einsammeln
                    for tempPaths in products_in_aisle:
                        tempPaths = self.env.get_accessible_position(tempPaths) 
                        if tempPaths not in path:  
                            # checken, ob wir den zusätzlichen weg überhaupt brauchen, oder ib wir bereits an der stelle waren
                            path += find_path(self.env, current_pos, tempPaths)  # Bottom-Left des vorherigen Clusters
                            current_pos = tempPaths


                    # Unten Rechts
                    path += find_path(self.env, current_pos, prev_bottom_right)
                    current_pos = prev_bottom_right


                    if i == len(clusters)-1:
                        # Wir befinden uns im letzten Cluster, wir müssen also noch mal nach oben
                        # Unten Rechts
                        sx, sy = bottom_right
                        sy += 1
                        new_bottom_right = (sx,sy)  # Um eins verschieben, damit wir nicht die doppelschleife laufen, sondern uns auf der imaginären unteren linken ecke des nicht exsitierneden nachfolegrs befinden
                        path += find_path(self.env, current_pos, new_bottom_right)  # Bottom-Left des vorherigen Clusters
                        current_pos = new_bottom_right
                        # Oben Rechts
                        path += find_path(self.env, current_pos, top_right)
                        current_pos = top_right


                    # Fahrtrichtungswechsel
                    direction = "up"  # Nächster Cluster wird von unten nach oben bearbeitet

            # 3. Füge den Weg zur Ablagestation hinzu
            drop_off = self.env.drop_offs[picker_id]
            #print("Wir suchen von ", current_pos, "nach", drop_off)
            path += find_path(self.env, current_pos, drop_off)

            #print("Picker:", picker_id , "Pfad zum Ziel:", path)

            self.paths[picker_id] = path

        return self.paths
