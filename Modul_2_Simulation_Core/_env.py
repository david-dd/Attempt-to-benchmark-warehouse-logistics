import pickle
import numpy as np
import random
from itertools import permutations
import copy
import heapq
import json
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random


import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class WarehouseEnv:
    def __init__(self,  min_orders=4, max_orders=4, json_file=None):

        ###################################
        #### Eigenschaften des Warehouses
        ###################################
        # Dim der Env
        self.width = None
        self.height = None
        self.num_pickers = None         # Anzahl der Picker
        self.picker_initPos = None      # Picker-Startpositionen 
        self.pickers = []             # Picker-Positionen
        self.drop_offs = None           # Ablagepositionen 
        self.jsonData = None
        self.graph = None
        self.min_orders = max(min_orders, 1) # mindestens eine Order
        self.max_orders = min(max_orders,10) # Pro Auftrag maximal 10 Produkt
        self.pland_paths = None
        self.history = []  # Liste für die gesamte Historie
        self.historyp = []  # Liste für die gesamte Historie
        self.grid_static = None
        self.wait_times = None

        self.parse_json(json_file)          # Laden der JSON und speichere sie in einer temp-variable
        self.reset()

      




    def parse_json(self, json_file):
        import json
        import numpy as np

        # JSON-Daten einlesen
        with open(json_file, "r") as file:
            data = json.load(file)

        self.jsonData = data.get("gridData", [])

    def reset_env_based_on_json(self):
        
        self.height = len(self.jsonData)
        self.width = len(self.jsonData[0])

        
        self.grid = np.full((self.height, self.width), " . ")
        self.storage_ids = np.full((self.height, self.width), "    ")

        
        pickers = 0
        self.pickers = []
        for row_index, row in enumerate(self.jsonData):
            for col_index, cell in enumerate(row):
                # Flurweg (Leerzeichen mit Richtungsangaben)
                if any(direction in cell for direction in ["L", "R", "U", "O"]):
                    self.grid[row_index, col_index] = cell.strip()
                if "D" in cell:
                    pickers += 1
                    self.pickers.append((row_index, col_index))

        self.num_pickers = pickers

        self.picker_initPos = copy.deepcopy(self.pickers)
        self.drop_offs = copy.deepcopy(self.pickers)









        


   
    def update_grid_with_json(self):
        id_counter = 0
        picker_index = 0

        for row_index, row in enumerate(self.jsonData):
            for col_index, cell in enumerate(row):
                # Lagerplatz (S)
                if "SH" in cell:
                    slot_id = "H" + f"{id_counter +1 :03}"
                    self.grid[row_index, col_index] = slot_id
                    self.storage_ids[row_index, col_index] = slot_id
                    #print("StoargeFound", row_index,  col_index , id_counter, slot_id)
                    id_counter += 1

                elif "SV" in cell:
                    slot_id = "V" + f"{id_counter +1 :03}"
                    self.grid[row_index, col_index] = slot_id
                    self.storage_ids[row_index, col_index] = slot_id
                    #print("StoargeFound", row_index,  col_index , id_counter, slot_id)
                    id_counter += 1

                # Ablageort (D)
                if "D" in cell:
                    drop_id = f"D{picker_index + 1:02}"
                    self.grid[row_index, col_index] = drop_id
                    self.drop_offs[picker_index] = (row_index, col_index)
                    self.pickers[picker_index] = (row_index, col_index)
                    picker_index += 1


        self.num_pickers = (picker_index)
        self.picker_initPos = copy.deepcopy(self.pickers)


    def create_graph_from_json(self):
        graph = {}

        for row in range(self.height):
            for col in range(self.width):
                try:
                    cell = self.grid[row, col]
                except:
                    #print("Row", row, "col", col)
                    continue
                if cell != " . ":  # Nur relevante Zellen betrachten
                    neighbors = []
                    

                    # Verbindungen prüfen
                    if "L" in cell and col > 0:  # Nach links
                        neighbors.append((row, col - 1))
                    if "R" in cell and col < self.width - 1:  # Nach rechts
                        neighbors.append((row, col + 1))
                    if "U" in cell and row < self.height - 1:  # Nach unten
                        neighbors.append((row + 1, col))
                    if "O" in cell and row > 0:  # Nach oben
                        neighbors.append((row - 1, col))

                    # Graph aktualisieren
                    graph[(row, col)] = neighbors

                    if len(neighbors) > 0 and "D" not in cell :
                        self.grid[row, col] = " . " # Flurweg
                    pass    
        self.graph = graph
        #print("Graph erfolgreich aus JSON erstellt.")


    def generate_random_order(self):

        order_size = random.randint(self.min_orders, self.max_orders)
        valid_positions = [(row, col) for row in range(self.height)
                       for col in range(self.width)
                       if ("V" in self.storage_ids[row, col] or "H" in self.storage_ids[row, col]) ]
        #print("self.storage_ids", self.storage_ids)
        return random.sample(valid_positions, order_size)
    

    

    def reset(self):
        """Setzt die Umgebung zurück und gibt die generierten Bestellungen zurück."""
        #random.seed(125)
        self.history = []  # Liste für die gesamte Historie
        self.historyp = []  # Liste für die gesamte Historie der Produkte
        self.grid_static = None
        self.pland_paths = None
        self.wait_times = None

        self.reset_env_based_on_json() 


        self.total_distances = [0] * self.num_pickers
        self.collected_products = [0] * self.num_pickers
        self.delivery_phases = [False] * self.num_pickers

        self.create_graph_from_json()         
        self.update_grid_with_json()       

        # Initialisiere Aufträge und andere Variablen
        self.current_orders = [self.generate_random_order() for _ in range(self.num_pickers)]
        
        # Wartezeiten für jeden Picker
        self.wait_times = {i: 0 for i in range(self.num_pickers)}  

        # Rückgabe der Bestellungen als deepcopy für externe Speicherung
        return [copy.deepcopy(order) for order in self.current_orders], self.get_state_one_hot(), [False] * self.num_pickers
    



   
    def getInit(self):
        return copy.deepcopy(self.current_orders), self.get_state_one_hot(), False
    
    def load_order(self, order):
        """Lädt eine gespeicherte Bestellung in die Umgebung."""
        self.pickers = copy.deepcopy(self.picker_initPos)
        self.current_orders = copy.deepcopy(order)
        self.total_distance = 0
        self.collected_products = 0
        self.delivery_phase = False

    def get_valid_actions_one_hot(self):
        picker_x, picker_y = self.pickers[0]
        valid_actions = [0, 0, 0, 0]  # [Up, Down, Left, Right]

        if (picker_x - 1, picker_y) in self.graph:
            valid_actions[0] = 1
        if (picker_x + 1, picker_y) in self.graph:
            valid_actions[1] = 1
        if (picker_x, picker_y - 1) in self.graph:
            valid_actions[2] = 1
        if (picker_x, picker_y + 1) in self.graph:
            valid_actions[3] = 1

        return valid_actions

    def get_state_one_hot(self):
        """Gibt den State als One-Hot-Encoded-Liste zurück."""
        state = []

        # Produkte in der Nähe von Gängen markieren
        product_positions = set(sum(self.current_orders, []))
        for node in self.graph.keys():
            grid_x, grid_y = node
            left_of_node = (grid_x, grid_y - 1)
            right_of_node = (grid_x, grid_y + 1)

            if left_of_node in product_positions or right_of_node in product_positions:
                state.append(1)
            else:
                state.append(0)

        # Wenn alle Produkte eingesammelt wurden, markiere die Ablageorte
        for picker_id, order in enumerate(self.current_orders):
            if not order:
                drop_off_node = self.drop_offs[picker_id]
                for i, node in enumerate(self.graph.keys()):
                    if node == drop_off_node:
                        state[i] = 1

        # Füge die Positionen aller Picker als One-Hot-Vektoren hinzu
        for picker in self.pickers:
            picker_one_hot = [1 if node == picker else 0 for node in self.graph.keys()]
            state.extend(picker_one_hot)

        return state




    def visualize(self, save_path=None, step=None):
        """
        Visualisiert die aktuelle Umgebung inklusive Grid, Graph, Picker, Produkte und Ablagestationen.
        """
        fig, ax = plt.subplots(figsize=(16, 12))

        # Farben für die Picker
        picker_colors = [
                "#0095fa",  # Blau
                "#369b00",  # Grün
                "#f99b1c",  # Orange
                "#c20000",  # Rot
                "#00bcd4",  # Cyan
                "#7fff00",  # Chartreuse-Grün
                "#ffd700",  # Gold                
                "#ff69b4",  # Pink
                "#8b4513",  # Braun
                "#4b0082"   # Indigo
        ]

        # Zeichne das Grid
        for y in range(self.height):  # Beachte: y wird für die Höhe verwendet
            for x in range(self.width):  # x wird für die Breite verwendet
                rect = mpatches.Rectangle((x, y), 1, 1, linewidth=0.5, edgecolor="#dddddd", facecolor="white")
                ax.add_patch(rect)




        # Zeichne die Produkte als Vierecke
        for picker_id, orders in enumerate(self.current_orders):
            for product in orders:
                py, px = product
                if self.grid[py, px] != " . ":
                    # Anzahl der Picker bestimmt die Größe und Position
                    num_pickers = len(self.pickers)
                    size = 0.6 / num_pickers  # Dynamische Größe basierend auf der Anzahl der Picker
                    picker_index = picker_id  # Nutze Picker-ID für Positionierung
                    offset = (picker_index - num_pickers // 2) * size  # Positionierungsversatz

                    # Berechne die Position des Vierecks
                    rect_x = px + 0.5 - size / 2 + offset
                    rect_y = py + 0.25 - size / 2

                    # Füge das Viereck hinzu
                    rect = mpatches.Rectangle(
                        (rect_x, rect_y), size, size,
                        color=picker_colors[picker_id],
                        alpha=1.0
                    )
                    ax.add_patch(rect)


        # Zeichne die Picker
        for picker_id, picker_pos in enumerate(self.pickers):
            py, px = picker_pos  # Korrektur: Vertausche x und y
            circle = mpatches.Circle((px + 0.5, py + 0.5), 0.4, color=picker_colors[picker_id], label=f"Picker {picker_id}", alpha=0.4)
            ax.add_patch(circle)


        # Zusätzliche Visualisierung für Drop-Zonen
        for picker_id, drop_zone in enumerate(self.drop_offs):
            dy, dx = drop_zone
            rect = mpatches.Rectangle((dx, dy), 1, 1, linewidth=2, edgecolor=picker_colors[picker_id], facecolor=picker_colors[picker_id], alpha=0.3)
            ax.add_patch(rect)


        # Zeichne gerichtete Pfeile für den Graphen
        for node, neighbors in self.graph.items():
            y, x = node  # Korrektur: Vertausche x und y für die Darstellung
            for neighbor in neighbors:
                ny, nx = neighbor  # Korrektur: Vertausche ebenfalls x und y
                
                # Pfeilkörper zeichnen
                plt.arrow(
                    x + 0.5, y + 0.5, (nx - x) * 0.9, (ny - y) * 0.9,  # Verkürzter Pfeil für den Körper
                    head_width=0, head_length=0, fc='#bbbbbb', ec='#bbbbbb', length_includes_head=True
                )
                
                # Pfeilkopf zeichnen
                plt.arrow(
                    x + 0.5 + (nx - x) * 0.9, y + 0.5 + (ny - y) * 0.9,  # Startpunkt des Kopfes
                    (nx - x) * 0.1, (ny - y) * 0.1,  # Kopfanteil
                    head_width=0.1, head_length=0.1, fc='#999999', ec='#999999', length_includes_head=True
                )
                
        # Zeichne die Lagerflächen
        for row in range(self.height):
            for col in range(self.width):
                if "H" in self.storage_ids[row, col] or "V" in self.storage_ids[row, col]:
                    plt.text(
                        col + 0.5, row + 0.5, self.storage_ids[row, col],
                        ha='center', va='center', fontsize=8,
                        bbox=dict(facecolor='white', alpha=0.0, edgecolor='none')
                    )
                if "D" in self.grid[row, col]:
                    plt.text(
                        col + 0.5, row + 0.5, self.grid[row, col],
                        ha='center', va='center', fontsize=8,
                        bbox=dict(facecolor='white', alpha=0.0, edgecolor='none')
                    )



        # Beschriftungen der Zeilen und Spalten
        for row in range(self.height):
            ax.text(-1, row + 0.5, f"{row}", ha="right", va="center", fontsize=8)  # Zeilenbeschriftung (links)
        for col in range(self.width):
            ax.text(col + 0.5, -1, f"{col}", ha="center", va="top", fontsize=8)  # Spaltenbeschriftung (unten)


        # Achsen und Darstellung anpassen
        padding = 1  # Zusätzlicher Platz für bessere Sichtbarkeit
        ax.set_xlim(-padding, self.width + padding)
        ax.set_ylim(-padding, self.height + padding)
        ax.set_aspect('equal', adjustable='box')
        ax.invert_yaxis()  # Invertiere die Y-Achse, um die Darstellung wie bei einem Kartensystem zu machen
        ax.axis('off')

        # Legende
        """
        handles = [mpatches.Patch(color=color, label=f"Picker {i}") for i, color in enumerate(picker_colors)]
        handles += [mpatches.Patch(color=color, alpha=0.5, label=f"Produkte {i}") for i, color in enumerate(picker_colors)]
        plt.legend(handles=handles, loc="upper left", bbox_to_anchor=(1, 1))
        """

        # Speichern oder anzeigen
        if save_path:
            filename = f"{save_path}/warehouse_step_{step:04d}.jpg" if step is not None else f"{save_path}/warehouse.jpg"
            plt.savefig(filename, format='jpg', dpi=300, bbox_inches='tight')
        else:
            plt.show()



    def get_accessible_position(self, target):
        """Gibt die Position zurück, von der aus der Picker das Ziel erreichen kann (links oder rechts daneben)."""
        target_x, target_y = target    
        if ("H" in self.grid[target_x,target_y]):
            adjacent_positions = [
                (target_x, target_y - 1),  # Links
                (target_x, target_y + 1)   # Rechts
            ]
        elif ("V" in self.grid[target_x,target_y]):
            adjacent_positions = [
                (target_x-1, target_y),    # Oben
                (target_x+1, target_y)     # Unten
            ]

        try:
            for pos in adjacent_positions:
                if pos in self.graph:
                    return pos
            print(f"Kein zugänglicher Punkt für das Ziel {target} gefunden!")
        except:
            return None

    def get_start_position(self, picker_id):
        """
        Gibt die definierte Ausgangsposition für einen Picker zurück.
        """
        # Beispiel: Startposition könnte an (0, 0) oder abhängig vom Picker sein
        return self.pickers[picker_id]

    def move_pickers(self, actions):
        """
        Koordiniert die Bewegungen der Picker.
        :param actions: Liste von Bewegungen [(dx, dy), ...] für jeden Picker.
        :return: Aktualisierte Picker-Positionen.
        """


        occupied_slots = set(self.pickers)  # Aktuell belegte Slots
        new_positions = []

        for picker_id, (dx, dy) in enumerate(actions):
            current_pos = self.pickers[picker_id]
            new_pos = (current_pos[0] + dx, current_pos[1] + dy)

            if new_pos in self.graph and new_pos not in occupied_slots:
                # Bewegung ist gültig und Slot ist frei
                new_positions.append(new_pos)
                occupied_slots.remove(current_pos)
                occupied_slots.add(new_pos)
            else:
                # Bewegung nicht möglich, Picker bleibt stehen
                new_positions.append(current_pos)
                if self.drop_offs[picker_id] == new_pos and len(self.current_orders[picker_id]) == 0:  
                    #picker ist bereits in der Ablagepos, weil alles abgearbietet -> wird nicht als warten gewertet 
                    pass
                else:
                    self.wait_times[picker_id] += 1  # Wartezeit erhöhen   
                    #print("Bewegung nicht möglich", current_pos , "->" , new_pos)

        self.pickers = new_positions
        return self.pickers
    
    def get_wait_times(self):
        """
        Gibt die gesammelten Wartezeiten für alle Picker zurück.
        """
        return self.wait_times

    def set_planed_paths(self, pland_paths):
        self.pland_paths = pland_paths

    def execute_plan(self):
        """
        Führt einen Schritt aus, bei dem jeder Picker entlang seines individuellen Pfads bewegt wird.
        Stellt sicher, dass kein Slot von mehreren Pickern gleichzeitig betreten wird.
        """
        occupied_slots = set(self.pickers)  # Aktuell besetzte Slots
        actions = [(0, 0)] * len(self.pickers)  # Bewegungsaktionen der Picker
        step_data = {"step": len(self.history), "pickers": [] }


        #### INIT
        if len(self.history) == 0:
            # Für den Export aufarbeiten
            # Für den Init-den neuen Zustand
            for picker_id, picker_pos in enumerate(self.pickers):
                step_data["pickers"].append({"id": picker_id, "pos": picker_pos, "orders": copy.deepcopy(self.current_orders[picker_id])})
            
            # Hinzufügen des ersten schritts
            self.history.append(step_data)
            # Stepdata nochmal aktualsieren
            step_data = {"step": len(self.history), "pickers": [] }

        ## Abarbeiten
        for picker_id, path in enumerate(self.pland_paths):
            if not path:
                continue  # Kein Pfad mehr für diesen Picker

            next_pos = path[0]
            current_pos = self.pickers[picker_id]


            # Überprüfen, ob ein Produkt eingesammelt werden kann
            for product in self.current_orders[picker_id]:
                if self.get_accessible_position(product) == next_pos:
                    # Ausgabe zum debuggen: 
                    #print(f"Picker {picker_id} hat Produkt bei {product} aufgenommen.")
                    self.current_orders[picker_id].remove(product)
                    break

            if next_pos not in occupied_slots:
                # Bewegung erlauben, wenn Slot nicht besetzt
                dx = next_pos[0] - current_pos[0]
                dy = next_pos[1] - current_pos[1]
                actions[picker_id] = (dx, dy)

                occupied_slots.remove(current_pos)
                occupied_slots.add(next_pos)
                self.pland_paths[picker_id].pop(0)  # Entferne besuchten Slot vom Pfad


        # Führe Bewegungen aus
        self.move_pickers(actions)

        # Für den Export aufarbeiten
        # Speichere den neuen Zustand
        for picker_id, picker_pos in enumerate(self.pickers):
            step_data["pickers"].append({"id": picker_id, "pos": picker_pos, "orders": copy.deepcopy(self.current_orders[picker_id])})

            

        self.history.append(step_data)

    def export_json(self, filename="simulation.json"):
        """Exportiert das gesamte Grid und die Historie der Simulation als JSON"""

        if self.grid_static is None:
            # Erstelle eine leere Grid-Matrix
            self.grid_static = [[""] * self.width for _ in range(self.height)]

            for row_index, row in enumerate(self.jsonData):
                for col_index, cell in enumerate(row):
                    # Flurweg (Leerzeichen mit Richtungsangaben)
                    self.grid_static[row_index][col_index] = cell.strip()


        data = {
            "grid": self.grid_static,
            "history": self.history
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

