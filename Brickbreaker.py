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

# Brick Object
class Brick(GameObject):
    COLORS = {1: '#ff4d4d', 2: '#ff1a1a', 3: '#cc0000'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
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
        self.canvas = tk.Canvas(self, bg='#aaaaff', width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()

        self.highscore_file = "highscore.txt"
        self.high_score = self.load_high_score()
        
        self.state = 'MENU' # Status game: MENU, WAITING, PLAYING, GAME_OVER
        
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.move_paddle(-15))
        self.canvas.bind('<Right>', lambda _: self.move_paddle(15))
        
        self.show_menu()

    def load_high_score(self):
        # Membaca top score dari file jika ada
        if os.path.exists(self.highscore_file):
            try:
                with open(self.highscore_file, "r") as f:
                    return int(f.read())
            except:
                return 0
        return 0

    def save_high_score(self):
        # Menyimpan top score ke file
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(self.highscore_file, "w") as f:
                    f.write(str(self.high_score))
            except:
                pass

    def move_paddle(self, offset):
        # Hanya bisa gerak jika game sedang main atau menunggu spasi
        if self.state in ['WAITING', 'PLAYING']:
            self.paddle.move(offset)

    def show_menu(self):
        self.state = 'MENU'
        self.canvas.delete('all')
        self.high_score = self.load_high_score()
        
        self.draw_text(self.width/2, 120, 'BREAKOUT', size='45')
        self.draw_text(self.width/2, 170, 'Love Edition', size='25')
        self.draw_text(self.width/2, 230, f'Top Score: {self.high_score}', size='20')
        self.draw_text(self.width/2, 300, 'Press SPACE to Start', size='15')
        
        self.canvas.bind('<space>', lambda _: self.init_game())

    def init_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete('all')
        
        self.lives = 3
        self.score = 0
        self.items = {}
        self.balls = []
        self.powerups = []
        self.hud = None

        # Membuat teks indikator skill di bawah
        skill_text = "Drop Skill: Ungu (Multi) | Biru (Panjang) | Hijau (Besar) | Merah (+Nyawa)"
        self.canvas.create_text(self.width/2, self.height - 15, text=skill_text, 
                                font=('Arial', 9, 'bold'), fill='#333333')

        self.paddle = Paddle(self.canvas, self.width / 2, 340)
        self.items[self.paddle.item] = self.paddle
        
        self.setup_bricks()
        self.update_hud()
        self.setup_turn()

    def setup_bricks(self):
        pattern = [
            [0, 2, 2, 0, 2, 2, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 2, 1, 3, 1, 2, 1],
            [0, 1, 1, 2, 1, 1, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ]
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

    def setup_turn(self):
        self.state = 'WAITING'
        for p in self.powerups:
            p.delete()
        self.powerups = []
        self.paddle.reset()
        
        for b in self.balls:
            b.delete()
        self.balls = []
        
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        ball = Ball(self.canvas, x, 324)
        self.balls.append(ball)
        self.paddle.set_ball(ball)

        self.text_msg = self.draw_text(self.width/2, 220, 'Press Space to Launch', size='20')
        self.canvas.bind('<space>', lambda _: self.start_turn())

    def start_turn(self):
        self.state = 'PLAYING'
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text_msg)
        self.paddle.ball = None
        self.game_loop()

    def spawn_extra_balls(self):
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        y = paddle_coords[1] - 15
        
        directions = [[-1, -1], [1, -1]]
        for d in directions:
            b = Ball(self.canvas, x, y)
            b.direction = d
            self.balls.append(b)

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text, font=font)

    def update_hud(self):
        text = f"Score: {self.score}   |   Lives: {self.lives}   |   Top Score: {max(self.score, self.high_score)}"
        if self.hud is None:
            self.hud = self.canvas.create_text(self.width/2, 20, text=text, font=('Arial', 12, 'bold'))
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def game_over(self, win):
        self.state = 'GAME_OVER'
        self.save_high_score()
        for b in self.balls: b.speed = 0
        msg = 'YOU WIN!' if win else 'GAME OVER!'
        self.draw_text(self.width/2, 200, msg, size='40')
        
        # Tunggu 3 detik lalu kembali ke menu utama
        self.after(3000, self.show_menu)

    def game_loop(self):
        if self.state != 'PLAYING':
            return

        self.check_collisions()

        paddle_coords = self.paddle.get_position()
        for p in self.powerups.copy():
            p.update()
            p_coords = p.get_position()
            if p_coords[3] >= self.height: 
                p.delete()
                self.powerups.remove(p)
            elif (p_coords[2] >= paddle_coords[0] and p_coords[0] <= paddle_coords[2] and
                  p_coords[3] >= paddle_coords[1] and p_coords[1] <= paddle_coords[3]):
                
                # Cek tipe skill yang ditangkap
                if p.skill == 'multi':
                    self.spawn_extra_balls()
                elif p.skill == 'long':
                    self.paddle.grow()
                elif p.skill == 'large':
                    for b in self.balls:
                        b.grow()
                elif p.skill == 'life':
                    self.lives += 1 # Menambah nyawa
                    self.update_hud()
                
                self.score += 50 # Bonus skor nangkap skill
                self.update_hud()
                
                p.delete()
                self.powerups.remove(p)

        for b in self.balls.copy():
            b.update()
            if b.get_position()[3] >= self.height:
                b.delete()
                self.balls.remove(b)

        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.game_over(win=True)
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
            self.after(50, self.game_loop)

    def check_collisions(self):
        for ball in self.balls:
            ball_coords = ball.get_position()
            items = self.canvas.find_overlapping(*ball_coords)
            objects = [self.items[x] for x in items if x in self.items]
            
            # Ambil data brick yang hancur dan seberapa banyak hit terjadi
            destroyed, hits = ball.collide(objects)
            
            # Tambah skor 10 untuk setiap pantulan bata
            if hits > 0:
                self.score += (hits * 10)
                self.update_hud()
            
            for d in destroyed:
                self.score += 40 # Bonus 40 jika bata hancur (Total 50 per bata)
                self.update_hud()
                
                if d.item in self.items:
                    del self.items[d.item]
                
                # 35% peluang mengeluarkan skill
                if random.random() < 0.35:
                    # 'life' dimasukkan ke dalam daftar skill yang bisa jatuh
                    skill = random.choice(['multi', 'long', 'large', 'life'])
                    coords = d.last_coords 
                    
                    x = (coords[0] + coords[2]) / 2
                    y = (coords[1] + coords[3]) / 2
                    p = PowerUp(self.canvas, x, y, skill)
                    self.powerups.append(p)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Breakout: Love Edition')
    game = Game(root)
    game.mainloop()