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

class MidPointCoordinator:
    def __init__(self, env):
        """
        Initialisiert den Koordinator für die Mid-Point Strategy.
        :param env: Instanz der WarehouseEnv-Umgebung.
        """
        self.env = env
        self.paths = [[] for _ in range(env.num_pickers)]  # Geplante Routen für jeden Picker

    def plan_picker_paths(self):
        """
        Plant die individuellen Pfade für jeden Picker basierend auf der Mid-Point-Strategie.
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
        ### Step 3: Mittelpunkt bestimmen
        ############################        

        warehouse_mid = int(self.env.height // 2)  # Mitte des Warehouses in vertikaler Richtung bestimmen


        ############################
        ### Step 4: Mittelpunkt Algo-starten
        ############################  

        for picker_id, start_pos in enumerate(self.env.pickers):
            Laufrichtung = "left"
            Suchrichtung = "bottom"
            path = []
            current_pos = start_pos

            ############################################################################
            # Phase 1: wir müssen nun dynamisch den Startpunkt für jeden picker finden. 
            ############################################################################ 

            # Es gibt zwei möglichkeiten, 
            # entweder direkt oben drüber (pos_1)
            # oder oben und noch eins nach rechts (pos_2)  

            sx, sy = start_pos
            pos_1 = (sx-2, sy)
            pos_2 = (sx-2, sy+1)

            path1 = find_path(self.env, current_pos, pos_1)
            path2 = find_path(self.env, current_pos, pos_2)

            if len(path1) < len(path2):
                path += path1
                current_pos = pos_1
            else:
                path += path2
                current_pos = pos_2  




        
            ############################################################################
            # Phase 2: Es muss geprüft werden, in welchem Gang der Picker steht.
            ############################################################################ 
            current_cluster = None
            cluster_dist = []
            for clusterKey, cluster in enumerate(clusters):
                bottom_left = self.env.get_accessible_position(cluster[0][-1])  # Unterer linker Punkt des Clusters
                temp_path = find_path(self.env, current_pos, bottom_left)
                if len(temp_path) == 1:
                    #print("Picker=", picker_id, "Wir haben den Gang gefunden=", clusterKey)
                    current_cluster = clusterKey
                    break

            
            ############################################################################
            # Phase 3: Abarbeitung des Mid-point-Algo
            ############################################################################ 
            alleGängeAbgeschlossen = False
            StartGangUnten = current_cluster
            while alleGängeAbgeschlossen != True:
              
                # Aufträge in diesem Gang identifizieren
                products_in_aisle =  []
    
                # Wir scanen nun für jedes produkt, dass der picker aufnehmen soll,
                # ob es sich auf der richtigen Seite befindet
                # wenn ja, dann wird geguckt, ob wir uns aktuell im richtigen Gang befinden
                for product in self.env.current_orders[picker_id]:

                    p_sx, p_sy = product
                    if Suchrichtung == "bottom":
                        if p_sx > warehouse_mid:
                            # Produkt befindet sich im unteren Teil
                            pass
                        else:
                            # Produkt befindet sich im oberen Teil, wir suchen aber unten
                            continue
                    else:
                        if p_sx > warehouse_mid:
                            # Produkt befindet sich im unteren Teil, wir suchen aber oben
                            continue
                        else:
                            # Produkt befindet sich im oberen Teil
                            pass

                    # Linker Teil des aktuellen Clusters
                    for p in clusters[current_cluster][0]:
                        if p == product:
                            products_in_aisle.append(product)
                    if current_cluster > 0:
                        # rechter Teil des vorherigen Clusters
                        for p in clusters[current_cluster-1][1]:
                            if p == product:
                                products_in_aisle.append(product)
                
                
                # Wir müssen den Gnag betreten
                if len(products_in_aisle) > 0:

                    # Erstmal sortieren
                    if Suchrichtung == "bottom":                
                        # Sortierung nach Zeilen (von unten nach oben)
                        products_in_aisle.sort(key=lambda x: x[0]) 
                        
                    else:
                        # Sortierung nach Zeilen (von oben nach unten)
                        products_in_aisle.sort(key=lambda x: -x[0])  

                         
                    back_point = None
                    sx, sy = current_pos
                    if Laufrichtung == "left":
                        bottom_left = self.env.get_accessible_position(clusters[current_cluster][0][-1])  # Unterer linker Punkt des Clusters
                        bl_sx, bl_sy = bottom_left
                        back_point = (bl_sx + 1, bl_sy-1)
                    else:
                        back_point = (sx, sy+1) # einen schritt weiter nach rechts
                    #print("Zeile 156 Picker=", picker_id, "Muss den Gang betreten:", current_cluster, "Produkte", products_in_aisle, "Backpoint=", back_point)  
                    
                    tempTarget = self.env.get_accessible_position(products_in_aisle[0]) 
                    #print("Zeile 159 Picker=", picker_id,  "current_pos" , current_pos, "tempTarget=", tempTarget) 
                    
                    # Zum weit weg gelegenstens produkt laufen
                    path += find_path(self.env, current_pos, tempTarget)  
                    current_pos = tempTarget

                    # Anschließend wieder nach unten fahren, wo wir vorher standen
                    # (Ausgenommen: wir stehen ganz links, dann bloß bis zum produkt laufen)
                    if current_cluster != 0:                        
                        path += find_path(self.env, current_pos, back_point)  
                        current_pos = back_point



                # Ab zum nächsten Gang
                if Laufrichtung == "left":
                    if current_cluster == 0:


                    
                        # Wir müssen den Gang nun ertsmal noch vollständig abarbeiten, und bis ganz nach oben:
                        top_right = self.env.get_accessible_position(clusters[current_cluster][1][0])  # Oberer rechter Punkt des Clusters
                        tr_sx, tr_sy = top_right
                        temp_target = (tr_sx-1, tr_sy)
                        path += find_path(self.env, current_pos, temp_target)  # Suche Pfad
                        current_pos = temp_target

                        #print("Zeile 184 Picker=", picker_id, "Geht zum oberen Cluster", current_cluster, "Punkt=", current_pos)  

                        # Laufrichtung ändern
                        Laufrichtung = "right"
                        Suchrichtung = "top"

                        current_cluster +=1


                        
                    else:
                        # Einen gang weiter nach links
                        current_cluster -=1

                        if StartGangUnten == current_cluster:
                            # Der nächste Gang, wäre der, wen wir bereits durchsucht haben!
                            # Rückkehr zur Ablagestation
                            drop_off = self.env.drop_offs[picker_id]
                            path += find_path(self.env, current_pos, drop_off)
                            current_pos = drop_off

                            # Wir brauchen keinen weiteren Durchlauf
                            alleGängeAbgeschlossen = True
                            #print("Alle gänge Abgeschlossen")
                            continue
                        else:
                            # Bewegung an das untere linke Ende vom neuen Cluster
                            bottom_left = self.env.get_accessible_position(clusters[current_cluster][0][-1])  # Unterer linker Punkt des Clusters
                            bl_sx, bl_sy = bottom_left
                            temp_target = (bl_sx + 1, bl_sy)
                            #print("Zeile 215 Picker=", picker_id, "Geht zum unteren Cluster", current_cluster, "Punkt=", temp_target)                            
                            path += find_path(self.env, current_pos, temp_target)
                            current_pos = temp_target
                
                else:
                    # LAUFRICHTUNG = Rechts
                    if current_cluster <= len(clusters)-1:



                        # Bewegung an das untere linke Ende vom neuen Cluster
                        top_right = self.env.get_accessible_position(clusters[current_cluster][1][0])  # Oberer rechter Punkt des Clusters
                        
                        tr_sx, tr_sy = top_right
                        temp_target = (tr_sx -1, tr_sy) # (tr_sx -1, tr_sy+1) <- führt zu einem extra kreis
                        #print("Zeile 229 Picker=", picker_id, "Geht zum oberen Cluster", current_cluster, "Punkt=", temp_target)                            
                        path += find_path(self.env, current_pos, temp_target)
                        current_pos = temp_target

                        
                        # Waren bei bereits im letzten Cluster?
                        if current_cluster == len(clusters)-1:
                            #wir müssen an an das obere Rechte Ende Vom Cluster, und dann ganz nach unten
                            top_right = self.env.get_accessible_position(clusters[current_cluster][1][0])  # Oberer rechter Punkt des Clusters
                            tr_sx, tr_sy = top_right
                            temp_target = (tr_sx-1, tr_sy)
                            path += find_path(self.env, current_pos, temp_target)  # Suche Pfad
                            current_pos = temp_target

                            #print("Picker=", picker_id, "Geht zum letzten oberen Cluster", current_cluster, "Punkt=", current_pos)  


                            # Pciker geht ganz nach unten
                            bottom_right = self.env.get_accessible_position(clusters[current_cluster][1][-1]) # Unterer rechter Punkt des Clusters
                            path += find_path(self.env, current_pos, bottom_right)  # Suche Pfad
                            current_pos = bottom_right

                            #print("Picker=", picker_id, "Geht zum letzten unterem Cluster", current_cluster, "Punkt=", current_pos) 
                            
                            # Laufrichtung ändern
                            Laufrichtung = "left"
                            Suchrichtung = "bottom"

                            # eventuell 
                            # current_cluster -=1 # ????

                        else:
                            # Wir können noch einen Gang nach rechts gehen 
                            current_cluster +=1

    











            #print("Picker=", picker_id, "Pfad=", path)
            #print()
            self.paths[picker_id] = path


            
           

        return self.paths

