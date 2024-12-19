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
        self.rescue_counter = 0
        self.x = random.randrange(0, len(self.layout))
        self.y = random.randrange(0, len(self.layout[0]))

        while(isWall(self.layout,self.x,self.y) or isAlarm(self.layout, self.x,self.y) or isExit(layout, self.x, self.y)):
            self.x = random.randrange(0, len(self.layout))
            self.y = random.randrange(0, len(self.layout[0]))

        self.new_x = -1
        self.new_y = -1
        self.saved_at = -1
        self.partial_x = 0.0
        self.partial_y = 0.0
        self.age = random.randint(1, 80)  # Wiek od 1 do 80 lat
        self.speed = self.calculate_speed()
        self.rescue_relatives = False
        self.synchronized_exit = False

    def calculate_speed(self):
        """Oblicza prędkość agenta na podstawie wieku."""
        if self.age > 60:  # Starsi
            return 1.0  # Poruszają się wolniej
        else:  # Dorośli
            return 1.1


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
        # self.x += dx
        # self.y += dy
        
        self.partial_x += dx* self.speed
        self.partial_y += dy * self.speed
        move_x = int(self.partial_x)
        move_y = int(self.partial_y)
        # print(f"agent: {self.getID()}, wiek: {self.age} - move ({move_x}, {move_y})")
        if abs(move_x) > 0 or abs(move_y) > 0:
            print(f"porusza się agent: {self.getID()}, wiek: {self.age} move ({move_x}, {move_y})")
            self.partial_x -= move_x
            self.partial_y -= move_y
            self.x += move_x
            self.y += move_y
        else:
            print(f"NIE porusza, agent: {self.getID()}, wiek: {self.age}, move ({move_x}, {move_y})")
        

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
            # print(f"[DEBUG] Updating agent {self.id}: Current position: ({self.x}, {self.y}), Plan: {self.plan}")
            if self.plan and len(self.plan) > 0:
                self.new_x = self.plan[0][0]
                self.new_y = self.plan[0][1]

                for agent in all_agents:
                    if not agent.isDead() and agent.getPosition() == [self.new_x, self.new_y] and not agent.getNewPosition() == [self.x, self.y]:
                        # print(f"[DEBUG] Agent {self.id}: Conflict detected with agent {agent.id} at ({self.new_x}, {self.new_y})")
                        return

                self.move(dx=(self.new_x - self.x), dy=(self.new_y - self.y))
                # print(f"[DEBUG] Agent {self.id}: Moved to ({self.x}, {self.y})")
                self.plan = self.plan[1:]
                self.rect.x = self.x * TILESIZE
                self.rect.y = self.y * TILESIZE

    def checkAlarm(self, alarm):
        # print(f"[DEBUG] Agent {self.id}: Checking alarm, Alarm state: {alarm}, Danger state: {self.danger}")
        if alarm and not self.danger:
            self.danger = True
            self.reconsider = True

    def receiveMessage(self, message):
        # print(f"[DEBUG] Agent {self.id}: Receiving message")
        for i in range(len(message)):
            for j in range(len(message[i])):
                if self.layout[i][j] != message[i][j] and (isFire(message, i, j) or isSmoke(message, i, j)):
                    # print(f"[DEBUG] Agent {self.id}: Danger detected at ({i}, {j})")
                    self.danger = True
                    self.reconsider = True
                    self.layout[i][j] = message[i][j]



    def moveRandom(self):
        # print("DEBUG: move random")
        row  = [-1, 0, 0, 1]
        col  = [0, -1, 1, 0]
        move = [True, False]
        prob = [1/self.id, 1-(1/self.id)]
        if (choices(move, prob)):
            i = random.randrange(0, 4)
            self.partial_x += row[i] * self.speed
            self.partial_y += col[i] * self.speed
            move_x = int(self.partial_x)
            move_y = int(self.partial_y)
            if abs(move_x) > 0 or abs(move_y) > 0:
                self.partial_x -= move_x
                self.partial_y -= move_y
            # # self.x += int(self.partial_x)
            # # self.y += int(self.partial_y)
            # x = self.x + int(self.partial_x)
            # y = self.y + int(self.partial_y)
            # # Zatrzymaj tylko część ułamkową dla następnych kroków
            # self.partial_x -= int(self.partial_x)
            # self.partial_y -= int(self.partial_y)
                x = self.x + move_x
                y = self.y + move_y
            # x = self.x + row[i]
            # y = self.y + col[i]
            # x = self.x + int(row[i] * self.speed)
            # y = self.y + int(col[i] * self.speed)

                if inLayout(self.layout, x,y) and (not isWall(self.layout,x,y) and not isFire(self.layout,x,y) and not isSmoke(self.layout,x,y) and not isExit(self.layout,x,y) and not isAlarm(self.layout,x,y)):
                        return [[x, y]]
                else:
                    return [[self.x, self.y]]
                
        return [[self.x, self.y]]
    def percept(self, layout):
        # print(f"[DEBUG] Agent {self.id}: Perceiving environment")
        x0 = max(self.x - self.range, 0)
        y0 = max(self.y - self.range, 0)
        x1 = min(self.x + self.range, len(layout) - 1)
        y1 = min(self.y + self.range, len(layout[0]) - 1)

        self.reconsider = False
        for i in range(x0, x1 + 1):
            for j in range(y0, y1 + 1):
                if self.layout[i][j] != layout[i][j]:
                    # print(f"[DEBUG] Agent {self.id}: Detected change at ({i}, {j})")
                    self.danger = True
                    self.reconsider = True
                    self.layout[i][j] = layout[i][j]

    def plan_(self, all_agents):
        # print(f"[DEBUG] Agent {self.id}: Planning, Danger: {self.danger}, Reconsider: {self.reconsider}")
        if not self.danger:
            # print("planowanie random")
            self.plan = self.moveRandom()
            # print(f"[DEBUG] Agent {self.id}: Random move plan: {self.plan}")
        elif self.rescue_relatives == True:
            # print("planowanie resuce")
            relative = self.check_for_relatives_in_range(all_agents, grid_size=10)
            if relative:
                self.rescue_counter +=1
                # self.plan = self.DijkstraToTarget(all_agents, target=relative.getPosition())
                # print(f"[DEBUG] Agent {self.id}: Found relative {relative.getID()} in range. Moving to relative at position: {relative.getPosition()}. Plan: {self.plan}")
                
                # if abs(self.x - relative.x) <= 2 and abs(self.y - relative.y) <= 2:
                # print(f"[DEBUG] Agent {self.id}: Synchronizing exit with relative {relative.id}")
                self.synchronize_exit(relative)
            else:
                # Jeśli nie znaleziono krewnych, zmień flagę i przejdź do ucieczki
                # print(f"[DEBUG] Agent {self.id}: No relatives found in range. Switching to escape mode.")
                self.rescue_relatives = False
                self.reconsider = True
                self.plan = self.Dijkstra()
        elif self.reconsider:
            # print("planowanie reconsider")
            if self.strategy == "nearest_exit":
                self.plan = self.Dijkstra()
            elif self.strategy == "safest_exit":
                danger_sources = self.get_danger_sources()
                self.plan = self.Dijkstra_safest(danger_sources)
            elif self.strategy == "least_crowded_exit":
                self.plan = self.DijkstraToTarget(all_agents)
            else:
                self.plan = self.Dijkstra()
            # print(f"[DEBUG] Agent {self.id}: Planned path: {self.plan}")

    def panic(self):
        # print(f"[DEBUG] Agent {self.id}: Panic mode activated")
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
                # print(f"[DEBUG] Agent {self.id}: Found free cell at ({x}, {y})")
                return [[x,y]]
        for i in range(len(row)):
            x = self.x + row[i]
            y = self.y + col[i]
            if (isSmoke(self.layout,x,y)):
                # print(f"[DEBUG] Agent {self.id}: No free cell, moving to smoke cell at ({x}, {y})")
                return [[x,y]]
        # print(f"[DEBUG] Agent {self.id}: No options left, staying at current position ({self.x}, {self.y})")
        return [[self.x,self.y]] #desisti


    def synchronize_exit(self, relative):
        # Obliczenie wspólnej ścieżki do wyjścia
        exit_path = self.Dijkstra()  # Oblicz najkrótszą ścieżkę do wyjścia

        # Ustawienie tej samej ścieżki dla obu agentów
        self.plan = exit_path
        relative.plan = exit_path
        relative.danger = True
        # Zmiana flag
        self.reconsider = False
        relative.reconsider = False

        # Oznaczenie zsynchronizowanego wyjścia
        self.synchronized_exit = True
        relative.synchronized_exit = True

        # Wyłączenie flag ratowania krewnych
        self.rescue_relatives = False
        relative.rescue_relatives = False

    def Dijkstra(self):
        # print(f"[DEBUG] Agent {self.id}: Starting Dijkstra's algorithm")
        source = [self.x, self.y]
        dests = self.exits

        if source in dests:
            # print(f"[DEBUG] Agent {self.id}: Already at an exit")
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
                # print(f"[DEBUG] Agent {self.id}: Destination reached: {parent}")
                my_dest = list(parent)
                break

            combined = list(zip(row, col))
            random.shuffle(combined)
            row, col = zip(*combined)

            for i in range(len(row)):
                # self.partial_x += row[i] * self.speed
                # self.partial_y += col[i] * self.speed
                x, y = parent[0] + row[i], parent[1] + col[i]
                # x, y = parent[0] + int(self.partial_x), parent[1] + int(self.partial_y)
                # self.partial_x -= int(self.partial_x)
                # self.partial_y -= int(self.partial_y)
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
            # print(f"[DEBUG] Agent {self.id}: No path to exit found, triggering panic")
            return self.panic()

        path = []
        at = my_dest
        while at != source:
            path.append(at)
            at = parents[tuple(at)]

        path.reverse()
        # print(f"[DEBUG] Agent {self.id}: Path found: {path}")
        return path
    

    def calculate_crowdedness_and_danger(self, exits, agents, radius):
        crowdedness = {}
        danger_level = {}  # Nowa struktura danych do śledzenia zagrożenia
        # print("Obliczanie zatłoczenia i poziomu zagrożenia...")
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

            # print(f"Wyjście {exit}: Zatłoczenie={crowdedness[exit]}, Zagrożenie={danger_level[exit]}")

        return crowdedness, danger_level

    def move_to_least_crowded_exit(self, all_agents):
        try:
            # Oblicz zatłoczenie i zagrożenie dla wszystkich wyjść
            crowdedness, danger_level = self.calculate_crowdedness_and_danger(self.exits, all_agents, 3)
            # print(f"Agent {self.getID()} - Zatłoczenie: {crowdedness}")
            # print(f"Agent {self.getID()} - Poziom zagrożenia: {danger_level}")

            # Wybierz najmniej zatłoczone wyjście
            best_exit = min(
                self.exits,
                key=lambda exit: crowdedness[tuple(exit)]  # Bierzemy wyjście o najniższym zatłoczeniu
            )
            # print(f"Agent {self.getID()} - Wybrane wyjście: {best_exit}")

            # Uruchom Dijkstrę do wybranego wyjścia
            path = self.DijkstraToTarget([tuple(best_exit)])
            if path:
                # print(f"Agent {self.getID()} - Ścieżka do wybranego wyjścia: {path}")
                return path

            # Jeśli Dijkstra nie znajdzie ścieżki, przechodzimy do trybu paniki
            # print(f"Agent {self.getID()} - Nie znaleziono ścieżki do wybranego wyjścia, przechodzę do trybu paniki.")
            return self.panic()

        except Exception as e:
            # print(f"Błąd w move_to_least_crowded_exit dla agenta {self.getID()}: {e}")
            return self.panic()


    def check_for_relatives_in_range(self, agents, grid_size=10):
        # print("[DEBUG] agent ma jakichś krewnych")
        for agent in agents:
            if agent.getID() in self.getRelatives():  # Sprawdź, czy to krewny
                distance_x = abs(self.x - agent.x)
                distance_y = abs(self.y - agent.y)
                if distance_x <= grid_size and distance_y <= grid_size:
                    # print("[DEBUG] agent znalazł krewnego w pobliżu")
                    return agent  # Zwróć krewnego w zasięgu
        return None


    def select_least_crowded_exit(self, all_agents):
        crowdedness, danger_level = self.calculate_crowdedness_and_danger(self.exits, all_agents, 10)

        # Oblicz najlepsze wyjście na podstawie najmniejszego zatłoczenia
        best_exit = None
        min_crowdedness = float('inf')
        for exit in self.exits:
            exit_tuple = tuple(exit)
            if crowdedness[exit_tuple] + danger_level[exit_tuple] < min_crowdedness:
                min_crowdedness = crowdedness[exit_tuple]
                best_exit = exit_tuple
                # print(f"[best_exit] Agent {self.id}: Selected least crowded exit: {best_exit}")


        # if best_exit is not None:
        #     # print(f"[DEBUG] Agent {self.id}: Selected least crowded exit: {best_exit}")
        # else:
        #     # print(f"[DEBUG] Agent {self.id}: No valid exits found.")
        self.strategy = STATUS[0]
        return best_exit

    def DijkstraToTarget(self, all_agents, target=None):
        # print(f"[DEBUG] Agent {self.id}: Starting DijkstraToTarget's algorithm")
        if not target:
        # Wybierz najmniej zatłoczone wyjście
            best_exit = self.select_least_crowded_exit(all_agents)
        else:
            # print("[DEBUG] mam zadany cel")
            best_exit = tuple(target)
        if best_exit is None:
            # print(f"[DEBUG] Agent {self.id}: No valid exit found. Triggering panic.")
            return self.panic()
        
        # print(f"[DEBUG] Agent {self.id}: Best exit selected: {best_exit}")
        source = (self.x, self.y)

        # Jeśli agent już jest przy wybranym wyjściu
        if source == best_exit:
            # print(f"[DEBUG] Agent {self.id}: Already at the best exit")
            return [list(source)]

        # Współrzędne ruchu w czterech kierunkach
        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        queue = []
        parents = {}
        distances = {}

        # Inicjalizacja odległości i rodziców
        for i in range(len(self.layout)):
            for j in range(len(self.layout[0])):
                distances[(i, j)] = math.inf
                parents[(i, j)] = None

        distances[source] = 0
        heapq.heappush(queue, (0, source))

        while queue:
            current_dist, current = heapq.heappop(queue)

            # Jeśli osiągnięto najlepsze wyjście
            if current == best_exit:
                path = []
                while current:
                    path.append(list(current))
                    current = parents[current]
                path.reverse()
                # print(f"[DEBUG] Agent {self.id}: Path to exit found: {path}")
                return path

            # Eksploruj sąsiadów
            for dx, dy in zip(row, col):
                
                neighbor = (current[0] + dx, current[1] + dy)

                if not (0 <= neighbor[0] < len(self.layout) and 0 <= neighbor[1] < len(self.layout[0])):
                    continue  # Poza granicami mapy

                if isWall(self.layout, neighbor[0], neighbor[1]) or isFire(self.layout, neighbor[0], neighbor[1]):
                    continue  # Nieprzechodnia komórka

                # Oblicz koszt przejścia
                weight = 1
                if isSmoke(self.layout, neighbor[0], neighbor[1]):
                    weight += (1 - self.risk) * 5

                alt = current_dist + weight
                if alt < distances[neighbor]:
                    distances[neighbor] = alt
                    parents[neighbor] = current
                    heapq.heappush(queue, (alt, neighbor))

        # print(f"[DEBUG] Agent {self.id}: No path to exit found. Triggering panic.")
        return self.panic()

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
                # x, y = parent[0] + int(row[i] * self.speed), parent[1] + int(col[i] * self.speed)
                # self.partial_x += row[i] * self.speed
                # self.partial_y += col[i] * self.speed
                # # x, y = parent[0] + row[i], parent[1] + col[i]
                # x, y = parent[0] + int(self.partial_x), parent[1] + int(self.partial_y)
                # self.partial_x -= int(self.partial_x)
                # self.partial_y -= int(self.partial_y)
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
        # if not danger_sources:
            # print("Nie znaleziono zagrożeń w layout!")
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



