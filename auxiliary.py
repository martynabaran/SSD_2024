import pygame
from random import choices
from settings import *
from copy import deepcopy
import yaml
import os

# Predicates
def inLayout(layout, i, j):
    return (0<= i < len(layout)) and (0 <= j < len(layout[0]))

def isFire(layout, i, j):
	return inLayout(layout, i, j ) and layout[i][j] == 'F'

def isSmoke(layout, i, j):
	return inLayout(layout, i, j ) and layout[i][j] == 'S'

def isWall(layout, i, j):
	return inLayout(layout, i, j ) and layout[i][j] == 'W'

def isExit(layout, i, j):
	return inLayout(layout, i, j) and layout[i][j] == 'E'

def isAlarm(layout, i, j):
	return inLayout(layout, i, j ) and layout[i][j] == 'A'

def validPropagation(layout, i, j):
	return not isWall(layout,i,j) and not isFire(layout,i,j) and not isSmoke(layout,i,j) and not isExit(layout,i,j)


# Auxiliar

# def getLayout(file):
#     # f = open('room_layouts/supermarket.txt', 'r').read()

# 	#Provide the path

# 	path = 'room_layouts/supermarket3.txt'
# 	if(file is None): f = open(path, 'r').read()
# 	else: f = open(file, 'r').read()
# 	p = []
# 	p = [item.split() for item in f.split('\n')[:-1]]
# 	return p

def getLayout(config_file='config.yaml', default_layout='room_layouts/supermarket3.txt'):
    """
    Wczytuje układ pomieszczenia na podstawie pliku YAML.
    Jeśli w YAML nie zdefiniowano układu, korzysta z domyślnego pliku.
    """
    layout_path = default_layout  # Domyślny układ

    try:
        # Wczytanie pliku konfiguracyjnego
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Sprawdzenie, czy layout jest zdefiniowany w pliku YAML
        layout_path = config.get('simulation', {}).get('agent_attributes', {}).get('layout', default_layout)
    except FileNotFoundError:
        print(f"Plik konfiguracyjny '{config_file}' nie został znaleziony. Używany będzie domyślny układ.")

    # Wczytanie układu
    if not os.path.exists(layout_path):
        print(f"Nie znaleziono pliku z układem: {layout_path}. Używany będzie domyślny układ: {default_layout}.")
        layout_path = default_layout

    with open(layout_path, 'r') as f:
        layout = [line.split() for line in f.read().splitlines()]
    
    return layout
def getExitsPos(layout):
	return [ [index, row.index('E')] for index, row in enumerate(layout) if 'E' in row]