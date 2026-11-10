import tkinter as tk
import random
import os

# Base Game Object
class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)

# Ball Object
class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [random.choice([1, -1]), -1]
        self.speed = 10
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def grow(self):
        if self.radius < 25:
            self.radius += 5
            coords = self.get_position()
            x = (coords[0] + coords[2]) / 2
            y = (coords[1] + coords[3]) / 2
            self.canvas.coords(self.item, x - self.radius, y - self.radius, 
                               x + self.radius, y + self.radius)

    def update(self):
        coords = self.get_position()
        width = int(self.canvas['width'])
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords_obj = game_object.get_position()
            if x > coords_obj[2]:
                self.direction[0] = 1
            elif x < coords_obj[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        destroyed = []
        hits = 0
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                hits += 1
                # Jika bata hancur (hit() return True), masukkan ke list destroyed
                if game_object.hit():
                    destroyed.append(game_object)
        
        # Mengembalikan list bata yang hancur dan jumlah hitongan tabrakan
        return destroyed, hits

# PowerUp / Skill Object
class PowerUp(GameObject):
    def __init__(self, canvas, x, y, skill_type):
        self.skill = skill_type
        self.speed = 5
        # Menambahkan 'life' dengan warna merah
        colors = {
            'multi': '#9b59b6', # Ungu
            'long': '#3498db',  # Biru
            'large': '#2ecc71', # Hijau
            'life': '#e74c3c'   # Merah (Nyawa Tambahan)
        }
        color = colors.get(skill_type, 'white')
        size = 12
        item = canvas.create_oval(x - size, y - size,
                                  x + size, y + size,
                                  fill=color, tags='powerup')
        super(PowerUp, self).__init__(canvas, item)

    def update(self):
        self.move(0, self.speed)

# Paddle Object
class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.default_width = 80
        self.width = self.default_width
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='yellow')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def reset(self):
        self.width = self.default_width
        self.update_coords()

    def grow(self):
        if self.width < 200:
            self.width += 40
            self.update_coords()

    def update_coords(self):
        coords = self.get_position()
        x = (coords[0] + coords[2]) / 2
        y = (coords[1] + coords[3]) / 2
        self.canvas.coords(self.item, x - self.width / 2, y - self.height / 2, 
                           x + self.width / 2, y + self.height / 2)

    def move(self, offset):
        coords = self.get_position()
        width = int(self.canvas['width'])
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

