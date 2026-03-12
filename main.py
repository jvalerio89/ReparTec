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

# colores
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
TOTAL_DELIVERIES=3
gas_station=(28,15)
gas_point=(28,16)
second_timer = 0
fuel_timer=0
move_timer = 0
# stats del enemigo
enemy_pos = [29, 1]  # Aparece en una esquina opuesta
enemy_active = False
lives = 3
deliveries_to_spawn_enemy = 3
death_reason = ""

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


# Cargar memoria al iniciar
load_memory()

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
        screen.fill(BLACK)
        screen.blit(font.render("Agente Inteligente - Repartidor", True, YELLOW), (450, 200))
        screen.blit(font.render(f"Completados: {total_completed} | Fallidos: {total_failed}", True, WHITE), (450, 300))
        screen.blit(font.render("Presiona ESPACIO para iniciar", True, GREEN), (450, 400))
        
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                agent, fuel, score, time_seconds, current_oil_touches = [1, 16], 100, 0, 0, 0
                deliveries = lugares_random(TOTAL_DELIVERIES, [], agent)
                time_blocks = lugares_random(7, deliveries, agent)
                state_game = "PLAYING"

    elif state_game == "PLAYING":

        move_timer += dt
        second_timer += dt
        fuel_timer += dt

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
            if action == 0: ny -= 1
            elif action == 1: ny += 1
            elif action == 2: nx -= 1
            elif action == 3: nx += 1

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
                elif pos_actual in time_blocks:
                    reward -= 30
                    current_oil_touches += 1
                elif pos_actual == gas_point:
                    reward = 200
                    fuel = 100
                    
            update_q(state, action, reward, next_state)

            # --- LÓGICA DEL ENEMIGO ---
            if score >= deliveries_to_spawn_enemy:
                enemy_active = True

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

        # --- DIBUJO JUEGO ---
        screen.fill(BUILDING)
        for y in range(ROWS):
            for x in range(COLS):
                if grid[y][x] == 1: pygame.draw.rect(screen, ROAD, (x*CELL, y*CELL, CELL, CELL))
                elif grid[y][x] == 3: pygame.draw.rect(screen, WATER_BLUE, (x*CELL, y*CELL, CELL, CELL))
        
        if enemy_active:
            pygame.draw.rect(screen, WHITE, (enemy_pos[0]*CELL, enemy_pos[1]*CELL, CELL, CELL))

        for d in deliveries: screen.blit(caja_img, (d[0]*CELL, d[1]*CELL))
        for b in time_blocks: screen.blit(aceite_img, (b[0]*CELL, b[1]*CELL))
        screen.blit(bidon_img, (gas_point[0]*CELL, gas_point[1]*CELL))
        screen.blit(camioneta_img, (agent[0]*CELL, agent[1]*CELL))

        # Barra superior UI
        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 40))
        info = font.render(f"Vidas: {lives} | Entregas: {score} | Gas: {fuel}% | Aceite: {current_oil_touches} | Tiempo: {time_seconds}s", True, WHITE)
        screen.blit(info, (20, 10))

    elif state_game == "RESULTS":
        
        enemy_active = False
        lives = 3

        screen.fill(BLACK)

        if score >= 10:
            res_txt = "¡ENTREGA EXITOSA!"
            color = GREEN
        elif death_reason == "asalto":
            res_txt = "¡TE ASALTARON!"
            color = RED
        else:
            res_txt = "AGENTE SIN GASOLINA"
            color = RED

        screen.blit(font.render(res_txt, True, color), (450, 200))
        screen.blit(font.render(res_txt, True, GREEN if score >= 10 else RED), (450, 200))
        screen.blit(font.render(f"Tiempo: {time_seconds}s | Entregas: {score}", True, WHITE), (450, 280))
        screen.blit(font.render("Presiona M para volver al menú", True, YELLOW), (450, 380))
        
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                state_game = "MENU"

    pygame.display.flip()