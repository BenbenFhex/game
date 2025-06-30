# 🔫 Retro Zombie FPS (Python + Tkinter)

This is a full-featured, retro-style 3D FPS written in pure Python using Tkinter. Survive an onslaught of zombies in a raycast-rendered world using your trusty 6-shot revolver. Inspired by classics like *DOOM* and *Wolfenstein 3D* — with a pixelated twist.

---

## 🎮 Features

- 🧟 Zombie AI that navigates around walls using BFS pathfinding
- 🎯 Raycasting engine simulating 3D walls and perspective
- 🔫 6-shot revolver with cooldown, reload animation, and effective range
- 💥 Bullet holes:
  - On zombies when hit
  - On walls when missed
- 🔍 Scope and zoom toggle (`Q` or `O`) for precision aiming
- 🕹️ Slowed movement while scoped for realism
- ❤️ Player health bar and game over condition
- 👁️ Crosshair and magnified reticle overlay
- ⌨️ Pure Python — no external libraries required

---

## 🧰 Requirements

- Python 3.x (recommended 3.8+)
- Tkinter (bundled with most Python distributions)

---

## ▶️ How to Run

1. Save the full game code in a file, for example: `zombie_fps.py`
2. Run it:

```bash
python zombie_fps.py
