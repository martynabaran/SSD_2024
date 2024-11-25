# Sprites

import pygame
import random
from random import choices
import numpy as np
from settings import *
from auxiliary import *
import heapq
import math


class Agent(pygame.sprite.Sprite):
    def __init__(self, identifier, layout, exits, health, risk, communicates):
        pygame.sprite.Sprite.__init__(self)
        self.image  = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(DARKRED)
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
        self.strategy = None

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
        if (not self.dead):
            if (len(self.plan)>0): #nasty FIXME
                self.new_x = (self.plan[0][0])
                self.new_y = (self.plan[0][1])
                
                for agent in all_agents:
                    if not agent.isDead() and agent.getPosition() == [self.new_x, self.new_y] and not agent.getNewPosition() == [self.x, self.y]:
                        return 

                self.move(dx = (self.new_x - self.x), dy = (self.new_y - self.y))
                self.plan    = self.plan[1:]
                self.rect.x  = self.x * TILESIZE 
                self.rect.y  = self.y * TILESIZE


    def checkAlarm(self, alarm):
        if alarm and not self.danger:
            self.danger     = True
            self.reconsider = True
    
    def receiveMessage(self, message):
        for i in range(len(message)):
            for j in range(len(message[i])):
                if (self.layout[i][j] != message[i][j] and (isFire(message,i,j) or isSmoke(message,i,j))):
                    self.danger       = True
                    self.reconsider   = True
                    self.layout[i][j] = message[i][j]
                    
    def receiveMessagefromRelative(self, message):
        for i in range(len(message)):
            for j in range(len(message[i])):
                if (self.layout[i][j] != message[i][j]):
                    self.danger       = True
                    self.reconsider   = True
                    self.layout[i][j] = message[i][j]

    def percept(self, layout):
        x0 = self.x-self.range
        y0 = self.y-self.range
        x1 = self.x+self.range
        y1 = self.y+self.range
        self.reconsider = False
        if (x0 < 0):
            x0 = 0
        if (y0 < 0):
            y0 = 0
        if (x1 > len(layout)-1):
            x1 = len(layout)-1
        if (y1 > len(layout[0])-1):
            y1 = len(layout[0])-1
        for i in range(x0, x1+1):
            for j in range(y0, y1+1):
                if (self.layout[i][j] != layout[i][j]):
                    self.danger       = True
                    self.reconsider   = True
                    self.layout[i][j] = layout[i][j]
                    # if self.relatives:
                    #     self.informRelative(i,j,layout[i][j])

    def informRelative(self, x, y, layout):
        for relative in self.relatives:
            if not relative.getDangerState():
                relative.setDangerState(True)
                relative.updateLayout(x,y,layout)

    def moveRandom(self):
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


    def plan_(self, all_agents):
        if not self.danger:  # Poruszanie losowe, gdy nie ma zagrożenia
            self.plan = self.moveRandom()
        elif self.reconsider:
            # Wybierz strategię
            if self.strategy == "nearest_exit":
                self.plan = self.Dijkstra()
            elif self.strategy == "safest_exit":
                self.plan = self.move_to_safest_exit(all_agents)
            elif self.strategy == "least_crowded_exit":
                self.plan = self.move_to_least_crowded_exit(all_agents)



    #Our reactive agent logic
    def panic(self):
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
                return [[x,y]]
        for i in range(len(row)):
            x = self.x + row[i]
            y = self.y + col[i]
            if (isSmoke(self.layout,x,y)):
                return [[x,y]]
        return [[self.x,self.y]] #desisti
    

    def calculate_crowdedness(self, exits, agents, radius):
        crowdedness = {}
        for exit in exits:
            x_exit, y_exit = exit
            crowdedness[exit] = 0
            
            for agent in agents:
                if not agent.isDead():
                    x_agent, y_agent = agent.getPosition()
                    # Sprawdzenie czy agent znajduje się w promieniu wokół wyjścia
                    if abs(x_agent - x_exit) <= radius and abs(y_agent - y_exit) <= radius:
                        crowdedness[exit] += 1
        return crowdedness

    def move_to_least_crowded_exit(self, all_agents):
        # Oblicz zatłoczenie wyjść
        radius = 2  # Promień wokół wyjścia, który będzie brany pod uwagę
        crowdedness = self.calculate_crowdedness(self.exits, all_agents, radius)
        
        # Znajdź najmniej zatłoczone wyjście
        least_crowded_exit = min(crowdedness, key=crowdedness.get)
        
        # Wyznacz trasę do najmniej zatłoczonego wyjścia
        self.plan = self.DijkstraToTarget(least_crowded_exit)



    def DijkstraToTarget(self, target):
        source = [self.x, self.y]
        dest = target  # Cel: konkretne wyjście

        if source == dest:
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

        while len(queue) > 0:
            cur = heapq.heappop(queue)
            parent = (cur[1], cur[2])

            if not enqueued[parent]:
                continue

            enqueued[parent] = False

            if list(parent) == dest:
                break

            combined = list(zip(row, col))
            random.shuffle(combined)
            row, col = zip(*combined)

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

        path = []
        at = dest
        while at != source:
            path.append(at)
            at = parents[tuple(at)]

        path.reverse()
        return path



    def Dijkstra(self):
        source  = [self.x, self.y]
        dests   = self.exits

        if (source in dests):
            return [source]

        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        queue   = []
        my_dest = []
        visited = []
        parents  = dict()
        distance = dict()
        enqueued = dict()

        # Initialize stuff
        for i in range(len(self.layout)):
            visit = []
            for j in range(len(self.layout)):
                visit.append(0)
                parents[(i,j)]  = None
                distance[(i,j)] = math.inf
                enqueued[(i,j)] = None
            visited.append(visit)

        queue = [[0, source[0], source[1]]]
        heapq.heapify(queue)
        distance[tuple(source)] = 0
        enqueued[tuple(source)] = True
        visited [source[0]][source[1]] = 1

        while (len(queue) > 0):
            
            cur    = heapq.heappop(queue)
            parent = (cur[1], cur[2])

            if (not enqueued[parent]):
                continue

            enqueued[parent] = False

            if(list(parent) in dests): 
                my_dest = list(parent)
                break

            # shuffle visiting order of the neighbours
            combined = list(zip(row, col))
            random.shuffle(combined)
            row, col = zip(*combined)

            for i in range(len(row)):

                x, y = parent[0] + row[i], parent[1] + col[i]
                if (x < 0 or y < 0 or x >= len(self.layout) or y >= len(self.layout[0])): continue

                if (enqueued[(x,y)] == False ):
                    continue

                if(not isWall(self.layout,x,y) and not isFire(self.layout,x,y) and not isAlarm(self.layout,x,y) and visited[x][y] == 0):
                    visited[x][y] = 1
                    
                    #Compute cost of this transition
                    weight = 1
                    if (isSmoke(self.layout,x,y)):
                        weight += 1-self.risk

                    alternative = distance[parent] + weight

                    if (alternative < distance[(x,y)]):
                        distance[(x,y)] = alternative
                        parents[(x,y)]  = list(parent)
                        heapq.heappush(queue,[alternative, x, y])
                        enqueued[(x,y)] = True

        panic = True
        for dest in dests:
            if visited[dest[0]][dest[1]]:
                panic = False

        if panic:
            return self.panic()

        path = []
        at   = my_dest
        while at != source:
            path.append(at)
            at = parents[tuple(at)]

        path.reverse()
        return path


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

                    # Add safety factor
                    safety_factor = min(
                        [math.sqrt((x - sx) ** 2 + (y - sy) ** 2) for sx, sy in danger_sources]
                    )
                    weight += 1 / max(safety_factor, 0.1)  # Avoid division by zero

                    alternative = distance[parent] + weight

                    if alternative < distance[(x, y)]:
                        distance[(x, y)] = alternative
                        parents[(x, y)] = list(parent)
                        heapq.heappush(queue, [alternative, x, y])
                        enqueued[(x, y)] = True

        if not my_dest:
            return self.panic()

        path = []
        at = my_dest
        while at != source:
            path.append(at)
            at = parents[tuple(at)]

        path.reverse()
        return path


    def heuristic(self, node, dests):
        return min(abs(node[0] - d[0]) + abs(node[1] - d[1]) for d in dests)


    def AStar(self):
        source = [self.x, self.y]
        dests = self.exits

        if source in dests:
            return [source]

        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        # Kolejka priorytetowa dla węzłów do odwiedzenia
        queue = []
        heapq.heapify(queue)

        # Zestawy i mapy dla odwiedzonych węzłów, kosztów, heurystyki, i rodziców
        visited = [[0 for _ in range(len(self.layout[0]))] for _ in range(len(self.layout))]
        g_cost = dict()  # Koszt dotarcia do danego węzła
        f_cost = dict()  # Całkowity koszt (g + h)
        parents = dict()  # Mapa rodziców do odtworzenia ścieżki

        # Inicjalizacja kosztów dla wszystkich węzłów
        for i in range(len(self.layout)):
            for j in range(len(self.layout[0])):
                g_cost[(i, j)] = math.inf
                f_cost[(i, j)] = math.inf

        # Inicjalizacja węzła startowego
        g_cost[tuple(source)] = 0
        f_cost[tuple(source)] = self.heuristic(source, dests)  # Heurystyka
        heapq.heappush(queue, (f_cost[tuple(source)], source))
        parents[tuple(source)] = None

        my_dest = []

        while len(queue) > 0:
            # Pobierz węzeł z najmniejszym kosztem f
            _, current = heapq.heappop(queue)
            current_tuple = tuple(current)

            if visited[current[0]][current[1]]:
                continue

            visited[current[0]][current[1]] = 1

            # Sprawdź, czy dotarliśmy do celu
            if current in dests:
                my_dest = current
                break

            # Przetwarzanie sąsiadów
            combined = list(zip(row, col))
            random.shuffle(combined)
            for drow, dcol in combined:
                x, y = current[0] + drow, current[1] + dcol

                if x < 0 or y < 0 or x >= len(self.layout) or y >= len(self.layout[0]):
                    continue

                if visited[x][y] or isWall(self.layout, x, y) or isFire(self.layout, x, y) or isAlarm(self.layout, x, y):
                    continue

                # Koszt przejścia do sąsiada
                weight = 1
                if isSmoke(self.layout, x, y):
                    weight += 1 - self.risk

                tentative_g_cost = g_cost[current_tuple] + weight

                # Jeśli znaleziono lepszy koszt, aktualizuj
                if tentative_g_cost < g_cost[(x, y)]:
                    g_cost[(x, y)] = tentative_g_cost
                    f_cost[(x, y)] = tentative_g_cost + self.heuristic([x, y], dests)
                    parents[(x, y)] = current
                    heapq.heappush(queue, (f_cost[(x, y)], [x, y]))

        # Jeśli nie znaleziono drogi, uruchom tryb paniki
        panic = True
        for dest in dests:
            if visited[dest[0]][dest[1]]:
                panic = False

        if panic:
            return self.panic()

        # Odtworzenie ścieżki
        path = []
        at = my_dest
        while at and tuple(at) in parents:
            path.append(at)
            at = parents[tuple(at)]

        path.reverse()
        return path

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