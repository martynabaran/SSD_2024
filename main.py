import pygame
from auxiliary import *
from random import choices
from settings import *
from spirites3 import *
from copy import deepcopy
import time
import uuid
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


def propagateFire(layout):
    spread    = [True, False] #either it spreads or not
    propagate = [FIRE,  1-FIRE]
    smoke     = [SMOKE, 1-SMOKE]
    row       = [-1, 0, 0, 1]
    col       = [0, -1, 1, 0]

    new_fires = []
    for fire in all_fires:
        i = random.randrange(0, 4)
        x = fire.x + row[i]
        y = fire.y + col[i]

        if (x > len(layout)-1 or y > len(layout[0])-1): continue

        propagate_ = propagate
        if (isSmoke(layout,x, y)):
            propagate_[0] += (1-propagate_[1])/2
            propagate_[1] = 1 - propagate_[0]
        if (choices(spread, propagate_)[0] and not isWall(layout,x,y) and not isFire(layout,x,y) and not isExit(layout,x,y)):
            for smoke in all_smokes:
                if smoke.x == x and smoke.y == y:
                    all_smokes.remove(smoke)
                    break
            new_fires.append([x,y])

    for fire in new_fires:
        addFire(fire[0], fire[1])

    return layout


def propagateSmoke(layout):
    spread = [True, False]        #either it spreads or not
    wind   = [0.4, 0.3, 0.2, 0.1]
    smk    = [SMOKE, 1-SMOKE]
    row    = [-1, 0, 0, 1]
    col    = [0, -1, 1, 0]
    
    for fire in all_fires:

        for i in range(len(row)):

            x = fire.x + row[i]
            y = fire.y + col[i]

            if (x > len(layout)-1 or y > len(layout[0])-1): continue

            if (choices(spread, smk)[0] and validPropagation(layout,x,y)):
                addSmoke(x,y)
            if (choices(spread, smk)[0] and validPropagation(layout,x,y)):
                addSmoke(x,y)
            if (choices(spread, smk)[0] and validPropagation(layout,x,y)):
                addSmoke(x,y)
            if (choices(spread, smk)[0] and validPropagation(layout,x,y)):
                addSmoke(x,y)


    for smoke in all_smokes:

        for i in range(len(row)):

            x = smoke.x + row[i]
            y = smoke.y + col[i]

            if (x > len(layout)-1 or y > len(layout[0])-1): continue

            go = choices(spread, smk)[0]
            if (go and validPropagation(layout,x,y)):
                addSmoke(x, y)
            if (go and validPropagation(layout,x,y)):
                addSmoke(x, y)
            if (go and validPropagation(layout,x,y)):
                addSmoke(x, y)
            if (go and validPropagation(layout,x,y)):
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

def assertInRange(speaker, listener):
    return abs(speaker.x - listener.x)<=VOL_RANGE and abs(speaker.y - listener.y)<=VOL_RANGE

def communicate(speaker):
    if (not speaker.isCommunicative()):
        return
    for listener in all_agents:
        if (speaker.getID() == listener.getID()): continue
        if assertInRange(speaker, listener):
            listener.receiveMessage(speaker.getLayout())
        # if listener.getID() in speaker.relatives:
        # 	print(f"PRZED: speaker danger = {speaker.getDangerState()} listener danger = {listener.getDangerState()}")
            
        # 	if speaker.getDangerState() or listener.getDangerState():				
        # 		speaker.danger = listener.danger = True

        # 	print(f"speaker {speaker.getID()} informuje b {listener.getID()}")
        # 	listener.receiveMessagefromRelative(speaker.getLayout())
        # 	print(f"speaker danger = {speaker.getDangerState()} listener danger = {listener.getDangerState()}")

import csv
import os
from collections import Counter
# Funkcja do zapisywania statystyk do pliku CSV
def save_simulation_stats(file_path, num_agents, strategy_counts, agents_saved, agents_dead, strategies, risk_levels):
    # Sprawdzenie czy plik już istnieje, jeśli nie, to zapisujemy nagłówki
    file_exists = os.path.exists(file_path)
    
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            # Zapisujemy nagłówki do pliku, jeśli to pierwszy zapis
            writer.writerow([
                'NumAgents', 'Strategy', 'RiskLevel', 'AgentsSaved', 'AgentsDead', 'SavedGroup', 'DeadGroup'
            ])
        
        # Zliczamy ile agentów przeżyło i z jakiej grupy
        saved_group = [agent.strategy for agent in agents_saved]
        dead_group = [agent.strategy for agent in agents_dead]
        
        for strategy in strategies:
            # Zapisujemy wiersz z wynikami
            writer.writerow([
                num_agents, strategy, Counter(risk_levels)[strategy], len(agents_saved), len(agents_dead),
                Counter(saved_group).get(strategy, 0), Counter(dead_group).get(strategy, 0)
            ])
import cv2

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

# Main
if __name__ == "__main__":
    global SCREEN, CLOCK, layout, all_sprites, all_agents, all_walls, all_fires, all_smokes, exits, soundAlarm

    soundAlarm = False
    fps = 30
    pygame.init()
    pygame.display.set_caption("Evacuation Simulation")
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT+40))
    CLOCK = pygame.time.Clock()
    SCREEN.fill(BLACK)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Format wideo (AVI)
    out = cv2.VideoWriter('simulationRelatives3.avi', fourcc, FPS, (WIDTH, HEIGHT+40))


    # Create agents
    layout = getLayout(None)
    exits  = getExitsPos(layout)

    all_sprites = pygame.sprite.Group()
    all_walls   = pygame.sprite.Group()
    all_agents  = pygame.sprite.Group()
    all_fires   = pygame.sprite.Group()
    all_smokes  = pygame.sprite.Group()
    all_alarms  = pygame.sprite.Group()
    createWalls()
    createAlarm()
    #fire_alarm = pygame.mixer.Sound("FireAlarm.wav")
    from collections import Counter

    STRATEGY = ['nearest_exit', 'safest_exit', 'least_crowded_exit']
    status_list = []  
    risk_levels = []
    colors = {'nearest_exit' : DARKRED	, 'safest_exit': PURPLE, 'least_crowded_exit': GREEN}
    for i in range(NUM_AGENTS):
        # strategy = random.choice(STRATEGY)
        strategy = STRATEGY[i % 3]
        status_list.append(strategy)
        # player = Agent(i+1, deepcopy(layout), exits, HEALTH_POINTS, 1, True, strategy=strategy, color=colors[strategy])
        player = Agent(identifier=i+1,layout=deepcopy(layout),exits=exits,health=HEALTH_POINTS,risk=random.uniform(0, 1),communicates=True,strategy=strategy,color=colors[strategy])
        all_sprites.add(player)
        all_agents.add(player)
        risk_levels.append(player.risk)
        
    all_agents_list = list(all_agents) 
    colors = [DARKPURPLE, ROYALPURPLE, LAVENDER]
    for i in range(2):
        agent_a = random.choice(all_agents_list)
        agent_b = random.choice([a for a in all_agents_list if a != agent_a])  # Unikamy relacji do samego siebie
        agent_a.getRelatives().append(agent_b.getID())
        agent_b.getRelatives().append(agent_a.getID())
        agent_a.communicates = True
        agent_b.communicates = True
        agent_a.image.fill(colors[i])
        agent_b.image.fill(colors[i])
        if agent_a.getDangerState() or agent_b.getDangerState():				
                agent_a.danger = agent_b.danger = True
        # print(f"A = {agent_a.getID()} {agent_a.getRelatives()}, B = {agent_b.getID()} {agent_b.getRelatives()}")
    
    agents_saved = []
    agents_dead = []
    status_counts = Counter(status_list)
    stats_file_path = 'simulation_stats.csv'
# Wypisz ile agentów ma każdy status
    for status, count in status_counts.items():
        print(f"Status '{status}': {count} agentów")
    createFires()
    
    pause = False
    run   = True
    
    agents_saved = []
    agents_dead = []

    # Main cycle
    i = 0
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


        if len(agents_saved) + len(agents_dead) == NUM_AGENTS:
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

            frame = pygame.surfarray.array3d(SCREEN)  # Pobranie obrazu jako tablicy
            frame = np.rot90(frame)  # Obrót obrazu
            frame = np.flip(frame, axis=1)  # Lustrzane odbicie
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # Zapis klatki do wideo
            # 
        
        i+=1

    pygame.mixer.pause()
    time.sleep(2)
    # out.release()
    pygame.quit()

    # for agent in all_agents:
    #     if not agent.isDead():
    #         agents_saved.append(agent)
    #     else:
    #         agents_dead.append(agent)

    # # Zliczanie, ilu przeżyło i zginęło
    # print(f"Liczba agentów: {NUM_AGENTS}")
    # print(f"Przeżyło: {len(agents_saved)}")
    # print(f"Zginęło: {len(agents_dead)}")
    
    
    # agents_strategy_count = Counter([agent.strategy for agent in all_agents_list])
    # print(f"Statystyki strategii:")
    # for strategy, count in agents_strategy_count.items():
    #     print(f"Strategia {strategy}: {count} agentów")
        
    # low_risk = [agent for agent in all_agents_list if agent.risk < 0.3]
    # medium_risk = [agent for agent in all_agents_list if 0.3 <= agent.risk < 0.7]
    # high_risk = [agent for agent in all_agents_list if agent.risk >= 0.7]
    
    # print(f"Agenci z niskim ryzykiem: {len(low_risk)}")
    # print(f"Agenci ze średnim ryzykiem: {len(medium_risk)}")
    # print(f"Agenci z wysokim ryzykiem: {len(high_risk)}")
    # summary = {
    #     "total_agents": NUM_AGENTS,
    #     "agents_saved": len(agents_saved),
    #     "agents_dead": len(agents_dead),
    #     "agents_by_strategy": dict(agents_strategy_count),
    #     "agents_by_risk": {
    #         "low": len(low_risk),
    #         "medium": len(medium_risk),
    #         "high": len(high_risk)
    #     }
    # }
    # print("Podsumowanie symulacji:")
    # for key, value in summary.items():
    #     print(f"{key}: {value}")