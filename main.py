import pygame
import sys
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

WHITE=(255,255,255)
GRAY=(60,60,60)
ROAD=(90,90,90)
BUILDING=(30,30,30)
YELLOW=(255,220,0)
RED=(200,50,50)
GREEN=(40,200,40)
BLACK=(0,0,0)

# =========================
# MAPA
# =========================
grid=[[0]*COLS for _ in range(ROWS)]

for r in [3,7,11,15]:
    for c in range(COLS):
        grid[r][c]=1

for c in [4,9,14,19,24]:
    for r in range(ROWS):
        grid[r][c]=1

# =========================
# OBJETOS
# =========================
deliveries=[
(4,3),(9,7),(19,11),(4,15),
(14,3),(24,7),(9,11),(19,15),
(24,3),(14,15)
]

TOTAL_DELIVERIES=10
game_over=False

gas_station=(24,15)

time_blocks=[(14,7),(9,11),(19,3),(4,7)]  # cuadrados negros

# =========================
# AGENTE
# =========================
agent=[4,15]
fuel=100
score=0
time_seconds=0

# timers
second_timer=0
fuel_timer=0


# =========================
# BFS
# =========================
def neighbors(x,y):
    moves=[]

    def add(nx,ny):
        if 0<=nx<COLS and 0<=ny<ROWS and grid[ny][nx]==1:
            moves.append((nx,ny))

    # -------- horizontales --------
    if y==3 or y==11:  # izquierda -> derecha
        add(x+1,y)

    if y==7 or y==15:  # derecha -> izquierda
        add(x-1,y)

    # -------- verticales --------
    if x==4 or x==14 or x==24:  # arriba -> abajo
        add(x,y+1)

    if x==9 or x==19:  # abajo -> arriba
        add(x,y-1)

    # ===== INTERSECCIONES (permitir giros) =====
    if 0<=x<COLS and 0<=y<ROWS and grid[y][x]==1:
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            add(x+dx,y+dy)

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
    global path,emergency

    if fuel<20:
        emergency=True
        path=bfs(tuple(agent),gas_station)
        return

    emergency=False

    best=None
    best_len=9999

    for d in deliveries:
        p=bfs(tuple(agent),d)
        if len(p)>0 and len(p)<best_len:
            best_len=len(p)
            best=d

    if best:
        path=bfs(tuple(agent),best)

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

    # ⏱️ tiempo natural
    if second_timer>=1000:
        time_seconds+=1
        second_timer=0

    # ⛽ gasolina natural
    if fuel_timer>=2000:
        fuel=max(0,fuel-5)
        fuel_timer=0

        if fuel<20:
            emergency=True
            path.clear()



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
                time_blocks.remove(tuple(agent))
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
            if grid[y][x]==1:
                pygame.draw.rect(screen,ROAD,(x*CELL,y*CELL,CELL,CELL))

    for d in deliveries:
        pygame.draw.circle(screen,RED,(d[0]*CELL+20,d[1]*CELL+20),10)

    for b in time_blocks:
        pygame.draw.rect(screen,BLACK,(b[0]*CELL+10,b[1]*CELL+10,20,20))

    pygame.draw.rect(screen,GREEN,(gas_station[0]*CELL,gas_station[1]*CELL,CELL,CELL))
    pygame.draw.rect(screen,YELLOW,(agent[0]*CELL+5,agent[1]*CELL+5,30,30))

    # UI
    txt1=font.render(f"Tiempo: {time_seconds}s",True,WHITE)
    txt2=font.render(f"Gasolina: {fuel}%",True,WHITE)
    txt3=font.render(f"Entregas: {score}/{TOTAL_DELIVERIES}",True,WHITE)

    screen.blit(txt1,(20,20))
    screen.blit(txt2,(20,50))
    screen.blit(txt3,(20,80))

    pygame.display.flip()
