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

class ReturnCoordinator:
    def __init__(self, env):
        """
        Initialisiert den Koordinator für Return-Routing.
        :param env: Instanz der WarehouseEnv-Umgebung.
        """
        self.env = env
        self.paths = [[] for _ in range(env.num_pickers)]  # Geplante Routen für jeden Picker

    def plan_picker_paths(self):
        """
        Plant die individuellen Pfade für jeden Picker basierend auf der Return-Strategie.
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
            #An die untere Linke ecke des gangs fahren 
            sx, sy = s_path_start
            pos_above_start = (sx+2 ,sy-1)

            ############################
            # Phase 1: Finde den kürzesten Weg vom Picker-Startpunkt zum S-Pfad-Startpunkt
            path += find_path(self.env, start_pos, pos_above_start)
            current_pos = pos_above_start
            ############################

            ############################
            # Phase 2: Gehe durch die Gänge und ermittle 
            
            for i, cluster in enumerate(clusters):
                top_left = self.env.get_accessible_position(cluster[0][0])
                bottom_left = self.env.get_accessible_position(cluster[0][-1])
                bottom_right = self.env.get_accessible_position(cluster[1][-1])
                top_right = self.env.get_accessible_position(cluster[1][0])

                #An die untere Linke ecke des gangs fahren 
                sx, sy = bottom_left
                pos_above_aisle = (sx+2 ,sy-1)
                path += find_path(self.env, current_pos, pos_above_aisle)  # Bottom-Left des vorherigen Clusters
                current_pos = pos_above_aisle

                
                # Aufträge in diesem Gang identifizieren
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

                products_in_aisle.sort(key=lambda x: x[0])  # Sortierung nach Zeilen (von oben nach unten) -> weil wir nur das höchst-gelegene produkt aktiv anfahren wollen, der rest ergibt sich
                
                
                if len(products_in_aisle) > 0:
                    #print("Picker:", picker_id , "Cluster=", i,  "wir sammeln bloß", products_in_aisle[0], "Produkte zum einsammeln", products_in_aisle)
                    # in diesem gang ist ein produkt zum aufnehmen, wir fahren es also an
                    pos_aisel = current_pos          
                    tempTarget = self.env.get_accessible_position(products_in_aisle[0]) 

                    # Zum weit weg gelegenstens produkt laufen
                    path += find_path(self.env, current_pos, tempTarget)  # Bottom-Left des vorherigen Clusters
                    current_pos = tempTarget
                    
                    # Anschließend wieder nach unten fahren, wo wir vorher standen
                    path += find_path(self.env, current_pos, pos_aisel)  # Bottom-Left des vorherigen Clusters
                    current_pos = pos_aisel


                if i == len(clusters)-1:
                    # Wir befinden uns im letzten Cluster, wir müssen also noch mal nach oben
                    # Unten Rechts
                    sx, sy = bottom_right
                    sy += 1 # 2 nach rechts (aber wir haben schon die Pos wo der Picker hin müsste)
                    sx += 2 # 2 nach unten
                    new_bottom_right = (sx,sy)  # Um eins verschieben, damit wir nicht die doppelschleife laufen, sondern uns auf der imaginären unteren linken ecke des nicht exsitierneden nachfolegrs befinden
                    path += find_path(self.env, current_pos, new_bottom_right)  # Bottom-Left des vorherigen Clusters
                    current_pos = new_bottom_right




                    # Aufträge in diesem Gang identifizieren
                    products_in_aisle =  []
                    for product in self.env.current_orders[picker_id]:
                        if i > 0:
                            # rechter Teil des aktuellen Clusters
                            for p in clusters[i][1]:
                                if p == product:
                                    products_in_aisle.append(product)
                    
                    products_in_aisle.sort(key=lambda x: x[0])  # Sortierung nach Zeilen (von oben nach unten) -> weil wir nur das höchst-gelegene produkt aktiv anfahren wollen, der rest ergibt sich
                    if len(products_in_aisle) > 0:
                        #print("GANZ RECHTS -- Picker:", picker_id , "Cluster=", i,  "wir sammeln bloß", products_in_aisle[0], "Produkte zum einsammeln", products_in_aisle)
                        # in diesem gang ist ein produkt zum aufnehmen, wir fahren es also an     
                        tempPath = self.env.get_accessible_position(products_in_aisle[0]) 
                        path += find_path(self.env, current_pos, tempPath)  
                        current_pos = tempPath
                        
                        # Anschließend wieder nach unten fahren, am unteren Ende des Clusters
                        path += find_path(self.env, current_pos, bottom_right) 
                        current_pos = bottom_right

            # Sofort zur Ablagestation zurückkehren
            drop_off = self.env.drop_offs[picker_id]
            path += find_path(self.env, current_pos, drop_off)
            current_pos = drop_off
                
            self.paths[picker_id] = path
        return self.paths
    

