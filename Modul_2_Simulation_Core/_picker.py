class PickerCoordinator:
    def __init__(self, env):
        """
        Initialisiert den Koordinator.
        :param env: Instanz der WarehouseEnv-Umgebung.
        """
        self.env = env
        self.paths = [[] for _ in range(env.num_pickers)]  # Geplante Routen für jeden Picker

    def plan_routes(self):
        """
        Plant vollständige Pfade für alle Picker.
        """
        for picker_id, order in enumerate(self.env.current_orders):
            current_pos = self.env.pickers[picker_id]
            path = []

            for target in order:
                accessible_pos = self.env.get_accessible_position(target)
                if accessible_pos:
                    path += self.find_path(current_pos, accessible_pos)
                    current_pos = accessible_pos

            # Ziel: Rückkehr zur Drop-Zone
            drop_zone = self.env.drop_offs[picker_id]
            path += self.find_path(current_pos, drop_zone)

            self.paths[picker_id] = path

        #print("Paths:", self.paths)

    
    def find_path(self, start, goal):
        """
        Berechnet den kürzesten Pfad zwischen Start und Ziel mit A*.
        :param start: Startposition (x, y).
        :param goal: Zielposition (x, y).
        :return: Liste von Positionen [(x1, y1), (x2, y2), ...] für den Pfad.
        """
        from heapq import heappop, heappush

        open_set = []
        heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heappop(open_set)

            if current == goal:
                # Rekonstruiere den Pfad
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]  # Pfad umkehren

            for neighbor in self.env.graph.get(current, []):
                tentative_g_score = g_score[current] + 1  # Abstand zwischen zwei Knoten = 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    heappush(open_set, (tentative_g_score, neighbor))

        print(f"Kein Pfad von {start} nach {goal} gefunden!")
        return []

   
    def execute_step(self):
        """
        Führt einen Simulationsschritt aus, behandelt Konflikte und aktualisiert Bestellungen sowie GUI.
        """
        occupied_slots = set(self.env.pickers)  # Aktuell belegte Slots
        actions = [(0, 0)] * len(self.env.pickers)  # Standardaktionen: Stehenbleiben
        executed = [False] * len(self.env.pickers)  # Verfolgung, ob ein Picker seine Aktion ausgeführt hat

        while not all(executed):  # Schleife, bis alle Picker ihren Schritt gemacht haben oder warten
            for picker_id, path in enumerate(self.paths):
                if executed[picker_id]:
                    continue  # Picker hat bereits seinen Schritt gemacht

                # Prüfen, ob die Bestellung leer ist
                if not self.env.current_orders[picker_id]:
                    if not self.env.delivery_phases[picker_id]:
                        # Planung der Route zur Drop-Zone
                        drop_zone = self.env.drop_offs[picker_id]
                        self.paths[picker_id] = self.find_path(self.env.pickers[picker_id], drop_zone)
                        self.env.delivery_phases[picker_id] = True
                    # Falls die Drop-Zone bereits erreicht wurde, bleibt der Picker stehen
                    if not path:
                        executed[picker_id] = True
                        continue

                # Falls Produkte vorhanden sind, prüfe und entferne sie
                if path:
                    next_pos = path[0]
                    current_pos = self.env.pickers[picker_id]

                    # Prüfen, ob die nächste Position blockiert ist
                    if next_pos in occupied_slots:
                        # Ausgabe zum debuggen: 
                        #print(f"Konflikt für Picker {picker_id} bei Position {next_pos}.")
                        executed[picker_id] = True  # Picker wartet
                        continue

                    # Überprüfen, ob ein Produkt eingesammelt werden kann
                    for product in self.env.current_orders[picker_id]:
                        if self.env.get_accessible_position(product) == next_pos:
                            # Ausgabe zum debuggen: 
                            #print(f"Picker {picker_id} hat Produkt bei {product} aufgenommen.")
                            self.env.current_orders[picker_id].remove(product)
                            break

                    # Bewegung ausführen
                    dx = next_pos[0] - current_pos[0]
                    dy = next_pos[1] - current_pos[1]
                    actions[picker_id] = (dx, dy)
                    occupied_slots.remove(current_pos)
                    occupied_slots.add(next_pos)

                    # Aktualisieren
                    self.paths[picker_id].pop(0)
                    executed[picker_id] = True
                else:
                    executed[picker_id] = True  # Keine Bewegung möglich, Picker bleibt stehen
        # Abschließend die Actionen ausführen
        self.env.move_pickers(actions)
