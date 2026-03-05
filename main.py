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

camioneta_izq = pygame.image.load("imgs/camionetas/camioneta1.png").convert_alpha()
camioneta_der = pygame.image.load("imgs/camionetas/camioneta2.png").convert_alpha()
camioneta_arr = pygame.image.load("imgs/camionetas/camioneta3.png").convert_alpha()
camioneta_abj = pygame.image.load("imgs/camionetas/camioneta4.png").convert_alpha()

aceite_img = pygame.image.load("imgs/aceite.png").convert_alpha()
bidon_img = pygame.image.load("imgs/bidon.png").convert_alpha()
calleH_img = pygame.image.load("imgs/calles/calleH.jpg").convert_alpha()
calleV_img = pygame.image.load("imgs/calles/calleV.jpg").convert_alpha()

#Imagenes de las fuentes
fuentes = []

for i in range(1, 25):
    img = pygame.image.load(f"imgs/fuente/Fuente{i}.png").convert_alpha()
    img = pygame.transform.scale(img, (CELL, CELL))
    fuentes.append(img)

#Imagenes de las cajas
cajas = []

for i in range(1,9):
    img = pygame.image.load(f"imgs/cajas/Caja{i}.png").convert_alpha()
    img = pygame.transform.scale(img,(CELL,CELL))
    cajas.append(img)

estatua1Arr_img = pygame.image.load("imgs/estatuas/estatua1Arr.png").convert_alpha()
estatua1Abj_img = pygame.image.load("imgs/estatuas/estatua1Abj.png").convert_alpha()
estatua2Arr_img = pygame.image.load("imgs/estatuas/estatua2Arr.png").convert_alpha()
estatua2Abj_img = pygame.image.load("imgs/estatuas/estatua2Abj.png").convert_alpha()

#Cesped
cesped_arr_izq = pygame.image.load("imgs/cesped/cesped_arriba_izquierda.png").convert_alpha()
cesped_arr_der = pygame.image.load("imgs/cesped/cesped_arriba_derecha.png").convert_alpha()
cesped_abj_izq = pygame.image.load("imgs/cesped/cesped_abajo_izquierda.png").convert_alpha()
cesped_abj_der = pygame.image.load("imgs/cesped/cesped_abajo_derecha.png").convert_alpha()
cespedC_arr_izq = pygame.image.load("imgs/cesped/cesped_corto_arriba_izquierda.png").convert_alpha()
cespedC_arr_der = pygame.image.load("imgs/cesped/cesped_corto_arriba_derecha.png").convert_alpha()
cespedC_abj_izq = pygame.image.load("imgs/cesped/cesped_corto_abajo_izquierda.png").convert_alpha()
cespedC_abj_der = pygame.image.load("imgs/cesped/cesped_corto_abajo_derecha.png").convert_alpha()

#Camellon
banqueta1_img = pygame.image.load("imgs/camellon/camellon1.png").convert_alpha()
banqueta2_img = pygame.image.load("imgs/camellon/camellon2.png").convert_alpha()
banqueta3_img = pygame.image.load("imgs/camellon/camellon1.png").convert_alpha()

##Edificios
#Hospital
hospital_img = pygame.image.load("imgs/edificios/hospital.png").convert_alpha()
#Restaurante
restaurante_img = pygame.image.load("imgs/edificios/restaurante.png").convert_alpha()
#Central de camiones
central_img = pygame.image.load("imgs/edificios/central.png").convert_alpha()
#Gasolinera
gasolinera_img = pygame.image.load("imgs/edificios/gasolinera.png").convert_alpha()
#Casas
casas1_img = pygame.image.load("imgs/edificios/casas1.png").convert_alpha()
casas2_img = pygame.image.load("imgs/edificios/casas2.png").convert_alpha()
casas3_img = pygame.image.load("imgs/edificios/casas3.png").convert_alpha()
casas4_img = pygame.image.load("imgs/edificios/casas4.png").convert_alpha()
#Edificios
edificio1_img = pygame.image.load("imgs/edificios/edificio1.png").convert_alpha()
edificio2_img = pygame.image.load("imgs/edificios/edificio2.png").convert_alpha()

# Escalar imágenes al tamaño de celda
camioneta_izq = pygame.transform.scale(camioneta_izq, (CELL, CELL))
camioneta_der = pygame.transform.scale(camioneta_der, (CELL, CELL))
camioneta_arr = pygame.transform.scale(camioneta_arr, (CELL, CELL))
camioneta_abj = pygame.transform.scale(camioneta_abj, (CELL, CELL))
aceite_img = pygame.transform.scale(aceite_img, (CELL, CELL))
bidon_img = pygame.transform.scale(bidon_img, (CELL, CELL))
calleH_img = pygame.transform.scale(calleH_img, (CELL, CELL))
calleV_img = pygame.transform.scale(calleV_img, (CELL, CELL))
estatua1Arr_img = pygame.transform.scale(estatua1Arr_img, (CELL, CELL))
estatua1Abj_img = pygame.transform.scale(estatua1Abj_img, (CELL, CELL))
estatua2Arr_img = pygame.transform.scale(estatua2Arr_img, (CELL, CELL))
estatua2Abj_img = pygame.transform.scale(estatua2Abj_img, (CELL, CELL))

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
direccion = "derecha"
fuel=100
score=0
time_seconds=0

# timers
second_timer=0
fuel_timer=0
caja_frame = 0
caja_timer = 0

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

    caja_timer += dt

    if caja_timer >= 250:  # 1 segundo
        caja_timer = 0
        caja_frame = (caja_frame + 1) % 8

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
            nuevo_x, nuevo_y = path.pop(0)

            if nuevo_x > agent[0]:
                direccion = "derecha"
            elif nuevo_x < agent[0]:
                direccion = "izquierda"
            elif nuevo_y > agent[1]:
                direccion = "abajo"
            elif nuevo_y < agent[1]:
                direccion = "arriba"

            agent[0],agent[1] = nuevo_x, nuevo_y

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
                if y in [1,5,7,10,12,16]:
                    screen.blit(calleH_img, rect)
                else:
                    screen.blit(calleV_img, rect)
            elif grid[y][x] == 3: # FUENTE
                pygame.draw.rect(screen, WATER_BLUE, rect)
            else:
                pygame.draw.rect(screen, BUILDING, rect)

    # Coordenadas de ciertas calles
    # Columna 1, las verticales
    calle1_cuadrado=(0,5)
    calle2_cuadrado=(0,7)
    calle3_cuadrado=(0,10)
    calle4_cuadrado=(0,12)
    # Rotonda, las verticales
    calle5_cuadrado=(2,7)
    calle6_cuadrado=(2,10)
    calle7_cuadrado=(7,7)
    calle8_cuadrado=(7,10)
    # Columna 9, las verticales
    calle9_cuadrado=(9,5)
    calle10_cuadrado=(9,7)
    calle11_cuadrado=(9,10)
    calle12_cuadrado=(9,12)
    # Columna 13, las verticales
    calle13_cuadrado=(13,5)
    calle14_cuadrado=(13,12)
    # Columna 17, las verticales
    calle15_cuadrado=(17,5)
    calle16_cuadrado=(17,12)
    # Columna 21, las verticales
    calle17_cuadrado=(21,5)
    calle18_cuadrado=(21,12)
    # Columna 25, las verticales
    calle19_cuadrado=(25,5)
    calle20_cuadrado=(25,12)
    # Columna 29, las verticales
    calle21_cuadrado=(29,5)
    calle22_cuadrado=(29,7)
    calle23_cuadrado=(29,10)
    calle24_cuadrado=(29,12)
    
    #Mostrar imagenes de las calles
    calles_verticales = [
        (0,5),(0,7),(0,10),(0,12),
        (2,7),(2,10),(7,7),(7,10),
        (9,5),(9,7),(9,10),(9,12),
        (13,5),(13,12),
        (17,5),(17,12),
        (21,5),(21,12),
        (25,5),(25,12),
        (29,5),(29,7),(29,10),(29,12)
    ]

    for x,y in calles_verticales:
        screen.blit(calleV_img, (x*CELL, y*CELL))

    for d in deliveries:
        screen.blit(cajas[caja_frame], (d[0]*CELL, d[1]*CELL))

    for b in time_blocks:
        screen.blit(aceite_img, (b[0]*CELL, b[1]*CELL))

    screen.blit(bidon_img, (gas_point[0]*CELL, gas_point[1]*CELL))
    
    if direccion == "izquierda":
        img = camioneta_izq
    elif direccion == "derecha":
        img = camioneta_der
    elif direccion == "arriba":
        img = camioneta_arr
    else:
        img = camioneta_abj

    screen.blit(img, (agent[0]*CELL, agent[1]*CELL))

    # UI
    txt1=font.render(f"Tiempo: {time_seconds}s",True,WHITE)
    txt2=font.render(f"Gasolina: {fuel}%",True,WHITE)
    txt3=font.render(f"Entregas: {score}/{TOTAL_DELIVERIES}",True,WHITE)

    screen.blit(txt1,(20,20))
    screen.blit(txt2,(20,50))
    screen.blit(txt3,(20,80))

    # Coordenadas de la fuente
    index = 0

    for y in range(11, 5, -1):      # filas
        for x in range(3, 7):       # columnas
            screen.blit(fuentes[index], (x*CELL, y*CELL))
            index += 1

    # Coordenadas de las estatuas
    estatuas = [
        (estatua1Arr_img, (1,8)),
        (estatua1Abj_img, (1,9)),
        (estatua2Arr_img, (8,8)),
        (estatua2Abj_img, (8,9))
    ]


    def cortar_tiles(img, cols, rows):
        tiles = []

        w, h = img.get_size()
        tile_w = w // cols
        tile_h = h // rows

        for r in range(rows):
            for c in range(cols):

                rect = pygame.Rect(
                    c * tile_w,
                    r * tile_h,
                    tile_w,
                    tile_h
                )

                tile = img.subsurface(rect)
                tile = pygame.transform.scale(tile, (CELL, CELL))

                tiles.append(tile)

        return tiles

    #Cesped
    tiles_arr_izq = cortar_tiles(cesped_arr_izq, 3, 3)
    tiles_arr_der = cortar_tiles(cesped_arr_der, 3, 3)
    tiles_abj_izq = cortar_tiles(cesped_abj_izq, 3, 3)
    tiles_abj_der = cortar_tiles(cesped_abj_der, 3, 3)
    tilesC_arr_izq = cortar_tiles(cespedC_arr_izq, 1, 2)
    tilesC_arr_der = cortar_tiles(cespedC_arr_der, 1, 2)
    tilesC_abj_izq = cortar_tiles(cespedC_abj_izq, 1, 2)
    tilesC_abj_der = cortar_tiles(cespedC_abj_der, 1, 2)

    #Camellon
    banqueta1_tiles = cortar_tiles(banqueta1_img, 7, 2)
    banqueta2_tiles = cortar_tiles(banqueta2_img, 3, 2)
    banqueta3_tiles = cortar_tiles(banqueta3_img, 7, 2)

    ##Edificios
    #Hospital
    hospital_tiles = cortar_tiles(hospital_img, 3, 5)
    #Restaurante
    restaurante_tiles = cortar_tiles(restaurante_img, 3, 5)
    #Central
    central_tiles = cortar_tiles(central_img, 3, 5)
    #Gasolinera
    gasolinera_tiles = cortar_tiles(gasolinera_img, 3, 5)
    #Casas
    casas1_tiles = cortar_tiles(casas1_img, 3, 5)
    casas2_tiles = cortar_tiles(casas2_img, 3, 5)
    casas3_tiles = cortar_tiles(casas3_img, 3, 5)
    casas4_tiles = cortar_tiles(casas4_img, 3, 5)
    #Edificios
    edificio1_tiles = cortar_tiles(edificio1_img, 3, 5)
    edificio2_tiles = cortar_tiles(edificio2_img, 3, 5)

    def dibujar_bloque(tiles, start_x, start_y, cols, rows):

        i = 0

        for y in range(rows):
            for x in range(cols):

                screen.blit(
                    tiles[i],
                    ((start_x + x) * CELL, (start_y + y) * CELL)
                )

                i += 1

    #Cesped
    dibujar_bloque(tiles_arr_izq, 1, 2, 3, 3)
    dibujar_bloque(tiles_arr_der, 6, 2, 3, 3)
    dibujar_bloque(tiles_abj_izq, 1, 13, 3, 3)
    dibujar_bloque(tiles_abj_der, 6, 13, 3, 3)
    dibujar_bloque(tilesC_arr_izq, 1, 5, 1, 2)
    dibujar_bloque(tilesC_arr_der, 8, 5, 1, 2)
    dibujar_bloque(tilesC_abj_izq, 1, 11, 1, 2)
    dibujar_bloque(tilesC_abj_der, 8, 11, 1, 2)

    #Camellon
    dibujar_bloque(banqueta1_tiles, 10, 8, 7, 2)
    dibujar_bloque(banqueta2_tiles, 18, 8, 3, 2)
    dibujar_bloque(banqueta3_tiles, 22, 8, 7, 2)

    ##Edificios
    #Hospital
    dibujar_bloque(hospital_tiles, 10, 11, 3, 5)
    #Restaurante
    dibujar_bloque(restaurante_tiles, 14, 11, 3, 5)
    #Central
    dibujar_bloque(central_tiles, 22, 11, 3, 5)
    #Gasolinera
    dibujar_bloque(gasolinera_tiles, 26, 11, 3, 5)
    #Casas
    dibujar_bloque(casas1_tiles, 10, 2, 3, 5)
    dibujar_bloque(casas2_tiles, 14, 2, 3, 5)
    dibujar_bloque(casas3_tiles, 18, 2, 3, 5)
    dibujar_bloque(casas4_tiles, 18, 11, 3, 5)
    #Edificios
    dibujar_bloque(edificio1_tiles, 22, 2, 3, 5)
    dibujar_bloque(edificio2_tiles, 26, 2, 3, 5)

    #Mostrar imagenes de las estatuas
    for img,(x,y) in estatuas:
        screen.blit(img,(x*CELL,y*CELL))

    pygame.display.flip()
