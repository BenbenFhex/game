import os
import time
import math
import threading
import keyboard  # install this on Replit

# MAP DEFINITION
MAP = [
    "##########",
    "#        #",
    "#  ##    #",
    "#     #  #",
    "#   ##### ",
    "#        #",
    "##########"
]

MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 24
FOV = math.pi / 3
DEPTH = 16

# PLAYER STATE
player_x = 3.0
player_y = 3.0
player_angle = 0.0
is_shooting = False
running = True

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def cast_ray(x):
    ray_angle = (player_angle - FOV/2) + (x / SCREEN_WIDTH) * FOV
    ray_x = math.cos(ray_angle)
    ray_y = math.sin(ray_angle)
    dist = 0
    while dist < DEPTH:
        test_x = int(player_x + ray_x * dist)
        test_y = int(player_y + ray_y * dist)
        if 0 <= test_x < MAP_WIDTH and 0 <= test_y < MAP_HEIGHT:
            if MAP[test_y][test_x] == "#":
                return dist
        else:
            return DEPTH
        dist += 0.05
    return DEPTH

def render_weapon(firing=False):
    return r"""
      ___
     | * |     PEW!
     |___|
    / ___ \
   |_/___\_|
    |||||""" if firing else r"""
      ___
     | H |
     |___|
    /   \ 
   |     |
    |||||
"""

def render_frame():
    frame = ""
    for x in range(SCREEN_WIDTH):
        dist = cast_ray(x)
        shade = " "
        if dist < DEPTH / 4: shade = "█"
        elif dist < DEPTH / 3: shade = "▓"
        elif dist < DEPTH / 2: shade = "▒"
        elif dist < DEPTH: shade = "░"
        else: shade = " "

        height = int(SCREEN_HEIGHT / dist)
        top = SCREEN_HEIGHT // 2 - height
        bottom = SCREEN_HEIGHT // 2 + height

        for y in range(SCREEN_HEIGHT):
            if y < top: frame += " "
            elif y > bottom: frame += "."
            else: frame += shade
        frame += "\n"
    return frame

def update():
    global player_x, player_y, player_angle, is_shooting
    speed = 0.2
    while running:
        if keyboard.is_pressed("a"):
            player_angle -= 0.1
        if keyboard.is_pressed("d"):
            player_angle += 0.1
        if keyboard.is_pressed("w"):
            dx = math.cos(player_angle) * speed
            dy = math.sin(player_angle) * speed
            if MAP[int(player_y + dy)][int(player_x + dx)] != "#":
                player_x += dx
                player_y += dy
        if keyboard.is_pressed("s"):
            dx = -math.cos(player_angle) * speed
            dy = -math.sin(player_angle) * speed
            if MAP[int(player_y + dy)][int(player_x + dx)] != "#":
                player_x += dx
                player_y += dy
        if keyboard.is_pressed("space"):
            is_shooting = True
        time.sleep(0.01)

# Run input listener in background
threading.Thread(target=update, daemon=True).start()

# Main render loop
try:
    while True:
        clear()
        print(render_frame())
        print(render_weapon(is_shooting))
        print("Controls: W/A/S/D to move | Space to shoot | Ctrl+C to quit")
        is_shooting = False
        time.sleep(0.05)
except KeyboardInterrupt:
    running = False
    print("\nGame exited.")
