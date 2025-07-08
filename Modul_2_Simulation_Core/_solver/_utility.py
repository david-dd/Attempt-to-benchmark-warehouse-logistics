import heapq

def identify_aisles(env):
    """
    Identifiziert die horizontalen (SH) und vertikalen (SV) Gänge basierend auf den Lagerplätzen.
    :param env: Instanz der WarehouseEnv-Umgebung.
    :return: Dictionary mit zwei Schlüsseln: "horizontal" und "vertical",
             die jeweils Listen von Gängen enthalten.
    """
    horizontal_aisles = []
    vertical_aisles = []

    for row in range(env.height):
        horizontal_aisle = []
        for col in range(env.width):
            if "V" in env.storage_ids[row, col]:
                horizontal_aisle.append((row, col))
        if horizontal_aisle:
            horizontal_aisles.append(horizontal_aisle)

    for col in range(env.width):
        vertical_aisle = []
        for row in range(env.height):
            if "H" in env.storage_ids[row, col]:
                vertical_aisle.append((row, col))
        if vertical_aisle:
            vertical_aisles.append(vertical_aisle)

    return {"horizontal": horizontal_aisles, "vertical": vertical_aisles}


def cluster_aisles(aisles):
    """
    Gruppiert die Gänge in Cluster basierend auf der Nähe.
    :param aisles: Dictionary mit horizontalen und vertikalen Gängen.
    :return: Liste von Clustern, jedes Cluster enthält Gänge, die nah beieinander liegen.
    """
    clusters = []
    for direction in ["horizontal", "vertical"]:
        aisle_list = aisles[direction]
        used = set()

        for i, aisle in enumerate(aisle_list):
            if i in used:
                continue
            cluster = [aisle]
            used.add(i)

            for j, other_aisle in enumerate(aisle_list):
                if j in used:
                    continue
                if are_aisles_close(aisle, other_aisle):
                    cluster.append(other_aisle)
                    used.add(j)
            clusters.append(cluster)
    return clusters


def are_aisles_close(aisle1, aisle2):
    """
    Prüft, ob zwei Gänge nah genug sind, um sie zu gruppieren.
    :param aisle1: Erster Gang (Liste von Slots).
    :param aisle2: Zweiter Gang (Liste von Slots).
    :return: True, wenn die Gänge nah genug sind, sonst False.
    """
    midpoint1 = aisle1[len(aisle1) // 2]
    midpoint2 = aisle2[len(aisle2) // 2]
    return manhattan_distance(midpoint1, midpoint2) <= 2


def find_path(env, start, goal):
    """
    Berechnet den kürzesten Pfad zwischen Start und Ziel mit A*.
    :param env: Instanz der WarehouseEnv-Umgebung.
    :param start: Startposition (x, y).
    :param goal: Zielposition (x, y).
    :return: Liste von Positionen [(x1, y1), (x2, y2), ...] für den Pfad.
    """
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]

        for neighbor in env.graph.get(current, []):
            tentative_g_score = g_score[current] + 1
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                heapq.heappush(open_set, (tentative_g_score, neighbor))
    return []


def manhattan_distance(pos1, pos2):
    """
    Berechnet die Manhattan-Distanz zwischen zwei Positionen.
    :param pos1: Erste Position (x1, y1).
    :param pos2: Zweite Position (x2, y2).
    :return: Manhattan-Distanz.
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


