import pygame
import sys
import random
import json
import os
import numpy as np

#===============================
# COnfiguracion/inicializacion
#===============================

pygame.init()
pygame.mixer.init()
# Parametros del juego
WIDTH, HEIGHT = 1200, 720
CELL = 40
COLS = WIDTH // CELL
ROWS = HEIGHT // CELL
MEMORY_FILE = "q_learning_data.json" #aqui se guarda lo que aprende

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Agente Inteligente - Repartidor")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial",22)

#===============================
# Colores
#===============================
WHITE=(255,255,255)
GRAY=(60,60,60)
ROAD=(90,90,90)
BUILDING=(30,30,30)
YELLOW=(255,220,0)
RED=(200,50,50)
GREEN=(40,200,40)
BLACK=(0,0,0)
WATER_BLUE=(0, 191, 255)

# Parámetros de aprendizaje
q_table = {}
actions = [0, 1, 2, 3] # 0 Arriba 1 Abajo 2 Izquierda 3 Derecha
alpha = 0.1
gamma = 0.9
epsilon = 0.8
epsilon_min = 0.05  # El mínimo de azar permitido
epsilon_decay = 0.99 # Factor de reducción
# Stats del agente
total_completed = 0
total_failed = 0
current_oil_touches = 0
state_game = "MENU"
TOTAL_DELIVERIES= 10
gas_station=(28,15)
gas_point=(28,16)
second_timer = 0
fuel_timer=0
move_timer = 0
caja_timer = 0
caja_frame = 0
direccion = 0
# stats del enemigo
enemy_pos = [29, 1]  # Aparece en una esquina opuesta
enemy_active = False
lives = 3
deliveries_to_spawn_enemy = 3
death_reason = ""
closed_roads = []
#===============
# FUNCIONES
#===============

def save_memory():
    data_to_save = {
            "total_completed": total_completed,
            "total_failed": total_failed,
            "q_table": {str(k): v for k, v in q_table.items()}
        }
    with open(MEMORY_FILE, "w") as f:
        json.dump(data_to_save, f)

def load_memory():
    global q_table, total_completed, total_failed
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            loaded_data = json.load(f)
            # Cargamos los stats
            total_completed = loaded_data.get("total_completed", 0)
            total_failed = loaded_data.get("total_failed", 0)
            # Reconvertimos los strings a tuplas para la q_table
            loaded_q = loaded_data.get("q_table", {})
            q_table = {eval(k): v for k, v in loaded_q.items()}


def get_q_values(state):
    if state not in q_table:
        q_table[state] = [0.0] * 4
    return q_table[state]

def reset_simulation(success=True):
    global agent, fuel, score, deliveries, time_blocks, game_over, time_seconds
    global current_oil_touches, total_completed, total_failed, state_game
    
    if success: 
        total_completed += 1
        if epsilon > epsilon_min:
            epsilon *= epsilon_decay
    else: total_failed += 1

    save_memory()
    state_game = "RESULTS" 


#Funcion para aleatorios
def lugares_random(count, existing_locations, agent):
    locations = []
    while len(locations) < count:
        rx = random.randint(0, COLS - 1)
        ry = random.randint(0, ROWS - 1)
        
        if grid[ry][rx] == 1 and (rx, ry) not in locations and (rx, ry) not in existing_locations:
            if [rx, ry] != agent:
                locations.append((rx, ry))
    return locations

#Sentido de las calles
def neighbors(x, y):
            moves = []
            def add(nx, ny):
                if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] == 1 and (nx, ny) not in closed_roads:
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

def choose_action(state):
            if random.random() < epsilon:
                return random.choice(actions)
            return np.argmax(get_q_values(state))

def update_q(state, action, reward, next_state):
    old_q = get_q_values(state)[action]
    next_max = max(get_q_values(next_state))
    new_q = old_q + alpha * (reward + gamma * next_max - old_q)
    q_table[state][action] = new_q

def move_enemy(enemy_p, agent_p):
    ex, ey = enemy_p
    ax, ay = agent_p
    
    possible_moves = []
    if ax > ex: possible_moves.append((ex + 1, ey))
    if ax < ex: possible_moves.append((ex - 1, ey))
    if ay > ey: possible_moves.append((ex, ey + 1))
    if ay < ey: possible_moves.append((ex, ey - 1))
    
    for move in possible_moves:
        nx, ny = move
        if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] == 1:
            return [nx, ny] # Retorna el primer movimiento válido hacia el agente
    return enemy_p

def move_enemy_legal(enemy_p, agent_p):
    ex, ey = enemy_p
    # mov permitidos por sentidos de calle
    posibles_pasos = neighbors(ex, ey)
    
    if not posibles_pasos:
        return enemy_p 
    
    mejor_paso = posibles_pasos[0]
    distancia_minima = float('inf')
    
    for paso in posibles_pasos:
        dist = abs(paso[0] - agent_p[0]) + abs(paso[1] - agent_p[1])
        if dist < distancia_minima:
            distancia_minima = dist
            mejor_paso = paso
            
    return list(mejor_paso)

#================
# Texturas
#+++++++++++++++++

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

def dibujar_bloque(tiles, start_x, start_y, cols, rows):

        i = 0

        for y in range(rows):
            for x in range(cols):

                screen.blit(
                    tiles[i],
                    ((start_x + x) * CELL, (start_y + y) * CELL)
                )

                i += 1

# =========================
# CARGA DE IMÁGENES
# =========================

camioneta_izq = pygame.image.load("imgs/camionetas/camioneta1.png").convert_alpha()
camioneta_der = pygame.image.load("imgs/camionetas/camioneta2.png").convert_alpha()
camioneta_arr = pygame.image.load("imgs/camionetas/camioneta3.png").convert_alpha()
camioneta_abj = pygame.image.load("imgs/camionetas/camioneta4.png").convert_alpha()
camionetaB_izq = pygame.image.load("imgs/camionetas/camionetaB1.png").convert_alpha()
camionetaB_der = pygame.image.load("imgs/camionetas/camionetaB2.png").convert_alpha()
camionetaB_arr = pygame.image.load("imgs/camionetas/camionetaB3.png").convert_alpha()
camionetaB_abj = pygame.image.load("imgs/camionetas/camionetaB4.png").convert_alpha()

aceite_img = pygame.image.load("imgs/aceite.png").convert_alpha()
bidon_img = pygame.image.load("imgs/bidon.png").convert_alpha()
obstaculo_img = pygame.image.load("imgs/obstaculo.png").convert_alpha()
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
camionetaB_izq = pygame.transform.scale(camionetaB_izq, (CELL, CELL))
camionetaB_der = pygame.transform.scale(camionetaB_der, (CELL, CELL))
camionetaB_arr = pygame.transform.scale(camionetaB_arr, (CELL, CELL))
camionetaB_abj = pygame.transform.scale(camionetaB_abj, (CELL, CELL))
aceite_img = pygame.transform.scale(aceite_img, (CELL, CELL))
bidon_img = pygame.transform.scale(bidon_img, (CELL, CELL))
obstaculo_img = pygame.transform.scale(obstaculo_img, (CELL, CELL))
calleH_img = pygame.transform.scale(calleH_img, (CELL, CELL))
calleV_img = pygame.transform.scale(calleV_img, (CELL, CELL))
estatua1Arr_img = pygame.transform.scale(estatua1Arr_img, (CELL, CELL))
estatua1Abj_img = pygame.transform.scale(estatua1Abj_img, (CELL, CELL))
estatua2Arr_img = pygame.transform.scale(estatua2Arr_img, (CELL, CELL))
estatua2Abj_img = pygame.transform.scale(estatua2Abj_img, (CELL, CELL))

# Cargar memoria al iniciar
load_memory()

# =========================
# CARGA DE AUDIO
# =========================

music_menu = "audio/menu.mp3"
music_game = "audio/juego.mp3"
music_enemy = "audio/persecucion.mp3"
music_win = "audio/ganar.mp3"
music_lose = "audio/perder.mp3"

current_music = None

# =========================
# FUNCIONES DE AUDIO
# =========================

def play_music(track, loop=True):
    global current_music

    if current_music != track:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(track)

        if loop:
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.play()

        current_music = track

# =========================
# MAPEO
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
# IFS PARA ESTADO DEL JUEGO
#==========================

while True:
    dt = clock.tick(60)
    events = pygame.event.get() # SE OBTIENEN UNA SOLA VEZ
    
    for e in events:
        if e.type == pygame.QUIT:
            save_memory()
            pygame.quit()
            sys.exit()

    if state_game == "MENU":
        play_music(music_menu)

        screen.fill(BLACK)
        screen.blit(font.render("Agente Inteligente - Repartidor", True, YELLOW), (450, 200))
        screen.blit(font.render(f"Completados: {total_completed} | Fallidos: {total_failed}", True, WHITE), (450, 300))
        screen.blit(font.render("Presiona ESPACIO para iniciar", True, GREEN), (450, 400))
        
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                play_music(music_game)
                agent, fuel, score, time_seconds, current_oil_touches = [1, 16], 100, 0, 0, 0
                deliveries = lugares_random(TOTAL_DELIVERIES, [], agent)
                time_blocks = lugares_random(7, deliveries, agent)
                closed_roads = lugares_random(2, deliveries + time_blocks, agent)
                state_game = "PLAYING"

    elif state_game == "PLAYING":
        if not enemy_active:
            play_music(music_game)

        move_timer += dt
        second_timer += dt
        fuel_timer += dt
        caja_timer += dt
        if caja_timer >= 250:
            caja_timer = 0
            caja_frame = (caja_frame + 1) % 8 

        if second_timer >= 1000:
            time_seconds += 1
            second_timer = 0
        if fuel_timer >= 2000:
            fuel = max(0, fuel - 2)
            fuel_timer = 0

        # Lógica de Movimiento Q-Learning
        if move_timer > 150 and fuel > 0:
            move_timer = 0
            
            if fuel <= 30:
                objetivo = gas_point 
            elif deliveries:
                objetivo = min(deliveries, key=lambda d: abs(agent[0]-d[0]) + abs(agent[1]-d[1]))
            else:
                objetivo = agent

            dir_x = 1 if objetivo[0] > agent[0] else (-1 if objetivo[0] < agent[0] else 0)
            dir_y = 1 if objetivo[1] > agent[1] else (-1 if objetivo[1] < agent[1] else 0)
            
            state = (agent[0], agent[1], dir_x, dir_y)
            
            action = choose_action(state)
            
            dist_antes = abs(agent[0]-objetivo[0]) + abs(agent[1]-objetivo[1])

            nx, ny = agent[0], agent[1]
            if action == 0: 
                ny -= 1
                direccion = 1
            elif action == 1: 
                ny += 1
                direccion = 0
            elif action == 2: 
                nx -= 1
                direccion = 3
            elif action == 3: 
                nx += 1
                direccion = 2

            reward = -2 # Castigo base leve por paso

            # Verificación de choque con edificios/sentidos
            if (nx, ny) not in neighbors(agent[0], agent[1]):
                reward = -20
                next_state = state # Si choca, el estado no cambia
            else:
                agent[0], agent[1] = nx, ny
                
                # --- 3. CALCULAR EL NUEVO ESTADO TRAS MOVERSE ---
                dir_x_n = 1 if objetivo[0] > nx else (-1 if objetivo[0] < nx else 0)
                dir_y_n = 1 if objetivo[1] > ny else (-1 if objetivo[1] < ny else 0)
                next_state = (nx, ny, dir_x_n, dir_y_n)

                dist_despues = abs(nx-objetivo[0]) + abs(ny-objetivo[1])

                if fuel <= 30:
                    reward -= 5 # Le entra "pánico" si no tiene gasolina
                
                if dist_despues < dist_antes:
                    reward += 10  # ¡Se acercó!
                elif dist_despues > dist_antes:
                    reward -= 15 
                
                pos_actual = (nx, ny)
                if pos_actual in deliveries:
                    reward = 300
                    deliveries.remove(pos_actual)
                    score += 1
                    if score % 2 == 0 and score < TOTAL_DELIVERIES:
                        objetos_actuales = deliveries + time_blocks + [gas_point, list(enemy_pos)]
                        closed_roads = lugares_random(2, objetos_actuales, agent)

                elif pos_actual in time_blocks:
                    reward -= 30
                    current_oil_touches += 1
                elif pos_actual == gas_point:
                    reward = 200
                    fuel = 100
                    
            update_q(state, action, reward, next_state)

            # --- LÓGICA DEL ENEMIGO ---
            if score >= deliveries_to_spawn_enemy and not enemy_active:
                enemy_active = True
                play_music(music_enemy)

            if enemy_active:
                # El enemigo se mueve un poco más lento que el agente para que sea justo
                if pygame.time.get_ticks() % 2 == 0: 
                    enemy_pos = move_enemy_legal(enemy_pos, agent)

                # Verificar COLISIÓN
                if list(agent) == enemy_pos:
                    lives -= 1
                    agent = [1, 16] # Al atraparlo, ambos vuelven a su lugar 
                    enemy_pos = [29, 1]
                    reward = -200    # Gran castigo para el Q-Learning
                    if lives <= 0:
                        total_failed += 1
                        death_reason = "asalto"
                        save_memory()
                        state_game = "RESULTS"

        if score >= TOTAL_DELIVERIES:
            total_completed += 1
            reward += 500
            if epsilon > epsilon_min:
                epsilon *= epsilon_decay
            save_memory()
            state_game = "RESULTS"

        elif fuel <= 0:
            total_failed += 1
            enemy_pos = [29, 1]
            death_reason = "gas"
            reward -= 300
            save_memory()
            state_game = "RESULTS"
            
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
        
        for x,y in calles_verticales:
            screen.blit(calleV_img, (x*CELL, y*CELL))

        for d in deliveries:
            screen.blit(cajas[caja_frame], (d[0]*CELL, d[1]*CELL))

        for b in time_blocks:
            screen.blit(aceite_img, (b[0]*CELL, b[1]*CELL))

        # --- DIBUJAR CALLES CERRADAS ---
        for cr in closed_roads:
            screen.blit(obstaculo_img, (cr[0]*CELL, cr[1]*CELL))

        screen.blit(bidon_img, (gas_point[0]*CELL, gas_point[1]*CELL))

        if direccion == 3:
            img = camioneta_izq
        elif direccion == 2:
            img = camioneta_der
        elif direccion == 1:
            img = camioneta_arr
        else:
            img = camioneta_abj

        screen.blit(img, (agent[0]*CELL, agent[1]*CELL))

        if enemy_active:
            if direccion == 3:
                img = camionetaB_izq
            elif direccion == 2:
                img = camionetaB_der
            elif direccion == 1:
                img = camionetaB_arr
            else:
                img = camionetaB_abj

            screen.blit(img, (enemy_pos[0]*CELL, enemy_pos[1]*CELL))

        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 40))
        info = font.render(f"Vidas: {lives} | Entregas: {score} | Gas: {fuel}% | Aceite: {current_oil_touches} | Tiempo: {time_seconds}s", True, WHITE)
        screen.blit(info, (20, 10))

    elif state_game == "RESULTS":
        
        enemy_active = False
        lives = 3

        if current_music not in [music_win, music_lose]:
            play_music(music_win if score >= TOTAL_DELIVERIES else music_lose, loop=False)

        screen.fill(BLACK)

        if score >= TOTAL_DELIVERIES:
            res_txt = "¡ENTREGA EXITOSA!"
            color = GREEN
        elif death_reason == "asalto":
            res_txt = "¡TE ASALTARON!"
            color = RED
        elif death_reason == "gas":
            res_txt = "AGENTE SIN GASOLINA"
            color = RED

        screen.blit(font.render(res_txt, True, color), (450, 200))
        screen.blit(font.render(res_txt, True, GREEN if score >= 10 else RED), (450, 200))
        screen.blit(font.render(f"Tiempo: {time_seconds}s | Entregas: {score}", True, WHITE), (450, 280))
        screen.blit(font.render("Presiona M para volver al menú", True, YELLOW), (450, 380))
        
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                state_game = "MENU"
                pygame.mixer.music.fadeout(1000)
                current_music = None


    pygame.display.flip()