import pygame
import sys
import random
from collections import deque

pygame.init()

WIDTH, HEIGHT = 1200, 720
CELL = 40
COLS = WIDTH // CELL
ROWS = HEIGHT // CELL

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Agente Inteligente - Repartidor")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial",22)

# =========================
# CARGA DE IMÁGENES
# =========================

caja_img = pygame.image.load("imgs/caja.png").convert_alpha()
aceite_img = pygame.image.load("imgs/aceite.png").convert_alpha()
camioneta_img = pygame.image.load("imgs/camioneta.png").convert_alpha()
bidon_img = pygame.image.load("imgs/bidon.png").convert_alpha()

# Escalar imágenes al tamaño de celda
caja_img = pygame.transform.scale(caja_img, (CELL, CELL))
aceite_img = pygame.transform.scale(aceite_img, (CELL, CELL))
camioneta_img = pygame.transform.scale(camioneta_img, (CELL, CELL))
bidon_img = pygame.transform.scale(bidon_img, (CELL, CELL))

WHITE=(255,255,255)
GRAY=(60,60,60)
ROAD=(90,90,90)
BUILDING=(30,30,30)
YELLOW=(255,220,0)
RED=(200,50,50)
GREEN=(40,200,40)
BLACK=(0,0,0)
WATER_BLUE=(0, 191, 255)

# =========================
# MAPA
# =========================

grid=[[0]*COLS for _ in range(ROWS)]

#columnas completas
for r in [1,16]:
    for c in range(COLS):
        grid[r][c]=1

#Filas completas
for c in [0, 9, 17, 21, 29]:
    for r in range(ROWS):
        grid[r][c]=1

for r in [0,17]:
    for c in range(COLS):
        grid[r][c]=0


#Tramos
# Calles Fuente
for c in range(2, 8): # 5, 2 a 7
    grid[5][c] = 1

for c in range(2, 8): # 12, 2 a 7
    grid[12][c] = 1
    
for r in range(5,13):
    grid[r][2] = 1

for r in range(5,13):
    grid[r][7] = 1

# union rotonda
for r in range(1,6): # 1-5, 4
    grid[r][4] = 1

for r in range(1,6): # 1-5, 4
    grid[r][5] = 1

for r in range(12,17):
    grid[r][4] = 1

for r in range(12,17):
    grid[r][5] = 1

for c in range(0,3):
    grid[7][c] = 1
for c in range(0,3):
    grid[10][c] = 1

for c in range(7,10):
    grid[7][c] = 1
for c in range(7,10):
    grid[10][c] = 1

#Boulevard
for c in range(9,30):
    grid[7][c] = 1
for c in range(9,30):
    grid[10][c] = 1

#Boulevatd Vertical
for r in range(1,8):
    grid[r][13] = 1
for r in range(10,17):
    grid[r][13] = 1


for r in range(1,8):
    grid[r][25] = 1
for r in range(10,17):
    grid[r][25] = 1
    
# Fuente
for r in range(6,12):
    for c in range(3,7):
        grid[r][c] = 3

# =========================
# AGENTE
# =========================

agent=[1,16]
fuel=100
score=0
time_seconds=0

# timers
second_timer=0
fuel_timer=0

#Funcion para aleatorios

def lugares_random(count, existing_locations):
    locations = []
    while len(locations) < count:
        rx = random.randint(0, COLS - 1)
        ry = random.randint(0, ROWS - 1)
        
        if grid[ry][rx] == 1 and (rx, ry) not in locations and (rx, ry) not in existing_locations:
            if [rx, ry] != agent:
                locations.append((rx, ry))
    return locations

# =========================
# OBJETOS
# =========================

deliveries=lugares_random(10,[])

TOTAL_DELIVERIES=10
game_over=False

gas_station=(28,15)
gas_point=(28,16)

time_blocks=lugares_random(7,deliveries) # aceite

# =========================
# BFS
# =========================
def neighbors(x, y):
    moves = []
    def add(nx, ny):
        if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] == 1:
            moves.append((nx, ny))

    # --- CALLES HORIZONTALES ---
    if y == 1: add(x - 1, y)      # Fila 1: Izquierda
    if y == 16: add(x + 1, y)     # Fila 16: Derecha
    if y == 5: add(x - 1, y)      # Arriba fuente: Izquierda
    if y == 12: add(x + 1, y)     # Abajo fuente: Derecha
    if y == 7: add(x + 1, y)      # Boulevard: Derecha
    if y == 10: add(x - 1, y)     # Boulevard: Izquierda

    # --- CALLES VERTICALES ---
    if x in [0, 9, 17]: add(x, y + 1) # Bajan
    if x in [21, 29]: add(x, y - 1)   # Suben
    
    # Lados Fuente
    if x == 2: add(x, y + 1)          # Baja
    if x == 7: add(x, y - 1)          # Sube
    
    # Cruces de Rotonda
    if x in [4, 5]:
        if y <= 7: add(x, y + 1)      # Entran por arriba
        if y >= 10: add(x, y - 1)     # Entran por abajo

    # Boulevards Verticales
    if x == 13: add(x, y - 1)         # Sube
    if x == 25: add(x, y + 1)         # Baja

    return moves


def bfs(start,goal):
    q=deque([start])
    visited={start:None}

    while q:
        cur=q.popleft()
        if cur==goal:
            break

        for nx,ny in neighbors(*cur):
            if (nx,ny) not in visited:
                visited[(nx,ny)]=cur
                q.append((nx,ny))

    path=[]
    cur=goal
    while cur!=start and cur in visited:
        path.append(cur)
        cur=visited[cur]
    path.reverse()
    return path


# =========================
# DECISION
# =========================

path=[]
emergency=False

def choose_target():
    global path, emergency

    if fuel < 20:
        emergency = True
        path = bfs(tuple(agent), gas_point)
        return

    emergency = False

    best = None
    best_len = 9999

    for d in deliveries:
        p = bfs(tuple(agent), d)
        if len(p) > 0 and len(p) < best_len:
            best_len = len(p)
            best = d

    if best:
        path = bfs(tuple(agent), best)

# =========================
# LOOP
# =========================

move_timer=0

while True:
    dt=clock.tick(60)
    move_timer+=dt

    if not game_over:
        second_timer+=dt
        fuel_timer+=dt

    #tiempo
    if second_timer>=1000:
        time_seconds+=1
        second_timer=0

    #gasolina
    if fuel_timer>=2000:
        fuel=max(0,fuel-5)
        fuel_timer=0

        if fuel<20:
            emergency=True
            path.clear()

    if tuple(agent) == gas_point:
                if fuel < 100: # Carga si no está lleno
                    fuel = 100
                    emergency = False


    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit()
            sys.exit()

    speed=120 if emergency else 250

    if game_over:
        speed=999999999


    if move_timer>speed:
        move_timer=0

        if not path and not game_over:
            choose_target()


        if path:
            agent[0],agent[1]=path.pop(0)

            # bolas rojas
            if tuple(agent) in deliveries and not emergency:
                deliveries.remove(tuple(agent))
                time_seconds+=1
                score+=1

                if score>=TOTAL_DELIVERIES:
                    game_over=True
                    path=[]


            # cuadrados negros
            if tuple(agent) in time_blocks and not emergency:
                time_seconds+=2

            # gasolinera
            if tuple(agent)==gas_station:
                if emergency:
                    time_seconds+=3
                    fuel=100
                    emergency=False
                    path.clear()

    # ================= DIBUJO =================

    screen.fill(BUILDING)

    for y in range(ROWS):
        for x in range(COLS):
            rect = (x*CELL, y*CELL, CELL, CELL)
            if grid[y][x] == 1:
                pygame.draw.rect(screen, ROAD, rect)
            elif grid[y][x] == 3: # FUENTE
                pygame.draw.rect(screen, WATER_BLUE, rect)
            else:
                pygame.draw.rect(screen, BUILDING, rect)

    for d in deliveries:
        screen.blit(caja_img, (d[0]*CELL, d[1]*CELL))

    for b in time_blocks:
        screen.blit(aceite_img, (b[0]*CELL, b[1]*CELL))

    screen.blit(bidon_img, (gas_point[0]*CELL, gas_point[1]*CELL))
    screen.blit(camioneta_img, (agent[0]*CELL, agent[1]*CELL))

    # UI
    txt1=font.render(f"Tiempo: {time_seconds}s",True,WHITE)
    txt2=font.render(f"Gasolina: {fuel}%",True,WHITE)
    txt3=font.render(f"Entregas: {score}/{TOTAL_DELIVERIES}",True,WHITE)

    screen.blit(txt1,(20,20))
    screen.blit(txt2,(20,50))
    screen.blit(txt3,(20,80))

    pygame.display.flip()
