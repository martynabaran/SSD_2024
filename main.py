import pygame
from auxiliary import *
from random import choices
from settings import *
from spirites3 import *
from copy import deepcopy
import time
import uuid
import csv
import os
from collections import Counter
import cv2

simulation_id = str(uuid.uuid4())

def drawGrid():
    for x in range(0, WIDTH, TILESIZE):
        pygame.draw.line(SCREEN, BLACK, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, TILESIZE):
        pygame.draw.line(SCREEN, BLACK, (0, y), (WIDTH, y))

def updateHealth(agent,i):
    pos = agent.getPosition()
    identifier  = agent.getID()
    if (isExit(layout,pos[0], pos[1]) and identifier not in agents_saved):
        agents_saved.append(identifier)
        agent.saved_at = i
        all_sprites.remove(agent)
        all_agents.remove(agent)

    if(agent.getHealth() > 0):
        if (isSmoke(layout,pos[0], pos[1])): 
            new_health = agent.getHealth() - SMOKE_DMG
            agent.setHealth(new_health)
        if (isFire(layout,pos[0], pos[1])): 
            new_health = agent.getHealth() - FIRE_DMG
            agent.setHealth(new_health)

    if(agent.getHealth() <= 0):
        agent.die()
        agent.setColor(BLACK)
        if (identifier not in agents_dead):
            agents_dead.append(identifier)

def createWalls():
    for i in range(int(GRIDWIDTH)):
        for j in range(int(GRIDHEIGHT)):
            if (isWall(layout,i,j)):
                wall = Wall(i,j)
                all_sprites.add(wall)
                all_walls.add(wall)


def createAlarm():
    pos = [ [index, row.index('A')] for index, row in enumerate(layout) if 'A' in row]
    for p in pos:
        i = p[0]
        j = p[1]
        alarm = Alarm(i,j)
        all_sprites.add(alarm)
        all_alarms.add(alarm)

def alarm():
    global soundAlarm
    for alarm in all_alarms:
        if(alarm.CheckAlarm(layout)):
            #pygame.mixer.Sound.play(fire_alarm)
            soundAlarm = True
            break
    if(soundAlarm):
        for alarm in all_alarms:
            alarm.FireAlarm()


def createFires():
    x = random.randrange(0, len(layout))
    y = random.randrange(0, len(layout[0]))
    while(isWall(layout,x,y)):
        x = random.randrange(0, len(layout))
        y = random.randrange(0, len(layout[0]))
    addFire(x,y)

def addFire(i,j):
    fire = Fire(i,j)
    layout[i][j] = 'F'
    all_sprites.add(fire)
    all_fires.add(fire)

def addSmoke(i,j):
    smoke = Smoke(i,j)
    layout[i][j] = 'S'
    all_sprites.add(smoke)
    all_smokes.add(smoke)

def propagateFire(layout, config=None):
    """
    Propaguje ogień w układzie na podstawie konfiguracji.

    :param layout: Układ (np. mapa).
    :param config: (Opcjonalnie) Słownik konfiguracji. Jeśli None, używane są globalne zmienne.
    :return: Zaktualizowany layout.
    """
    # Pobieranie wartości z konfiguracji lub użycie domyślnych globalnych zmiennych
    fire_val = config.get("simulation", {}).get("fire_propagation", FIRE) if config else FIRE
    smoke_val = config.get("simulation", {}).get("smoke_propagation", SMOKE) if config else SMOKE

    spread = [True, False]  # Zmienna do propagacji
    propagate = [fire_val, 1 - fire_val]
    smoke = [smoke_val, 1 - smoke_val]
    row = [-1, 0, 0, 1]
    col = [0, -1, 1, 0]

    new_fires = []
    for fire in all_fires:
        i = random.randrange(0, 4)
        x = fire.x + row[i]
        y = fire.y + col[i]

        if (x > len(layout)-1 or y > len(layout[0])-1): continue

        propagate_ = propagate
        if (isSmoke(layout, x, y)):
            propagate_[0] += (1 - propagate_[1]) / 2
            propagate_[1] = 1 - propagate_[0]
        if (choices(spread, propagate_)[0] and not isWall(layout, x, y) and not isFire(layout, x, y) and not isExit(layout, x, y)):
            for smoke in all_smokes:
                if smoke.x == x and smoke.y == y:
                    all_smokes.remove(smoke)
                    break
            new_fires.append([x, y])

    for fire in new_fires:
        addFire(fire[0], fire[1])

    return layout


def propagateSmoke(layout, config=None):
    """
    Propaguje dym w układzie na podstawie konfiguracji.

    :param layout: Układ (np. mapa).
    :param config: (Opcjonalnie) Słownik konfiguracji. Jeśli None, używane są globalne zmienne.
    :return: Zaktualizowany layout.
    """
    # Pobieranie wartości z konfiguracji lub użycie domyślnych globalnych zmiennych
    spread_val = [True, False]        #either it spreads or not
    wind   = [0.4, 0.3, 0.2, 0.1]
    smk_val = config.get("simulation", {}).get("smoke_propagation", SMOKE) if config else SMOKE

    smk = [smk_val, 1 - smk_val]
    row = [-1, 0, 0, 1]
    col = [0, -1, 1, 0]

    for fire in all_fires:
        for i in range(len(row)):
            x = fire.x + row[i]
            y = fire.y + col[i]

            if (x > len(layout)-1 or y > len(layout[0])-1): continue

            if (choices(spread_val, smk)[0] and validPropagation(layout, x, y)):
                addSmoke(x, y)

    for smoke in all_smokes:
        for i in range(len(row)):
            x = smoke.x + row[i]
            y = smoke.y + col[i]

            if (x > len(layout)-1 or y > len(layout[0])-1): continue

            go = choices(spread_val, smk)[0]
            if (go and validPropagation(layout, x, y)):
                addSmoke(x, y)

    return layout



def draw():				
    SCREEN.fill(WHITE)
    all_walls.draw(SCREEN)
    all_smokes.draw(SCREEN)
    all_fires.draw(SCREEN)
    all_alarms.draw(SCREEN)
    all_agents.draw(SCREEN)
    s = 'Saved Agents: ' + str(len(agents_saved))
    drawText(SCREEN, s, 34, WIDTH/3, HEIGHT)
    s = 'Dead Agents: ' + str(len(agents_dead))
    drawText(SCREEN, s, 34, 2*WIDTH/3, HEIGHT)
    drawGrid()
    pygame.display.flip()

# Draw Text in screen
font_name = pygame.font.match_font('arial')
def drawText(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE, BLACK)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (int(x),int(y))
    surf.blit(text_surface, text_rect)
def assertInRange(speaker, listener, config=None):
    """
    Sprawdza, czy odległość między speakerem a listenerem mieści się w dopuszczalnym zakresie.

    :param speaker: Obiekt reprezentujący mówcę.
    :param listener: Obiekt reprezentujący słuchacza.
    :param config: (Opcjonalnie) Słownik konfiguracji. Jeśli None, używana jest globalna zmienna VOL_RANGE.
    :return: True, jeśli listener znajduje się w zakresie od speakera, False w przeciwnym razie.
    """
    # Pobieranie wartości vol_range z konfiguracji lub użycie domyślnej VOL_RANGE
    vol_range = config.get("simulation", {}).get("vol_range", VOL_RANGE) if config else VOL_RANGE
    return abs(speaker.x - listener.x) <= vol_range and abs(speaker.y - listener.y) <= vol_range

def communicate(speaker):
    if (not speaker.isCommunicative()):
        return
    for listener in all_agents:
        if (speaker.getID() == listener.getID()): continue
        if assertInRange(speaker, listener):
            listener.receiveMessage(speaker.getLayout())




def gather_agent_data(all_agents_list):
    # Przygotowanie nagłówków do pliku CSV
    headers = ['Simulation_ID', 'Agent_ID', 'Survived', 'Age', 'Risk_Level', 'Strategy', 'Health_End', 
               'Escape_Time', 'Has_Relatives']

    # Otwarcie pliku CSV w trybie do zapisu (tworzenie lub nadpisanie)
    with open('simulation_agents.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow(headers)  # Zapisanie nagłówków

        # Zbieranie danych o każdym agencie
        for agent in all_agents_list:
            # Zakładamy, że agent ma odpowiednie metody do pozyskania tych informacji
            row = [
                simulation_id,   # ID symulacji, można je zdefiniować przed rozpoczęciem
                agent.getID(),   # ID agenta
                not agent.isDead(),  # Przeżył czy nie
                agent.age,       # Wiek
                agent.risk,      # Poziom ryzyka
                agent.strategy,  # Typ strategii
                agent.getHealth(),  # Poziom zdrowia na koniec
                agent.saved_at,  # Czas ucieczki (możesz tu wykorzystać krok, kiedy agent opuścił)
                len(agent.getRelatives()) > 0  # Czy miał bliskich w pobliżu
            ]
            writer.writerow(row)  # Zapisanie wiersza z danymi o agencie

import random
from copy import deepcopy
import yaml

# Funkcja do wczytania konfiguracji
def load_config(config_file='config.yaml'):
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Plik konfiguracyjny {config_file} nie istnieje. Używane będą wartości domyślne.")
        return {}

# Funkcja do inicjalizacji agentów
def initialize_agents(config, num_agents, layout=None, exits=None):
    default_values = {
        "health": 100,
        "risk_range": (0.0, 1.0),
        "communicates": num_agents,
        "strategies": {"nearest_exit": 33, "safest_exit": 33, "least_crowded_exit": 34},
        "range": VIS_RANGE,
        "volume": VOL_RANGE
    }

    # Pobierz wartości z pliku konfiguracyjnego lub ustaw domyślne
    simulation_config = config.get('simulation', {})
    agent_attributes = simulation_config.get('agent_attributes', {})
    
    health = agent_attributes.get('health', default_values["health"])
    risk_range = agent_attributes.get('risk', default_values["risk_range"])
    communicates = agent_attributes.get('communicates', default_values["communicates"])
    range_ = agent_attributes.get('range', default_values["range"])
    volume = agent_attributes.get('volume', default_values["volume"])
    
    strategies = simulation_config.get('strategies', [])
    print(strategies)
    strategy_counts =  strategies if strategies else default_values["strategies"]


    # Przygotuj agentów
    all_agents = pygame.sprite.Group()
    strategy_pool = []
    for strategy, count in strategy_counts.items():
        strategy_pool.extend([strategy] * count)

    colors = {'nearest_exit': "DARKRED", 'safest_exit': "PURPLE", 'least_crowded_exit': (112, 125, 26)}
    
    for i in range(num_agents):
        strategy = strategy_pool.pop(0) if strategy_pool else random.choice(list(colors.keys()))
        risk = random.uniform(*risk_range)
        agent = Agent(
            identifier=i + 1,
            layout=deepcopy(layout),
            exits=exits,
            health=health,
            risk=risk,
            communicates=(i < communicates),
            strategy=strategy,
            color=colors[strategy],
            range=range_,
            volume=volume
        )
        all_agents.add(agent)
    
    return all_agents

def initialize_families(config, agents):
    """
    Inicjalizuje rodziny na podstawie konfiguracji.
    
    :param config: Słownik z konfiguracją symulacji.
    :param agents: Lista agentów.
    :return: Zaktualizowana lista agentów z przypisanymi rodzinami.
    """
    # Pobieranie liczby rodzin z konfiguracji
    num_families = config.get("simulation", {}).get("num_families", 0)
    
    # Jeśli liczba rodzin jest zerowa lub brak pola w konfiguracji, nie tworzymy rodzin
    if num_families <= 0:
        print("Rodziny nie zostały zainicjalizowane, ponieważ liczba rodzin wynosi 0 lub jest nieokreślona.")
        return agents

    # Tworzenie rodzin
    all_agents_list = list(agents)
    random.shuffle(all_agents_list)  # Losowe przemieszanie agentów
    families_created = 0
    family_colors = [
        (102, 51, 153),  # Ciemny fiolet
        (0, 128, 128),   # Turkusowy
        (128, 0, 128),   # Fioletowy
        (75, 0, 130),    # Indygo
        (210, 105, 30),  # Czekoladowy
        (244, 164, 96),  # Piaskowy
        (139, 69, 19),   # Brązowy
        (46, 139, 87),   # Zielony morski
        (72, 61, 139),   # Ciemny niebieski
        (112, 128, 144), # Szaroniebieski
        (116, 221, 195),
        (214, 27, 98),
        (19, 158, 44),
        (103, 123, 217),
        (164, 110, 169),
        (112, 125, 26),
        (3, 87, 14),
        (61, 31, 90),
        (59, 50, 219),
        (14, 4, 2),
        (0, 247, 241),
        (204, 67, 196),
        (244, 21, 223),
        (177, 250, 200),
        (152, 231, 244),
        (70, 162, 30),
        (8, 136, 169),
        (185, 234, 221),
        (141, 174, 172),
        (254, 70, 87),
        (3, 60, 47),
        (148, 0, 79),
        (45, 238, 9),
        (67, 0, 235),
        (232, 98, 90),
        (76, 148, 185),
        (104, 130, 159),
        (147, 147, 181),
        (98, 129, 110),
        (235, 110, 210)
    ]

    for i in range(num_families):
        if len(all_agents_list) < 2:
            print("Nie można stworzyć więcej rodzin, ponieważ zabrakło agentów.")
            break

        # Wybieramy 2 lub 3 losowych agentów do jednej rodziny
        family_size = random.randint(2, 3)
        family_agents = [all_agents_list.pop() for _ in range(min(family_size, len(all_agents_list)))]
        family_color = family_colors[i % len(family_colors)]
        # Dodajemy ich do wzajemnych list relatives
        for agent in family_agents:
            for relative in family_agents:
                if agent != relative:
                    agent.getRelatives().append(relative.getID())
            agent.communicates = True  # Aktywacja komunikacji dla członków rodziny
            agent.image.fill(family_color)

        families_created += 1

    print(f"Zainicjalizowano {families_created} rodzin.")
    return agents


# Main
if __name__ == "__main__":
    global SCREEN, CLOCK, layout, all_sprites, all_agents, all_walls, all_fires, all_smokes, exits, soundAlarm, agents_saved, agents_dead
    
    soundAlarm = False
    fps = 30
    pygame.init()
    pygame.display.set_caption("Evacuation Simulation")
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT+40))
    CLOCK = pygame.time.Clock()
    SCREEN.fill(BLACK)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Format wideo (AVI)
    out = cv2.VideoWriter('simulationRelatives3.avi', fourcc, FPS, (WIDTH, HEIGHT+40))

    config = load_config("config.yaml")
    # Create agents
    layout = getLayout()
    exits  = getExitsPos(layout)

    all_sprites = pygame.sprite.Group()
    all_walls   = pygame.sprite.Group()
    all_agents  = pygame.sprite.Group()
    all_fires   = pygame.sprite.Group()
    all_smokes  = pygame.sprite.Group()
    all_alarms  = pygame.sprite.Group()
    createWalls()
    createAlarm()
  
    num_agents = config.get("simulation", {}).get("num_agents", NUM_AGENTS) if config else NUM_AGENTS
    all_agents = initialize_agents(config, num_agents, layout=layout, exits=exits)   
    all_agents_list = list(all_agents)
    all_agents = initialize_families(config, all_agents) 
  
        
    
    agents_saved = []
    agents_dead = []
    stats_file_path = 'simulation_stats.csv'

    createFires()
    
    pause = False
    run   = True
    
    agents_saved = []
    agents_dead = []

    # Main cycle
    i = 0
    print(f"wielkosc layoutu: ({len(layout)}, {len(layout[0])})")
    while run:
        
        CLOCK.tick(FPS)
        
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    pause = not pause

        if pause:
            pygame.mixer.pause()
        else:
            pygame.mixer.unpause()


        if len(agents_saved) + len(agents_dead) == len(all_agents_list):
            gather_agent_data(all_agents_list)
            break

        if not pause:
            
            for agent in all_agents:
                agent.percept(layout)
                agent.checkAlarm(soundAlarm)
                communicate(agent)
                if agent.danger and len(agent.relatives) > 0 and agent.rescue_counter == 0:
                    # print(f"[DEBUG] Agent {agent.id}: Danger detected and relatives present. Activating rescue mode.")
                    agent.rescue_relatives = True
                else:
                    agent.rescue_relatives = False
            
            for agent in all_agents:
                if not agent.synchronized_exit:
                    # print(f"[DEBUG] Agent {agent.id}: Planning exit strategy.")
                    agent.plan_(all_agents_list)
                updateHealth(agent,i)

            if (i%5 == 0): layout = propagateFire(layout)
            if (i%4 == 0): layout = propagateSmoke(layout)

            alarm()

            all_agents.update(all_agents)
            draw()

            # USE TO SAVE THE VIDEO FROM EVACUATION 
            # frame = pygame.surfarray.array3d(SCREEN)  # Pobranie obrazu jako tablicy
            # frame = np.rot90(frame)  # Obrót obrazu
            # frame = np.flip(frame, axis=1)  # Lustrzane odbicie
            # out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # Zapis klatki do wideo
            # 
        
        i+=1

    pygame.mixer.pause()
    time.sleep(2)
    # out.release()
    pygame.quit()
