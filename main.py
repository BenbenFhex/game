import tkinter as tk
import math
import random
from collections import deque

# === Game Constants ===
MAP = [
    "##########",
    "#        #",
    "#  ##  # #",
    "#     #  #",
    "#   #### #",
    "#        #",
    "##########"
]
MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)
WIDTH, HEIGHT = 800, 400
FOV_NORMAL = math.pi / 3
FOV_ZOOM = math.pi / 6
DEPTH = 16
NUM_RAYS = 120
SCALE = WIDTH // NUM_RAYS

PLAYER_SPEED = 0.08
PLAYER_SPEED_ZOOM = 0.03
TURN_SPEED = 0.08
TURN_SPEED_ZOOM = 0.03

player_x, player_y = 3.0, 3.0
player_angle = 0.0
player_hp = 100
game_over = False

ammo = 6
max_ammo = 6
gun_range = 100
reloading = False
reload_timer = 0
cooldown_timer = 0
gun_flash_timer = 0
zoomed_in = False

zombies = []
wall_holes = []
zombie_bullets = []

root = tk.Tk()
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
canvas.pack()
root.title("Retro Zombie FPS")
keys = {}

# === Game Functions ===
def cast_rays():
    rays = []
    fov = FOV_ZOOM if zoomed_in else FOV_NORMAL
    delta_angle = fov / NUM_RAYS
    for ray in range(NUM_RAYS):
        angle = player_angle - fov / 2 + ray * delta_angle
        dx, dy = math.cos(angle), math.sin(angle)
        depth = 0
        while depth < DEPTH:
            tx, ty = int(player_x + dx * depth), int(player_y + dy * depth)
            if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
                if MAP[ty][tx] == "#":
                    break
            else:
                break
            depth += 0.05
        rays.append((ray, depth))
    return rays

def get_shade(dist):
    if dist < DEPTH / 3: return "#777"
    elif dist < DEPTH / 2: return "#444"
    elif dist < DEPTH: return "#222"
    else: return "#ccc"

def draw_health():
    bar_width = 200
    fill = int((player_hp / 100) * bar_width)
    canvas.create_rectangle(10, 10, 10 + bar_width, 26, fill="#333")
    canvas.create_rectangle(10, 10, 10 + fill, 26, fill="#d11")
    canvas.create_text(270, 18, text=f"HP: {player_hp}", fill="white", font=("Courier", 14))

def draw_scope():
    cx, cy = WIDTH // 2, HEIGHT // 2
    canvas.create_line(cx - 10, cy, cx + 10, cy, fill="white")
    canvas.create_line(cx, cy - 10, cx, cy + 10, fill="white")
    canvas.create_oval(cx - 25, cy - 25, cx + 25, cy + 25, outline="#555")
    if zoomed_in:
        canvas.create_oval(cx - 50, cy - 50, cx + 50, cy + 50, outline="#aaa")
        canvas.create_text(cx, cy + 60, text="ZOOM", fill="gray", font=("Courier", 10))

def draw_gun():
    cx = WIDTH // 2
    by = HEIGHT - 70
    if gun_flash_timer > 0:
        canvas.create_text(cx, by - 50, text="⚡", font=("Courier", 26), fill="yellow")
    canvas.create_rectangle(cx - 8, by, cx + 8, by + 30, fill="#222")
    canvas.create_rectangle(cx - 4, by - 20, cx + 4, by, fill="#aaa")
    canvas.create_text(cx + 100, by - 40, text=f"Ammo: {ammo}/6", fill="white", font=("Courier", 14))
    if reloading:
        canvas.create_text(cx, by - 60, text="RELOADING...", fill="orange", font=("Courier", 14))
        chamber = (reload_timer // 10) % 6
        for i in range(6):
            angle = math.radians(i * 60)
            rx = cx + int(20 * math.cos(angle))
            ry = by - 20 + int(20 * math.sin(angle))
            fill = "#f80" if i == chamber else "#444"
            canvas.create_oval(rx-4, ry-4, rx+4, ry+4, fill=fill, outline="black")

def draw_wall_holes():
    for h in wall_holes:
        if h["life"] > 0:
            canvas.create_oval(h["x"]-2, HEIGHT//2-2, h["x"]+2, HEIGHT//2+2, fill="#a00", outline="black")
            h["life"] -= 1

def update_zombie_bullets():
    global player_hp, game_over
    for bullet in zombie_bullets[:]:
        # Move bullet
        bullet["x"] += bullet["dx"] * 0.3
        bullet["y"] += bullet["dy"] * 0.3
        bullet["life"] -= 1

        # Check wall collision
        if (bullet["x"] < 0 or bullet["x"] >= MAP_WIDTH or 
            bullet["y"] < 0 or bullet["y"] >= MAP_HEIGHT or
            MAP[int(bullet["y"])][int(bullet["x"])] == "#" or
            bullet["life"] <= 0):
            zombie_bullets.remove(bullet)
            continue

        # Check player collision
        if math.hypot(bullet["x"] - player_x, bullet["y"] - player_y) < 0.3:
            player_hp -= 15
            zombie_bullets.remove(bullet)
            if player_hp <= 0:
                game_over = True

def draw_zombie_bullets(rays):
    for bullet in zombie_bullets:
        dx, dy = bullet["x"] - player_x, bullet["y"] - player_y
        dist = math.hypot(dx, dy)
        angle = math.atan2(dy, dx) - player_angle
        angle = (angle + math.pi) % (2 * math.pi) - math.pi
        fov = FOV_ZOOM if zoomed_in else FOV_NORMAL
        if -fov / 2 <= angle <= fov / 2:
            cx = int((angle + fov / 2) / fov * WIDTH)
            idx = min(max(int(cx / SCALE), 0), len(rays) - 1)
            if dist <= rays[idx][1] + 0.1:
                canvas.create_oval(cx-3, HEIGHT//2-3, cx+3, HEIGHT//2+3, fill="orange", outline="red")

def zombie_shoot(zombie):
    # Check if zombie has clear line of sight to player
    dx = player_x - zombie["x"]
    dy = player_y - zombie["y"]
    dist = math.hypot(dx, dy)

    if dist > 8:  # Max shooting range
        return False

    # Normalize direction
    dx /= dist
    dy /= dist

    # Check for walls in the way
    steps = int(dist * 20)
    for step in range(1, steps):
        check_x = zombie["x"] + dx * step * 0.05
        check_y = zombie["y"] + dy * step * 0.05
        if (0 <= int(check_x) < MAP_WIDTH and 0 <= int(check_y) < MAP_HEIGHT and
            MAP[int(check_y)][int(check_x)] == "#"):
            return False

    # Create bullet
    zombie_bullets.append({
        "x": zombie["x"], "y": zombie["y"],
        "dx": dx, "dy": dy, "life": 200
    })
    return True

def draw_zombies(rays):
    for z in zombies:
        if not z["alive"]: continue
        dx, dy = z["x"] - player_x, z["y"] - player_y
        dist = math.hypot(dx, dy)
        angle = math.atan2(dy, dx) - player_angle
        angle = (angle + math.pi) % (2 * math.pi) - math.pi
        fov = FOV_ZOOM if zoomed_in else FOV_NORMAL
        if -fov / 2 <= angle <= fov / 2:
            cx = int((angle + fov / 2) / fov * WIDTH)
            idx = min(max(int(cx / SCALE), 0), len(rays) - 1)
            if dist <= rays[idx][1] + 0.2:
                h = max(int(HEIGHT / (dist + 0.01)), 20)
                w = int(h * 0.5)
                top = HEIGHT // 2 - h // 2

                # Use zombie's color based on type
                color = z["color"]
                outline_colors = {
                    "#4a6b3a": "#2a4b1a",  # Normal zombie
                    "#6a4b3a": "#4a2b1a",  # Armed zombie  
                    "#3a3a3a": "#1a1a1a"   # Armored zombie
                }
                outline = outline_colors.get(color, "#2a2a2a")

                canvas.create_rectangle(cx - w//2, top, cx + w//2, top + h, fill=color, outline=outline)

                # Draw armor plating for armored zombies
                if z["type"] == "armored":
                    # Draw armor plates
                    plate_w = w // 3
                    canvas.create_rectangle(cx - plate_w//2, top + h//4, cx + plate_w//2, top + h//2, fill="#555", outline="#333")
                    canvas.create_rectangle(cx - plate_w//2, top + h//2, cx + plate_w//2, top + 3*h//4, fill="#555", outline="#333")

                # Draw gun if zombie has one
                if z["has_gun"]:
                    gun_x = cx + w//4
                    gun_y = top + h//3
                    canvas.create_rectangle(gun_x-2, gun_y-1, gun_x+6, gun_y+1, fill="#333")

                # Draw health indicator for damaged zombies
                if z["health"] < z["max_health"]:
                    # Red damage indicator
                    canvas.create_oval(cx - w//4, top - 5, cx + w//4, top + 5, fill="red", outline="darkred")
                    canvas.create_text(cx, top, text=str(z["health"]), fill="white", font=("Courier", 8))

                for hole in z["holes"]:
                    if hole["life"] > 0:
                        hx = cx + int(hole["x"] * w // 2)
                        hy = top + int(hole["y"] * h)
                        canvas.create_oval(hx-3, hy-3, hx+3, hy+3, fill="red", outline="black")
                        hole["life"] -= 1

def fire_gun():
    global ammo, cooldown_timer, gun_flash_timer, reloading, reload_timer
    if reloading or cooldown_timer > 0 or ammo <= 0: return
    ammo -= 1
    cooldown_timer = 12
    gun_flash_timer = 6

    # When zoomed in, check for zombie in crosshair first
    if zoomed_in:
        # Check each zombie to see if it's in the crosshair
        for z in zombies:
            if not z["alive"]: continue
            dx, dy = z["x"] - player_x, z["y"] - player_y
            dist = math.hypot(dx, dy)
            angle_to_zombie = math.atan2(dy, dx) - player_angle
            angle_to_zombie = (angle_to_zombie + math.pi) % (2 * math.pi) - math.pi

            # Check if zombie is in center of crosshair (very precise when zoomed)
            if abs(angle_to_zombie) < 0.02 and dist <= gun_range:  # Very tight angle for zoom precision
                z["holes"].append({"x": 0, "y": 0.4, "life": 15})
                z["health"] -= 1
                if z["health"] <= 0:
                    z["alive"] = False
                return

    # Regular raycast shooting
    angle = player_angle
    dx, dy = math.cos(angle), math.sin(angle)
    hit_accuracy = 0.3 if not zoomed_in else 0.15  # More accurate when zoomed

    for step in range(int(gun_range * 20)):
        px, py = player_x + dx * step * 0.05, player_y + dy * step * 0.05
        if 0 <= int(px) < MAP_WIDTH and 0 <= int(py) < MAP_HEIGHT:
            if MAP[int(py)][int(px)] == "#":
                wall_holes.append({"x": WIDTH // 2, "life": 20})
                break
        for z in zombies:
            if z["alive"] and math.hypot(z["x"] - px, z["y"] - py) < hit_accuracy:
                z["holes"].append({"x": 0, "y": 0.4, "life": 15})
                z["health"] -= 1
                if z["health"] <= 0:
                    z["alive"] = False
                return
    wall_holes.append({"x": WIDTH // 2, "life": 20})
    if ammo <= 0:
        reloading = True
        reload_timer = 60

def reload_gun():
    global reloading, reload_timer, ammo
    if not reloading and ammo < max_ammo:
        reloading = True
        reload_timer = 60

def bfs(start, goal):
    q = deque([(start, [])])
    visited = {start}
    while q:
        (x, y), path = q.popleft()
        if (x, y) == goal: return path
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT and MAP[ny][nx] == " " and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append(((nx, ny), path + [(nx, ny)]))
    return []

def spawn_zombie():
    spaces = [(x,y) for y in range(MAP_HEIGHT) for x in range(MAP_WIDTH)
              if MAP[y][x] == " " and math.hypot(player_x - x, player_y - y) > 4]
    if spaces:
        x, y = random.choice(spaces)

        # Randomize zombie type
        zombie_type = random.choice([
            "normal",     # 33% chance - basic zombie
            "armed",      # 33% chance - zombie with gun
            "armored"     # 33% chance - armored zombie (2 hits to kill)
        ])

        # Set zombie properties based on type
        if zombie_type == "normal":
            has_gun = False
            health = 1
            speed = 0.02
            color = "#4a6b3a"
        elif zombie_type == "armed":
            has_gun = True
            health = 1
            speed = 0.015
            color = "#6a4b3a"
        else:  # armored
            has_gun = False  # Armored zombies cannot have guns
            health = 2
            speed = 0.01  # Slower due to armor
            color = "#3a3a3a"  # Dark gray for armor

        zombies.append({
            "x": x+0.5, "y": y+0.5, "alive": True, "path": [], 
            "hit_timer": 0, "holes": [], "has_gun": has_gun,
            "shoot_timer": 0, "last_shot": 0, "health": health,
            "max_health": health, "type": zombie_type, "speed": speed,
            "color": color
        })

def update_zombies():
    global player_hp, game_over

    # Spawn new zombies if needed
    alive_count = sum(1 for z in zombies if z["alive"])
    while alive_count < 3:
        spawn_zombie()
        alive_count += 1

    player_cell = (int(player_x), int(player_y))

    for z in zombies:
        if not z["alive"]: 
            continue

        # Update timers
        if z["hit_timer"] > 0:
            z["hit_timer"] -= 1
            continue

        if z["shoot_timer"] > 0:
            z["shoot_timer"] -= 1

        zombie_cell = (int(z["x"]), int(z["y"]))
        dist_to_player = math.hypot(z["x"] - player_x, z["y"] - player_y)

        # Armed zombies try to shoot if in range
        if z["has_gun"] and dist_to_player > 0.5 and dist_to_player < 6 and z["shoot_timer"] <= 0:
            if zombie_shoot(z):
                z["shoot_timer"] = 180  # Cooldown between shots (3 seconds at 60fps)

        # Check if zombie reached player for melee attack
        if dist_to_player < 0.5:
            player_hp -= 20
            z["hit_timer"] = 60
            if player_hp <= 0:
                game_over = True
            continue

        # Pathfinding - armed zombies move slower and prefer to keep distance
        if not z["path"] or len(z["path"]) == 0:
            z["path"] = bfs(zombie_cell, player_cell)

        if z["path"]:
            # Armed zombies stop moving if close enough to shoot
            if z["has_gun"] and dist_to_player < 4 and dist_to_player > 2:
                continue  # Don't move closer, just shoot

            next_cell = z["path"][0]
            target_x, target_y = next_cell[0] + 0.5, next_cell[1] + 0.5

            dx = target_x - z["x"]
            dy = target_y - z["y"]
            dist = math.hypot(dx, dy)

            if dist < 0.1:
                z["path"].pop(0)
            else:
                # Use individual zombie speed based on type
                z["x"] += (dx / dist) * z["speed"]
                z["y"] += (dy / dist) * z["speed"]

def draw_game_over():
    canvas.create_text(WIDTH // 2, HEIGHT // 2 - 20, text="GAME OVER", fill="red", font=("Courier", 32, "bold"))
    canvas.create_text(WIDTH // 2, HEIGHT // 2 + 20, text="Press R to Restart", fill="white", font=("Courier", 16))

def restart_game():
    global player_x, player_y, player_angle, player_hp, game_over
    global ammo, reloading, reload_timer, cooldown_timer, gun_flash_timer

    player_x, player_y = 3.0, 3.0
    player_angle = 0.0
    player_hp = 100
    game_over = False
    ammo = 6
    reloading = False
    reload_timer = 0
    cooldown_timer = 0
    gun_flash_timer = 0
    zombies.clear()
    wall_holes.clear()
    zombie_bullets.clear()

    # Spawn initial zombies
    for _ in range(3):
        spawn_zombie()

# === Event Handlers ===
def key_press(event):
    keys[event.keysym] = True

def key_release(event):
    keys[event.keysym] = False

def render():
    canvas.delete("all")

    if game_over:
        draw_game_over()
        return

    # Cast rays for wall rendering
    rays = cast_rays()

    # Draw walls
    for ray, dist in rays:
        shade = get_shade(dist)
        wall_height = HEIGHT / (dist + 0.01)
        wall_top = (HEIGHT - wall_height) / 2
        wall_bottom = wall_top + wall_height

        x = ray * SCALE
        canvas.create_rectangle(x, wall_top, x + SCALE, wall_bottom, fill=shade, outline="")

    # Draw zombies
    draw_zombies(rays)

    # Draw zombie bullets
    draw_zombie_bullets(rays)

    # Draw wall holes
    draw_wall_holes()

    # Draw UI elements
    draw_health()
    draw_scope()
    draw_gun()

def update():
    global player_x, player_y, player_angle
    global reload_timer, cooldown_timer, gun_flash_timer, zoomed_in

    # Update timers
    if reload_timer > 0:
        reload_timer -= 1
        if reload_timer <= 0:
            global ammo, reloading
            ammo = max_ammo
            reloading = False
            reload_timer = 0

    if cooldown_timer > 0:
        cooldown_timer -= 1

    if gun_flash_timer > 0:
        gun_flash_timer -= 1

    # Handle game over
    if game_over:
        if keys.get('r') or keys.get('R'):
            restart_game()
        render()
        root.after(16, update)
        return

    # Movement (slower when zoomed in)
    current_speed = PLAYER_SPEED_ZOOM if zoomed_in else PLAYER_SPEED
    current_turn_speed = TURN_SPEED_ZOOM if zoomed_in else TURN_SPEED

    if keys.get('w') or keys.get('W') or keys.get('Up'):
        new_x = player_x + math.cos(player_angle) * current_speed
        new_y = player_y + math.sin(player_angle) * current_speed
        if (0 <= int(new_x) < MAP_WIDTH and 0 <= int(new_y) < MAP_HEIGHT and
            MAP[int(new_y)][int(new_x)] == " "):
            player_x = new_x
            player_y = new_y

    if keys.get('s') or keys.get('S') or keys.get('Down'):
        new_x = player_x - math.cos(player_angle) * current_speed
        new_y = player_y - math.sin(player_angle) * current_speed
        if (0 <= int(new_x) < MAP_WIDTH and 0 <= int(new_y) < MAP_HEIGHT and
            MAP[int(new_y)][int(new_x)] == " "):
            player_x = new_x
            player_y = new_y

    if keys.get('a') or keys.get('A') or keys.get('Left'):
        player_angle -= current_turn_speed

    if keys.get('d') or keys.get('D') or keys.get('Right'):
        player_angle += current_turn_speed

    # Shooting
    if keys.get('space'):
        fire_gun()

    # Manual reload
    if keys.get('r') and not game_over:
        reload_gun()

    # Zoom toggle
    if keys.get('e') or keys.get('E'):
        zoomed_in = not zoomed_in
        keys['e'] = False  # Prevent continuous toggling
        keys['E'] = False

    # Update game state
    update_zombies()
    update_zombie_bullets()

    # Render everything
    render()

    # Schedule next frame
    root.after(16, update)

# Initialize game
root.bind('<KeyPress>', key_press)
root.bind('<KeyRelease>', key_release)
root.focus_set()

# Start with initial zombies
for _ in range(3):
    spawn_zombie()

# Start the game loop
update()
root.mainloop()
