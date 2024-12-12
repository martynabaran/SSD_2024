import pygame
import random
from random import choices
import numpy as np
from settings import *
from auxiliary import *
import heapq
import math


class Agent(pygame.sprite.Sprite):
    def __init__(self, identifier, layout, exits, health, risk, communicates, strategy, color):
        pygame.sprite.Sprite.__init__(self)
        self.image  = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect()


        self.id           = identifier
        self.health       = health
        self.risk         = risk
        self.communicates = communicates
        self.layout       = layout
        self.plan         = []
        self.exits        = exits
        self.danger       = False
        self.reconsider   = False
        self.dead         = False
        self.range        = VIS_RANGE
        self.volume       = VOL_RANGE
        self.relatives = []
        self.strategy = strategy

        self.x = random.randrange(0, len(self.layout))
        self.y = random.randrange(0, len(self.layout[0]))

        while(isWall(self.layout,self.x,self.y) or isAlarm(self.layout, self.x,self.y) or isExit(layout, self.x, self.y)):
            self.x = random.randrange(0, len(self.layout))
            self.y = random.randrange(0, len(self.layout[0]))

        self.new_x = -1
        self.new_y = -1

    def getPosition(self):
        return [self.x, self.y]

    def getNewPosition(self):
        return [self.new_x, self.new_y]
    
    def getID(self):
        return self.id
    
    def getLayout(self):
        return self.layout
    
    def updateLayout(self, x, y, layout):
        self.layout[x][y] = layout

    def getRelatives(self):
        return self.relatives
    def getHealth(self):
        return self.health

    def getVolume(self):
        return self.volume
    
    def setHealth(self, new_health):
        self.health = new_health

    def setColor(self, color):
        self.image.fill(color)
    
    def setRange(self, new_range):
        self.range = new_range
    
    def setVolume(self, new_volume):
        self.volume =  new_volume
        
    def move(self, dx=0, dy=0):
        self.x += dx
        self.y += dy

    def die(self):
        self.dead = True

    def isDead(self):
        return self.dead

    def isCommunicative(self):
        return self.communicates

    def getDangerState(self):
        return self.danger

    def setDangerState(self, state):
        self.danger = state

    def update(self, all_agents):
        if not self.dead:
            print(f"[DEBUG] Updating agent {self.id}: Current position: ({self.x}, {self.y}), Plan: {self.plan}")
            if self.plan and len(self.plan) > 0:
                self.new_x = self.plan[0][0]
                self.new_y = self.plan[0][1]

                for agent in all_agents:
                    if not agent.isDead() and agent.getPosition() == [self.new_x, self.new_y] and not agent.getNewPosition() == [self.x, self.y]:
                        print(f"[DEBUG] Agent {self.id}: Conflict detected with agent {agent.id} at ({self.new_x}, {self.new_y})")
                        return

                self.move(dx=(self.new_x - self.x), dy=(self.new_y - self.y))
                print(f"[DEBUG] Agent {self.id}: Moved to ({self.x}, {self.y})")
                self.plan = self.plan[1:]
                self.rect.x = self.x * TILESIZE
                self.rect.y = self.y * TILESIZE

    def checkAlarm(self, alarm):
        print(f"[DEBUG] Agent {self.id}: Checking alarm, Alarm state: {alarm}, Danger state: {self.danger}")
        if alarm and not self.danger:
            self.danger = True
            self.reconsider = True

    def receiveMessage(self, message):
        print(f"[DEBUG] Agent {self.id}: Receiving message")
        for i in range(len(message)):
            for j in range(len(message[i])):
                if self.layout[i][j] != message[i][j] and (isFire(message, i, j) or isSmoke(message, i, j)):
                    print(f"[DEBUG] Agent {self.id}: Danger detected at ({i}, {j})")
                    self.danger = True
                    self.reconsider = True
                    self.layout[i][j] = message[i][j]



    def moveRandom(self):
        print("DEBUG: move random")
        row  = [-1, 0, 0, 1]
        col  = [0, -1, 1, 0]
        move = [True, False]
        prob = [1/self.id, 1-(1/self.id)]
        if (choices(move, prob)):
            i = random.randrange(0, 4)
            x = self.x + row[i]
            y = self.y + col[i]
            if (not isWall(self.layout,x,y) and not isFire(self.layout,x,y) and not isSmoke(self.layout,x,y) and not isExit(self.layout,x,y) and not isAlarm(self.layout,x,y)):
                return [[x, y]]
        return [[self.x, self.y]]
    def percept(self, layout):
        print(f"[DEBUG] Agent {self.id}: Perceiving environment")
        x0 = max(self.x - self.range, 0)
        y0 = max(self.y - self.range, 0)
        x1 = min(self.x + self.range, len(layout) - 1)
        y1 = min(self.y + self.range, len(layout[0]) - 1)

        self.reconsider = False
        for i in range(x0, x1 + 1):
            for j in range(y0, y1 + 1):
                if self.layout[i][j] != layout[i][j]:
                    print(f"[DEBUG] Agent {self.id}: Detected change at ({i}, {j})")
                    self.danger = True
                    self.reconsider = True
                    self.layout[i][j] = layout[i][j]

    def plan_(self, all_agents):
        print(f"[DEBUG] Agent {self.id}: Planning, Danger: {self.danger}, Reconsider: {self.reconsider}")
        if not self.danger:
            self.plan = self.moveRandom()
            print(f"[DEBUG] Agent {self.id}: Random move plan: {self.plan}")
        elif self.reconsider:
            if self.strategy == "nearest_exit":
                self.plan = self.Dijkstra()
            elif self.strategy == "safest_exit":
                danger_sources = self.get_danger_sources()
                self.plan = self.Dijkstra_safest(danger_sources)
            elif self.strategy == "least_crowded_exit":
                self.plan = self.move_to_least_crowded_exit(all_agents)
            else:
                self.plan = self.Dijkstra()
            print(f"[DEBUG] Agent {self.id}: Planned path: {self.plan}")

    def panic(self):
        print(f"[DEBUG] Agent {self.id}: Panic mode activated")
        #search for a free adjacent cell. if there's none, search for a cell with smoke. if there's none, give up :(
        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        combined = list(zip(row, col))
        random.shuffle(combined)
        row, col = zip(*combined)
        
        for i in range(len(row)):
            x = self.x + row[i]
            y = self.y + col[i]
            if (not isWall(self.layout,x,y) and not isFire(self.layout,x,y) and not isSmoke(self.layout,x,y) and not isAlarm(self.layout,x,y)):
                print(f"[DEBUG] Agent {self.id}: Found free cell at ({x}, {y})")
                return [[x,y]]
        for i in range(len(row)):
            x = self.x + row[i]
            y = self.y + col[i]
            if (isSmoke(self.layout,x,y)):
                print(f"[DEBUG] Agent {self.id}: No free cell, moving to smoke cell at ({x}, {y})")
                return [[x,y]]
        print(f"[DEBUG] Agent {self.id}: No options left, staying at current position ({self.x}, {self.y})")
        return [[self.x,self.y]] #desisti

    def Dijkstra(self):
        print(f"[DEBUG] Agent {self.id}: Starting Dijkstra's algorithm")
        source = [self.x, self.y]
        dests = self.exits

        if source in dests:
            print(f"[DEBUG] Agent {self.id}: Already at an exit")
            return [source]

        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]
        
        queue = []
        my_dest = []
        visited = []
        parents = {}
        distance = {}
        enqueued = {}

        for i in range(len(self.layout)):
            visit = []
            for j in range(len(self.layout[0])):
                visit.append(0)
                parents[(i, j)] = None
                distance[(i, j)] = math.inf
                enqueued[(i, j)] = None
            visited.append(visit)

        heapq.heappush(queue, [0, source[0], source[1]])
        distance[tuple(source)] = 0
        enqueued[tuple(source)] = True
        visited[source[0]][source[1]] = 1

        while queue:
            cur = heapq.heappop(queue)
            parent = (cur[1], cur[2])

            if not enqueued[parent]:
                continue

            enqueued[parent] = False

            if list(parent) in dests:
                print(f"[DEBUG] Agent {self.id}: Destination reached: {parent}")
                my_dest = list(parent)
                break

            combined = list(zip(row, col))
            random.shuffle(combined)
            row, col = zip(*combined)

            for i in range(len(row)):
                x, y = parent[0] + row[i], parent[1] + col[i]
                if x < 0 or y < 0 or x >= len(self.layout) or y >= len(self.layout[0]):
                    continue

                if enqueued[(x, y)] is False:
                    continue

                if not isWall(self.layout, x, y) and not isFire(self.layout, x, y) and not isAlarm(self.layout, x, y) and visited[x][y] == 0:
                    visited[x][y] = 1

                    weight = 1
                    if isSmoke(self.layout, x, y):
                        weight += 1 - self.risk

                    alternative = distance[parent] + weight

                    if alternative < distance[(x, y)]:
                        distance[(x, y)] = alternative
                        parents[(x, y)] = list(parent)
                        heapq.heappush(queue, [alternative, x, y])
                        enqueued[(x, y)] = True

        if not my_dest:
            print(f"[DEBUG] Agent {self.id}: No path to exit found, triggering panic")
            return self.panic()

        path = []
        at = my_dest
        while at != source:
            path.append(at)
            at = parents[tuple(at)]

        path.reverse()
        print(f"[DEBUG] Agent {self.id}: Path found: {path}")
        return path
    

    def calculate_crowdedness_and_danger(self, exits, agents, radius):
        crowdedness = {}
        danger_level = {}  # Nowa struktura danych do śledzenia zagrożenia
        print("Obliczanie zatłoczenia i poziomu zagrożenia...")
        for exit in exits:
            exit = tuple(exit)
            x_exit, y_exit = exit
            crowdedness[exit] = 0
            danger_level[exit] = 0

            for agent in agents:
                if not agent.isDead():
                    x_agent, y_agent = agent.getPosition()
                    if abs(x_agent - x_exit) <= radius and abs(y_agent - y_exit) <= radius:
                        crowdedness[exit] += 1

            # Oblicz poziom zagrożenia w promieniu wokół wyjścia
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x, y = x_exit + dx, y_exit + dy
                    if 0 <= x < len(self.layout) and 0 <= y < len(self.layout[0]):
                        if isFire(self.layout, x, y):
                            danger_level[exit] += 10  # Wysoka kara za ogień
                        elif isSmoke(self.layout, x, y):
                            danger_level[exit] += 5  # Niższa kara za dym

            print(f"Wyjście {exit}: Zatłoczenie={crowdedness[exit]}, Zagrożenie={danger_level[exit]}")

        return crowdedness, danger_level

    # def move_to_least_crowded_exit(self, all_agents):
    #     try:
    #         # Oblicz zatłoczenie i zagrożenie
    #         crowdedness, danger_level = self.calculate_crowdedness_and_danger(self.exits, all_agents, radius=5)
    #         print(f"Zatłoczenie: {crowdedness}")
    #         print(f"Poziom zagrożenia: {danger_level}")
            
    #         # Połącz obie metryki z uwzględnieniem ryzyka agenta
    #         combined_score = {
    #             exit: crowdedness[exit] + danger_level[exit] 
    #             for exit in crowdedness
    #         }
    #         print(f"Połączone wyniki: {combined_score}")
            
    #         # Znajdź wyjście o najmniejszym łącznym wyniku
    #         least_crowded_exit_x, least_crowded_exit_y = min(combined_score, key=combined_score.get)
    #         print(f"Najlepsze wyjście: {least_crowded_exit_x}, {least_crowded_exit_y}")
            
    #         # Wyznacz ścieżkę do wyjścia
    #         path = self.DijkstraToTarget(least_crowded_exit_x, least_crowded_exit_y)
    #         if path is None:
    #             print("DijkstraToTarget zwróciła None. Próbuję najbliższego wyjścia.")
    #             return self.Dijkstra()
    #         print(f"Ścieżka do wyjścia: {path}")
    #         return path
    #     except Exception as e:
    #         print(f"Błąd w move_to_least_crowded_exit: {e}")
    #         return []
    def move_to_least_crowded_exit(self, all_agents):
        try:
            # Oblicz zatłoczenie i zagrożenie
            crowdedness, danger_level = self.calculate_crowdedness_and_danger(self.exits, all_agents, radius=5)
            print(f"Zatłoczenie: {crowdedness}")
            print(f"Poziom zagrożenia: {danger_level}")
             # Pozycja agenta
            x_agent, y_agent = self.getPosition()
            
            # Oblicz odległości do każdego wyjścia
            distances = {
                tuple(exit): ((x_agent - exit[0]) ** 2 + (y_agent - exit[1]) ** 2) ** 0.5
                for exit in self.exits
            }
            print(f"Odległości agenta {self.getID()} do wyjść: {distances}")
            
            # Definiujemy wagi dla skumulowanego score
            w_crowdedness = 2.5
            w_danger = 2.5
            w_distance = 1.5

            # Oblicz znormalizowane wartości dla wszystkich wyjść
            max_crowdedness = max(max(crowdedness.values(), default=1),1)  # Poprawka tutaj
            max_danger = max(max(danger_level.values(), default=1),1)     # Poprawka tutaj
            max_distance = max(max(distances.values(), default=1), 1)   
            scores = {}
            for exit in self.exits:
                exit_tuple = tuple(exit)
                if distances[exit_tuple] <= 10 and danger_level[exit_tuple] < 200:
                    self.DijkstraToTarget([exit])
                    return
                score = (
                    w_crowdedness * (crowdedness[exit_tuple] / max_crowdedness) +
                    w_danger * (danger_level[exit_tuple] / max_danger) +
                    w_distance * (distances[exit_tuple] / max_distance)
                )
                scores[exit_tuple] = score

            # Posortuj wyjścia według skumulowanego wyniku (score)
            sorted_exits = sorted(self.exits, key=lambda exit: scores[tuple(exit)])
            print(f"Agent  {self.getID()} - Posortowane wyjścia według score: {sorted_exits}")
        
            # Posortuj wyjścia według zatłoczenia i zagrożenia
            # sorted_exits = sorted(
            #     self.exits,
            #     key=lambda exit: (crowdedness[tuple(exit)], danger_level[tuple(exit)])
            # )
            # print(f"Posortowane wyjścia: {sorted_exits}")
            
            # Przekaż posortowaną listę do DijkstraToTarget
            path = self.DijkstraToTarget(sorted_exits)
            if not path:
                print("DijkstraToTarget nie znalazła ścieżki. Wchodzę w tryb paniki.")
                return self.panic()
            print(f"Ścieżka do wyjścia: {path}")
            return path
        except Exception as e:
            print(f"Błąd w move_to_least_crowded_exit: {e}")
            return []


    def DijkstraToTarget(self, sorted_exits):
        print(f"Rozpoczynam DijkstraToTarget dla posortowanych wyjść: {sorted_exits}")
        source = [self.x, self.y]
        if source in sorted_exits:
            return [source]
        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        queue = []
        visited = []
        parents = dict()
        distance = dict()
        enqueued = dict()

        for i in range(len(self.layout)):
            visit = []
            for j in range(len(self.layout[0])):
                visit.append(0)
                parents[(i, j)] = None
                distance[(i, j)] = math.inf
                enqueued[(i, j)] = None
            visited.append(visit)

        queue = [[0, source[0], source[1]]]
        heapq.heapify(queue)
        distance[tuple(source)] = 0
        enqueued[tuple(source)] = True
        visited[source[0]][source[1]] = 1

        for target in sorted_exits:
            target = tuple(target)
            print(f"Próba dotarcia do wyjścia: {target}")
            while queue:
                cur = heapq.heappop(queue)
                parent = (cur[1], cur[2])
                if not enqueued[parent]:
                    continue

                enqueued[parent] = False

                if list(parent) == list(target):
                    print(f"Dotarłem do wyjścia: {target}")
                    path = []
                    at = list(target)
                    while at != source:
                        path.append(at)
                        at = parents[tuple(at)]

                    path.reverse()
                    print(f"Ścieżka do wyjścia {target}: {path}")
                    return path

                for i in range(len(row)):
                    x, y = parent[0] + row[i], parent[1] + col[i]
                    if (
                        x < 0
                        or y < 0
                        or x >= len(self.layout)
                        or y >= len(self.layout[0])
                    ):
                        continue

                    if enqueued[(x, y)] == False:
                        continue

                    if not isWall(self.layout, x, y) and not isFire(self.layout, x, y) and not isAlarm(self.layout, x, y) and visited[x][y] == 0:
                        visited[x][y] = 1
                        weight = 1
                        if isSmoke(self.layout, x, y):
                            weight += 1 - self.risk

                        alternative = distance[parent] + weight

                        if alternative < distance[(x, y)]:
                            distance[(x, y)] = alternative
                            parents[(x, y)] = list(parent)
                            heapq.heappush(queue, [alternative, x, y])
                            enqueued[(x, y)] = True

            # Jeśli nie znaleziono ścieżki do bieżącego wyjścia, spróbuj kolejnego
            print(f"Nie udało się dotrzeć do wyjścia: {target}, próba kolejnego.")
            continue

        print("Nie udało się dotrzeć do żadnego wyjścia. Wchodzę w tryb paniki.")
        return self.panic()


    # def DijkstraToTarget(self, targetX, targetY):
    #     print(f"Rozpoczynam DijkstraToTarget do celu ({targetX}, {targetY})")
    #     source = [self.x, self.y]
    #     dest = [targetX, targetY]

    #     if source == list(dest):
    #         print("Już jesteś w miejscu docelowym.")
    #         return [source]

    #     row = [-1, 0, 0, 1]
    #     col = [0, -1, 1, 0]

    #     queue = []
    #     visited = []
    #     parents = dict()
    #     distance = dict()
    #     enqueued = dict()

    #     for i in range(len(self.layout)):
    #         visit = []
    #         for j in range(len(self.layout[0])):
    #             visit.append(0)
    #             parents[(i, j)] = None
    #             distance[(i, j)] = math.inf
    #             enqueued[(i, j)] = None
    #         visited.append(visit)

    #     queue = [[0, source[0], source[1]]]
    #     heapq.heapify(queue)
    #     distance[tuple(source)] = 0
    #     enqueued[tuple(source)] = True
    #     visited[source[0]][source[1]] = 1

    #     while len(queue) > 0:
    #         cur = heapq.heappop(queue)
    #         parent = (cur[1], cur[2])
    #         # print(f"Odwiedzam wierzchołek: {parent} z odległością {cur[0]}")

    #         if not enqueued[parent]:
    #             continue

    #         enqueued[parent] = False

    #         if list(parent) == list(dest):
    #             print("Dotarłem do celu!")
    #             break

    #         combined = list(zip(row, col))
    #         random.shuffle(combined)
    #         row, col = zip(*combined)

    #         for i in range(len(row)):
    #             x, y = parent[0] + row[i], parent[1] + col[i]
    #             if (
    #                 x < 0
    #                 or y < 0
    #                 or x >= len(self.layout)
    #                 or y >= len(self.layout[0])
    #             ):
    #                 continue

    #             if enqueued[(x, y)] == False:
    #                 continue

    #             if not isWall(self.layout, x, y) and not isFire(self.layout, x, y) and not isAlarm(self.layout, x, y) and visited[x][y] == 0:
    #                 visited[x][y] = 1
    #                 weight = 1
    #                 if isSmoke(self.layout, x, y):
    #                     weight += 1 - self.risk

    #                 alternative = distance[parent] + weight

    #                 if alternative < distance[(x, y)]:
    #                     distance[(x, y)] = alternative
    #                     parents[(x, y)] = list(parent)
    #                     heapq.heappush(queue, [alternative, x, y])
    #                     enqueued[(x, y)] = True

    #     if not visited[dest[0]][dest[1]]:
    #         print("Nie mogę znaleźć ścieżki. Wchodzę w tryb paniki.")
    #         return self.panic()

    #     path = []
    #     at = list(dest)
    #     while at != source:
    #         path.append(at)
    #         at = parents[tuple(at)]

    #     path.reverse()
    #     print(f"Wyznaczona ścieżka: {path}")
    #     return path

    def Dijkstra_safest(self, danger_sources):
        source = [self.x, self.y]
        dests = self.exits

        if source in dests:
            return [source]

        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        queue = []
        my_dest = []
        visited = []
        parents = dict()
        distance = dict()
        enqueued = dict()

        # Initialize grids
        for i in range(len(self.layout)):
            visit = []
            for j in range(len(self.layout[0])):
                visit.append(0)
                parents[(i, j)] = None
                distance[(i, j)] = math.inf
                enqueued[(i, j)] = None
            visited.append(visit)

        # Add starting node
        queue = [[0, source[0], source[1]]]
        heapq.heapify(queue)
        distance[tuple(source)] = 0
        enqueued[tuple(source)] = True
        visited[source[0]][source[1]] = 1

        while len(queue) > 0:
            cur = heapq.heappop(queue)
            parent = (cur[1], cur[2])

            if not enqueued[parent]:
                continue

            enqueued[parent] = False

            if list(parent) in dests:
                my_dest = list(parent)
                break

            # Shuffle visiting order
            combined = list(zip(row, col))
            random.shuffle(combined)
            row, col = zip(*combined)

            for i in range(len(row)):
                x, y = parent[0] + row[i], parent[1] + col[i]
                if x < 0 or y < 0 or x >= len(self.layout) or y >= len(self.layout[0]):
                    continue

                if enqueued[(x, y)] == False:
                    continue

                if not isWall(self.layout, x, y) and visited[x][y] == 0:
                    visited[x][y] = 1

                    # Calculate cost
                    weight = 1
                    if isSmoke(self.layout, x, y):
                        weight += 1 - self.risk

                    # # Add safety factor
                    # safety_factor = min(
                    #     [math.sqrt((x - sx) ** 2 + (y - sy) ** 2) for sx, sy in danger_sources]
                    # )
                    if danger_sources:
                        safety_factor = min(
                            [math.sqrt((x - sx) ** 2 + (y - sy) ** 2) for sx, sy in danger_sources]
                        )
                    else:
                        safety_factor = float('inf')
                    weight += 1 / max(safety_factor, 0.1)  # Avoid division by zero

                    alternative = distance[parent] + weight

                    if alternative < distance[(x, y)]:
                        distance[(x, y)] = alternative
                        parents[(x, y)] = list(parent)
                        heapq.heappush(queue, [alternative, x, y])
                        enqueued[(x, y)] = True

        # if not my_dest:
        #     return self.panic()
        panic = True
        for dest in dests:
            if visited[dest[0]][dest[1]]:
                panic = False

        if panic:
            return self.panic()
        
        path = []
        at = my_dest
        while at != source:
            path.append(at)
            at = parents[tuple(at)]

        path.reverse()
        return path

    def get_danger_sources(self):
        danger_sources = []
        for i in range(len(self.layout)):
            for j in range(len(self.layout[0])):
                if isFire(self.layout, i, j) or isSmoke(self.layout, i, j):  # Definiowanie zagrożenia
                    danger_sources.append((i, j))
        if not danger_sources:
            print("Nie znaleziono zagrożeń w layout!")
        return danger_sources


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = self.x * TILESIZE 
        self.rect.y = self.y * TILESIZE

class Alarm(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image  = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE

    def CheckAlarm(self, layout):
        x0 = self.x - ALARMRANGE
        y0 = self.y - ALARMRANGE 
        x1 = self.x + ALARMRANGE
        y1 = self.y + ALARMRANGE

        for i in range(x0, x1+1):
            for j in range(y0, y1+1):
                if(isSmoke(layout, i, j) or isFire(layout, i, j)):
                    return True
        return False
    
    def FireAlarm(self):
        self.image.fill(RED)


class Fire(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(ORANGE)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = self.x * TILESIZE 
        self.rect.y = self.y * TILESIZE

class Smoke(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREY)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = self.x * TILESIZE 
        self.rect.y = self.y * TILESIZE