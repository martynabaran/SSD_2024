import pygame
import random
from random import choices
import numpy as np
from settings import *
from auxiliary import *
import heapq
import math


class Agent(pygame.sprite.Sprite):
    def __init__(self, identifier, layout, exits, health, risk, communicates, strategy, color, range, volume):
        pygame.sprite.Sprite.__init__(self)
        self.image  = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect()

        # Core properties of the agent
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
        self.range        = range
        self.volume       = volume
        self.relatives = []
        self.strategy = strategy
        self.rescue_counter = 0
        
        # Initialize position avoiding walls, alarms, and exits
        self.x = random.randrange(0, len(self.layout))
        self.y = random.randrange(0, len(self.layout[0]))
        while(isWall(self.layout,self.x,self.y) or isAlarm(self.layout, self.x,self.y) or isExit(layout, self.x, self.y)):
            self.x = random.randrange(0, len(self.layout))
            self.y = random.randrange(0, len(self.layout[0]))

        # Movement and age attributes
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
        """Calculates agent speed based on age. Older agents move slower."""
        if self.age > 60:  # Starsi
            return 1.0  
        else: 
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
        """Moves the agent based on calculated deltas."""
        # self.partial_x += dx * self.speed
        # self.partial_y += dy * self.speed
        # move_x, move_y = int(self.partial_x), int(self.partial_y)
       
        # if abs(move_x) > 0 or abs(move_y) > 0:
        #     self.partial_x -= move_x
        #     self.partial_y -= move_y
        #     self.x = max(self.x + dx, self.x + move_x)
        #     self.y = max(self.x + dy, self.x + move_y)
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
        """Updates agent's position based on its plan and checks for conflicts with other agents."""
        if not self.dead and self.plan and len(self.plan) > 0:
                self.new_x, self.new_y  = self.plan[0][0], self.plan[0][1]

                # Check for conflicts with other agents
                for agent in all_agents:
                    if not agent.isDead() and agent.getPosition() == [self.new_x, self.new_y] and not agent.getNewPosition() == [self.x, self.y]:
                        return

                self.move(dx=(self.new_x - self.x), dy=(self.new_y - self.y))
                self.plan = self.plan[1:]
                self.rect.x = self.x * TILESIZE
                self.rect.y = self.y * TILESIZE

    def checkAlarm(self, alarm):
        if alarm and not self.danger:
            self.danger = True
            self.reconsider = True

    def receiveMessage(self, message):
        for i in range(len(message)):
            for j in range(len(message[i])):
                if self.layout[i][j] != message[i][j] and (isFire(message, i, j) or isSmoke(message, i, j)):
                    self.danger = True
                    self.reconsider = True
                    self.layout[i][j] = message[i][j]

    def moveRandom(self):
        row  = [-1, 0, 0, 1]
        col  = [0, -1, 1, 0]
        move = [True, False]
        prob = [1/self.id, 1-(1/self.id)]
        if (choices(move, prob)):
            i = random.randrange(0, 4)
            # self.partial_x += row[i] * self.speed
            # self.partial_y += col[i] * self.speed
            # move_x = int(self.partial_x)
            # move_y = int(self.partial_y)
            # if abs(move_x) > 0 or abs(move_y) > 0:
            #     self.partial_x -= move_x
            #     self.partial_y -= move_y
            #     x = self.x + move_x
            #     y = self.y + move_y
            x = self.x + row[i]
            y = self.y + col[i]
            if not isWall(self.layout,x,y) and not isFire(self.layout,x,y) and not isSmoke(self.layout,x,y) and not isExit(self.layout,x,y) and not isAlarm(self.layout,x,y):
                        return [[x, y]]
            else:
                    return [[self.x, self.y]]
                
        return [[self.x, self.y]]
    
    def percept(self, layout):
        """Allows the agent to perceive changes in its environment."""
        x0, y0 = max(self.x - self.range, 0), max(self.y - self.range, 0)
        x1, y1 = min(self.x + self.range, len(layout) - 1), min(self.y + self.range, len(layout[0]) - 1)

        self.reconsider = False
        for i in range(x0, x1 + 1):
            for j in range(y0, y1 + 1):
                if self.layout[i][j] != layout[i][j]:
                    self.danger = True
                    self.reconsider = True
                    self.layout[i][j] = layout[i][j]

    def plan_(self, all_agents):
        """Generates a movement plan based on the agent's strategy and current danger state."""
        if not self.danger:
            self.plan = self.moveRandom()
        elif self.rescue_relatives:
            relative = self.check_for_relatives_in_range(all_agents, grid_size=10)
            if relative:
                self.rescue_counter += 1
                self.synchronize_exit(all_agents,relative)
            else:
                self.rescue_relatives = False
                self.reconsider = True
                self.plan = self.Dijkstra()
        elif self.reconsider:
            if self.strategy == "nearest_exit":
                self.plan = self.Dijkstra()
            elif self.strategy == "safest_exit":
                danger_sources = self.get_danger_sources()
                self.plan = self.Dijkstra_safest(danger_sources)
            elif self.strategy == "least_crowded_exit":
                self.plan = self.DijkstraToTarget(all_agents)
            else:
                self.plan = self.Dijkstra()

    def panic(self):
        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        combined = list(zip(row, col))
        random.shuffle(combined)
        row, col = zip(*combined)
        
        for i in range(len(row)):
            x = self.x + row[i]
            y = self.y + col[i]
            if (not isWall(self.layout, x, y) and not isFire(self.layout, x, y) and not isSmoke(self.layout, x, y) and not isAlarm(self.layout, x, y)):
                return [[x, y]]
        
        for i in range(len(row)):
            x = self.x + row[i]
            y = self.y + col[i]
            if (isSmoke(self.layout, x, y)):
                return [[x, y]]

        return [[self.x, self.y]]  # No options left, staying in the same position


    def synchronize_exit(self, all_agents, relative):
        # Calculate common path to exit
        exit_path = self.Dijkstra()

        # Set same path for both agents
        self.plan = exit_path
        relative.plan = relative.DijkstraToTarget(all_agents, target=exit_path[-1])
        relative.danger = True
        print(f"AGENT: pozycja - ({self.x}, {self.y}), plan: {self.plan}")
        print(f"RELATIVE: pozycja ({relative.x}, {relative.y}) : {relative.plan}")
        self.reconsider = False
        relative.reconsider = False

        # Mark synchronized exit
        self.synchronized_exit = True
        relative.synchronized_exit = True

        # Set off flags to rescue relatives (already rescued)
        self.rescue_relatives = False
        relative.rescue_relatives = False

    def Dijkstra(self):
        source = [self.x, self.y]
        dests = self.exits

        if source in dests:
            return [source]

        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]
        
        queue = []
        visited = []
        parents = {}
        distance = {}
        enqueued = {}
        my_dest = []

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
        # if 0 <= source[0] < len(self.layout) and 0 <= source[1] < len(self.layout[0]):
        # visited[source[0]][source[1]] = 1
        if 0 <= source[0] < len(visited) and 0 <= source[1] < len(visited[0]):
            visited[source[0]][source[1]] = 1
        else:
            print(f"[ERROR] Source out of bounds: {source}, len on visited: {len(visited)}, {len(visited[0])}")
            print(f"layout bounds: {len(self.layout)}, {len(self.layout[0])}")
            return []

        while queue:
            cur = heapq.heappop(queue)
            parent = (cur[1], cur[2])

            if not enqueued[parent]:
                continue

            enqueued[parent] = False

            if list(parent) in dests:
                my_dest = list(parent)
                break
                # return [list(parent)]

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
        # return self.panic()  # No path found, triggering panic
    

    def calculate_crowdedness_and_danger(self, exits, agents, radius):
        crowdedness = {}
        danger_level = {}  
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

            # Calculate teh level of danger around the exit
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x, y = x_exit + dx, y_exit + dy
                    if 0 <= x < len(self.layout) and 0 <= y < len(self.layout[0]):
                        if isFire(self.layout, x, y):
                            danger_level[exit] += 10  # High penalty for fire
                        elif isSmoke(self.layout, x, y):
                            danger_level[exit] += 5  # Lower penalty for smoke

            

        return crowdedness, danger_level

    def move_to_least_crowded_exit(self, all_agents):
        crowdedness, danger_level = self.calculate_crowdedness_and_danger(self.exits, all_agents, 3)

        best_exit = min(self.exits, key=lambda exit: crowdedness[tuple(exit)])

        path = self.DijkstraToTarget([tuple(best_exit)])
        if path:
            return path

        return self.panic()


    def check_for_relatives_in_range(self, agents, grid_size=10):
        for agent in agents:
            if agent.getID() in self.getRelatives():  # Sprawdź, czy to krewny
                distance_x = abs(self.x - agent.x)
                distance_y = abs(self.y - agent.y)
                if distance_x <= grid_size and distance_y <= grid_size:
                    return agent  # Return relative in range
        return None


    def select_least_crowded_exit(self, all_agents):
        crowdedness, danger_level = self.calculate_crowdedness_and_danger(self.exits, all_agents, 10)

        best_exit = None
        min_crowdedness = float('inf')
        for exit in self.exits:
            exit_tuple = tuple(exit)
            if crowdedness[exit_tuple] + danger_level[exit_tuple] < min_crowdedness:
                min_crowdedness = crowdedness[exit_tuple]
                best_exit = exit_tuple
                
        self.strategy = STATUS[0]
        return best_exit

    def DijkstraToTarget(self, all_agents, target=None):
        if not target:
            best_exit = self.select_least_crowded_exit(all_agents)
        else:
            best_exit = tuple(target)
        
        if best_exit is None:
            return self.panic()
        
        source = (self.x, self.y)
        if source == best_exit:
            return [list(source)]

        row = [-1, 0, 0, 1]
        col = [0, -1, 1, 0]

        queue = []
        parents = {}
        distances = {}

        for i in range(len(self.layout)):
            for j in range(len(self.layout[0])):
                distances[(i, j)] = math.inf
                parents[(i, j)] = None

        distances[source] = 0
        heapq.heappush(queue, (0, source))

        while queue:
            current_dist, current = heapq.heappop(queue)

            if current == best_exit:
                path = []
                while current:
                    path.append(list(current))
                    current = parents[current]
                path.reverse()
                return path

            for dx, dy in zip(row, col):
                neighbor = (current[0] + dx, current[1] + dy)

                if not (0 <= neighbor[0] < len(self.layout) and 0 <= neighbor[1] < len(self.layout[0])):
                    continue

                if isWall(self.layout, neighbor[0], neighbor[1]) or isFire(self.layout, neighbor[0], neighbor[1]):
                    continue

                weight = 1
                if isSmoke(self.layout, neighbor[0], neighbor[1]):
                    weight += (1 - self.risk) * 5

                alt = current_dist + weight
                if alt < distances[neighbor]:
                    distances[neighbor] = alt
                    parents[neighbor] = current
                    heapq.heappush(queue, (alt, neighbor))

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
        # if 0 <= source[0] < len(self.layout) and 0 <= source[1] < len(self.layout[0]):
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



