import tkinter as tk
import random
import os

try:
    import pygame
except ImportError:
    print("Modul pygame belum terinstall. Jalankan: pip install pygame")

# Base Game Object
class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)
        
    def get_bbox(self):
        return self.canvas.bbox(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)

# Tombak Ultimate (Spear)
class Spear(GameObject):
    def __init__(self, canvas, x, y):
        self.speed = 12 # Disesuaikan untuk 60 FPS
        points = [
            x - 12, y,         
            x + 12, y,         
            x + 12, y - 80,   
            x, y - 120,        
            x - 12, y - 80    
        ]
        item = canvas.create_polygon(points, fill='#8B4513', outline='#E5E4E2', width=2, tags='spear')
        super(Spear, self).__init__(canvas, item)

    def update(self):
        self.move(0, -self.speed)

# Ball Object (Telur Dino)
class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [random.choice([1, -1]), -1]
        self.speed = 5.5 # Disesuaikan untuk 60 FPS
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='#FFF8DC', tags='ball')
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
        
        # Mencegah bug bola nyangkut di dinding
        if coords[0] <= 0:
            self.direction[0] = 1 
        elif coords[2] >= width:
            self.direction[0] = -1 
            
        if coords[1] <= 0:
            self.direction[1] = 1 
            
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        
        hit_paddle = any(isinstance(obj, Paddle) for obj in game_objects)
        
        if hit_paddle:
            self.direction[1] = -1 # Paksa mantul ke atas agar tidak tembus paddle
        elif len(game_objects) > 1:
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
                if game_object.hit():
                    destroyed.append(game_object)
        
        return destroyed, hits

# PowerUp / Skill Object
class PowerUp(GameObject):
    def __init__(self, canvas, x, y, skill_type):
        self.skill = skill_type
        self.speed = 3 # Disesuaikan untuk 60 FPS
        colors = {
            'multi': '#9b59b6', 
            'long': '#3498db',  
            'large': '#2ecc71', 
            'life': '#e74c3c'   
        }
        color = colors.get(skill_type, 'white')
        size = 12
        item = canvas.create_oval(x - size, y - size,
                                  x + size, y + size,
                                  fill=color, tags='powerup')
        super(PowerUp, self).__init__(canvas, item)

    def update(self):
        self.move(0, self.speed)

# Paddle Object (Batang Kayu Purba)
class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.default_width = 80
        self.width = self.default_width
        self.height = 12
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#5C3A21')
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

# Brick Object (Tanah, Batu, Fosil)
class Brick(GameObject):
    COLORS = {1: '#8B4513', 2: '#696969', 3: '#F5DEB3'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, outline='#2F4F4F', tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.last_coords = self.get_position()
        self.hits -= 1
        if self.hits == 0:
            self.delete()
            return True 
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])
            return False

# Main Game Controller
class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='black', width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()

        # Load Gambar Background
        try:
            self.bg_image = tk.PhotoImage(file="jungle.png")
        except Exception:
            self.bg_image = None # Akan menggunakan fallback warna jika gambar tidak ditemukan

        self.init_audio()

        self.highscore_file = "dino_highscore.txt"
        self.high_score = self.load_high_score()
        self.paddle_timer = None 
        
        self.paddle_direction = 0 
        self.paddle_speed = 10 # Disesuaikan untuk 60 FPS
        
        self.ulti_ready = True
        self.ulti_cooldown = 0
        self.particles = []
        
        self.state = 'MENU' 
        self.canvas.focus_set()
        
        self.canvas.bind('<KeyPress-Left>', self.on_key_press)
        self.canvas.bind('<KeyPress-Right>', self.on_key_press)
        self.canvas.bind('<KeyRelease-Left>', self.on_key_release)
        self.canvas.bind('<KeyRelease-Right>', self.on_key_release)
        
        self.canvas.bind('<KeyPress-u>', self.fire_ulti)
        self.canvas.bind('<KeyPress-U>', self.fire_ulti)
        
        self.show_menu()

    def init_audio(self):
        try:
            pygame.mixer.init()
            if os.path.exists('jungle.mp3'):
                pygame.mixer.music.load('jungle.mp3')
                pygame.mixer.music.set_volume(0.5) 
                pygame.mixer.music.play(-1) 
        except Exception:
            pass

    def draw_background(self):
        """Membuat ulang background setelah canvas di-clear untuk mencegah bug"""
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor='nw', tags='bg')
        else:
            self.canvas.create_rectangle(0, 0, self.width, self.height, fill='#2E4A22', tags='bg')
        self.canvas.tag_lower('bg')

    def spawn_trail(self, x, y, radius):
        """Efek partikel api untuk bola dan ulti"""
        item = self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, 
                                       fill='#FFFF00', outline='', tags='trail')
        # Taruh partikel di atas background, tapi di bawah bola/paddle
        self.canvas.tag_lower(item, 'ball')
        self.canvas.tag_raise(item, 'bg')
        
        self.particles.append({
            'item': item, 
            'life': 10, 
            'max_life': 10, 
            'x': x, 
            'y': y, 
            'r': radius
        })

    def on_key_press(self, event):
        if event.keysym == 'Left':
            self.paddle_direction = -self.paddle_speed
        elif event.keysym == 'Right':
            self.paddle_direction = self.paddle_speed

    def on_key_release(self, event):
        if event.keysym == 'Left' and self.paddle_direction < 0:
            self.paddle_direction = 0
        elif event.keysym == 'Right' and self.paddle_direction > 0:
            self.paddle_direction = 0

    def fire_ulti(self, event):
        if self.state == 'PLAYING' and self.ulti_ready:
            self.ulti_ready = False
            self.ulti_cooldown = 30
            
            coords = self.paddle.get_position()
            x = (coords[0] + coords[2]) / 2
            y = coords[1]
            
            spear = Spear(self.canvas, x, y)
            self.spears.append(spear)
            self.update_cooldown()

    def update_cooldown(self):
        if self.ulti_cooldown > 0:
            self.ulti_cooldown -= 1
            self.update_hud()
            self.after(1000, self.update_cooldown) 
        else:
            self.ulti_ready = True
            self.update_hud()

    def load_high_score(self):
        if os.path.exists(self.highscore_file):
            try:
                with open(self.highscore_file, "r") as f:
                    return int(f.read())
            except:
                return 0
        return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(self.highscore_file, "w") as f:
                    f.write(str(self.high_score))
            except:
                pass

    def draw_text(self, x, y, text, size='40', color='white'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text, font=font, fill=color)

    def show_menu(self):
        self.state = 'MENU'
        self.canvas.delete('all')
        self.draw_background()
        
        self.high_score = self.load_high_score()
        
        self.draw_text(self.width/2, 120, 'DINO BREAKOUT', size='45', color='#FFD700')
        self.draw_text(self.width/2, 170, 'Jurassic Era', size='25', color='#98FB98')
        self.draw_text(self.width/2, 230, f'Top Score: {self.high_score}', size='20', color='white')
        self.draw_text(self.width/2, 300, 'Press SPACE to Start', size='15', color='white')
        
        self.canvas.bind('<space>', lambda _: self.init_game())

    def init_game(self):
        self.canvas.unbind('<space>')
        self.lives = 3
        self.score = 0
        self.current_level = 1
        self.ulti_ready = True
        self.ulti_cooldown = 0
        self.load_level()

    def get_level_pattern(self, level):
        if level == 1:
            return [[1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1]]
        elif level == 2:
            return [[0, 0, 2, 0, 0, 2, 0], [0, 2, 2, 2, 0, 2, 2], [2, 2, 2, 2, 2, 2, 2], [1, 1, 1, 1, 1, 1, 1]]
        elif level == 3:
            return [[3, 3, 0, 0, 0, 3, 3], [3, 3, 3, 3, 3, 3, 3], [0, 0, 3, 3, 3, 0, 0], [1, 2, 1, 2, 1, 2, 1], [3, 3, 0, 0, 0, 3, 3]]
        elif level == 4:
            return [[0, 0, 3, 3, 3, 0, 0], [0, 3, 2, 0, 2, 3, 0], [3, 2, 0, 1, 0, 2, 3], [0, 3, 2, 0, 2, 3, 0], [0, 0, 3, 3, 3, 0, 0]]
        elif level == 5:
            return [[2, 0, 2, 0, 2, 0, 0], [2, 2, 2, 2, 2, 0, 0], [0, 3, 3, 3, 0, 0, 0], [0, 3, 3, 3, 0, 0, 0], [0, 0, 3, 0, 0, 0, 0]]
        else:
            pattern = []
            rows = random.randint(4, 6)
            for _ in range(rows):
                row = []
                for _ in range(7):
                    row.append(random.choice([0, 1, 1, 2, 2, 3])) 
                pattern.append(row)
            return pattern

    def load_level(self):
        self.canvas.delete('all')
        self.draw_background()
        
        self.items = {}
        self.balls = []
        self.powerups = []
        self.spears = []
        self.particles = []
        self.hud = None
        
        if self.paddle_timer:
            self.after_cancel(self.paddle_timer)
            self.paddle_timer = None

        skill_text = "Drops: Ungu(Multi) | Biru(Panjang) | Hijau(Besar) | Merah(Nyawa)"
        self.canvas.create_text(self.width/2, self.height - 15, text=skill_text, 
                                font=('Arial', 9, 'bold'), fill='#DDDDDD')

        self.paddle = Paddle(self.canvas, self.width / 2, 340)
        self.items[self.paddle.item] = self.paddle
        
        self.setup_bricks()
        self.update_hud()
        self.setup_turn(new_level=True)

    def setup_bricks(self):
        pattern = self.get_level_pattern(self.current_level)
        col_width = 75
        row_height = 25
        x_offset = (self.width - (7 * col_width)) / 2 + (col_width / 2)
        y_offset = 60

        for row_idx, row in enumerate(pattern):
            for col_idx, hit_points in enumerate(row):
                if hit_points > 0:
                    x = x_offset + col_idx * col_width
                    y = y_offset + row_idx * row_height
                    brick = Brick(self.canvas, x, y, hit_points)
                    self.items[brick.item] = brick

    def setup_turn(self, new_level=False):
        self.state = 'WAITING'
        self.paddle_direction = 0 
        
        if self.paddle_timer:
            self.after_cancel(self.paddle_timer)
            self.paddle_timer = None

        for p in self.powerups: p.delete()
        self.powerups = []
        for s in self.spears: s.delete()
        self.spears = []
        for pt in self.particles: self.canvas.delete(pt['item'])
        self.particles = []
        
        self.paddle.reset()
        
        for b in self.balls:
            b.delete()
        self.balls = []
        
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        ball = Ball(self.canvas, x, 324)
        self.balls.append(ball)
        self.paddle.set_ball(ball)

        msg = f'LEVEL {self.current_level} - Press Space' if new_level else 'Press Space to Launch'
        self.text_msg = self.draw_text(self.width/2, 220, msg, size='20', color='#FFD700')
        self.canvas.bind('<space>', lambda _: self.start_turn())

    def start_turn(self):
        self.state = 'PLAYING'
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text_msg)
        self.paddle.ball = None
        self.game_loop()

    def reset_paddle_length(self):
        self.paddle.reset()
        self.paddle_timer = None

    def spawn_extra_balls(self):
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        y = paddle_coords[1] - 15
        
        directions = [[-1, -1], [1, -1]]
        for d in directions:
            b = Ball(self.canvas, x, y)
            b.direction = d
            self.balls.append(b)

    def update_hud(self):
        ulti_status = "READY" if self.ulti_ready else f"CD {self.ulti_cooldown}s"
        text = f"Level: {self.current_level}   |   Score: {self.score}   |   Lives: {self.lives}   |   Ulti (U): {ulti_status}"
        
        if self.hud is None:
            self.hud = self.canvas.create_text(self.width/2, 20, text=text, font=('Arial', 11, 'bold'), fill='white')
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def level_complete(self):
        self.state = 'LEVEL_TRANSITION'
        for b in self.balls: b.speed = 0
        for s in self.spears: s.speed = 0
        
        bonus = self.current_level * 100
        self.score += bonus
        self.update_hud()
        
        self.draw_text(self.width/2, 180, 'LEVEL CLEAR!', size='35', color='#2ecc71')
        self.draw_text(self.width/2, 230, f'Bonus Score: +{bonus}', size='20', color='#FFD700')
        
        self.after(2500, self.next_level)

    def next_level(self):
        self.current_level += 1
        self.load_level()

    def game_over(self, win):
        self.state = 'GAME_OVER'
        self.save_high_score()
        for b in self.balls: b.speed = 0
        
        msg = 'YOU SURVIVED!' if win else 'EXTINCTION! (Game Over)'
        color = '#2ecc71' if win else '#e74c3c'
        self.draw_text(self.width/2, 200, msg, size='35', color=color)
        
        self.after(3500, self.show_menu)

    def game_loop(self):
        if self.state != 'PLAYING':
            return

        # GERAKAN PADDLE SUPER MULUS (Terintegrasi)
        if self.paddle_direction != 0:
            self.paddle.move(self.paddle_direction)

        self.check_collisions()

        # Update Tombak Ulti + Buntut Api
        for s in self.spears.copy():
            bbox = s.get_bbox()
            cx = (bbox[0] + bbox[2]) / 2
            self.spawn_trail(cx, bbox[3] - 10, 8) # Drop trail di bagian bawah tombak
            s.update()
            
            items_hit = self.canvas.find_overlapping(*s.get_bbox())
            for item_id in items_hit:
                if item_id in self.items:
                    obj = self.items[item_id]
                    if isinstance(obj, Brick):
                        bc = obj.get_position()
                        bx = (bc[0] + bc[2]) / 2
                        by = (bc[1] + bc[3]) / 2
                        obj.delete()
                        del self.items[item_id]
                        self.score += 50
                        self.update_hud()
                        
                        if random.random() < 0.35:
                            skill = random.choice(['multi', 'long', 'large', 'life'])
                            p = PowerUp(self.canvas, bx, by, skill)
                            self.powerups.append(p)
            
            if bbox[3] <= 0:
                s.delete()
                self.spears.remove(s)

        # Efek visual memudar untuk Jejak Api
        for p in self.particles.copy():
            p['life'] -= 1
            if p['life'] <= 0:
                self.canvas.delete(p['item'])
                self.particles.remove(p)
            else:
                ratio = p['life'] / p['max_life']
                nr = p['r'] * ratio
                self.canvas.coords(p['item'], p['x'] - nr, p['y'] - nr, p['x'] + nr, p['y'] + nr)
                # Gradasi warna: Kuning -> Oranye -> Merah
                if ratio > 0.6: color = '#FFFF00'
                elif ratio > 0.3: color = '#FFA500'
                else: color = '#FF0000'
                self.canvas.itemconfig(p['item'], fill=color)

        paddle_coords = self.paddle.get_position()
        for p in self.powerups.copy():
            p.update()
            p_coords = p.get_position()
            if p_coords[3] >= self.height: 
                p.delete()
                self.powerups.remove(p)
            elif (p_coords[2] >= paddle_coords[0] and p_coords[0] <= paddle_coords[2] and
                  p_coords[3] >= paddle_coords[1] and p_coords[1] <= paddle_coords[3]):
                
                if p.skill == 'multi':
                    self.spawn_extra_balls()
                elif p.skill == 'long':
                    self.paddle.grow()
                    if self.paddle_timer:
                        self.after_cancel(self.paddle_timer)
                    self.paddle_timer = self.after(10000, self.reset_paddle_length)
                elif p.skill == 'large':
                    for b in self.balls:
                        b.grow()
                elif p.skill == 'life':
                    self.lives += 1
                    self.update_hud()
                
                self.score += 50
                self.update_hud()
                
                p.delete()
                self.powerups.remove(p)

        # Update Bola + Buntut Api
        for b in self.balls.copy():
            coords = b.get_position()
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            self.spawn_trail(cx, cy, b.radius * 0.8) # Drop trail
            
            b.update()
            if b.get_position()[3] >= self.height:
                b.delete()
                self.balls.remove(b)

        num_bricks = len(self.canvas.find_withtag('brick'))
        
        if num_bricks == 0:
            self.level_complete()
            return
            
        elif len(self.balls) == 0: 
            self.lives -= 1
            self.update_hud()
            if self.lives < 0:
                self.game_over(win=False)
            else:
                self.after(500, self.setup_turn)
            return
        else:
            # LOOP SANGAT MULUS! 16 MILIDETIK (~60 FPS)
            self.after(16, self.game_loop)

    def check_collisions(self):
        for ball in self.balls:
            ball_coords = ball.get_position()
            items = self.canvas.find_overlapping(*ball_coords)
            objects = [self.items[x] for x in items if x in self.items]
            
            destroyed, hits = ball.collide(objects)
            
            if hits > 0:
                self.score += (hits * 10)
                self.update_hud()
            
            for d in destroyed:
                self.score += 40 
                self.update_hud()
                
                if d.item in self.items:
                    del self.items[d.item]
                
                if random.random() < 0.35:
                    skill = random.choice(['multi', 'long', 'large', 'life'])
                    coords = d.last_coords 
                    
                    x = (coords[0] + coords[2]) / 2
                    y = (coords[1] + coords[3]) / 2
                    p = PowerUp(self.canvas, x, y, skill)
                    self.powerups.append(p)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Dino Breakout: Jurassic Era')
    game = Game(root)
    game.mainloop()