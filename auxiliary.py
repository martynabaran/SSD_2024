import pygame
from random import choices
from settings import *
from copy import deepcopy


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
	return inLayout(layout, i, j ) and layout[i][j] == 'E'

def isAlarm(layout, i, j):
	return inLayout(layout, i, j ) and layout[i][j] == 'A'

def validPropagation(layout, i, j):
	return not isWall(layout,i,j) and not isFire(layout,i,j) and not isSmoke(layout,i,j) and not isExit(layout,i,j)


# Auxiliar

def getLayout(file):
    # f = open('room_layouts/supermarket.txt', 'r').read()

	#Provide the path

	path = 'room_layouts/supermarket3.txt'
	if(file is None): f = open(path, 'r').read()
	else: f = open(file, 'r').read()
	p = []
	p = [item.split() for item in f.split('\n')[:-1]]
	return p

def getExitsPos(layout):
	return [ [index, row.index('E')] for index, row in enumerate(layout) if 'E' in row]