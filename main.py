import pygame
from pygame import Vector2
from enum import Enum
from math import floor


def lerp(a, b, t):
    return a + (b - a) * t


class Tile(Enum):
    Empty = 0
    Wall = 1
    Pellet = 2
    Power = 3
    Gate = 4


board_spec = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X............XX............X",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "XoXXXX.XXXXX.XX.XXXXX.XXXXoX",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "X..........................X",
    "X.XXXX.XX.XXXXXXXX.XX.XXXX.X",
    "X.XXXX.XX.XXXXXXXX.XX.XXXX.X",
    "X......XX....XX....XX......X",
    "XXXXXX.XXXXX XX XXXXX.XXXXXX",
    "     X.XX          XX.X     ",
    "     X.XX XXX--XXX XX.X     ",
    "XXXXXX.XX X      X XX.XXXXXX",
    "      ... X 1234 X ...      ",
    "XXXXXX.XX X      X XX.XXXXXX",
    "     X.XX XXXXXXXX XX.X     ",
    "     X.XX    S     XX.X     ",
    "XXXXXX.XX XXXXXXXX XX.XXXXXX",
    "X............XX............X",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "Xo..XX................XX..oX",
    "XXX.XX.XX.XXXXXXXX.XX.XX.XXX",
    "XXX.XX.XX.XXXXXXXX.XX.XX.XXX",
    "X......XX....XX....XX......X",
    "X.XXXXXXXXXX.XX.XXXXXXXXXX.X",
    "X.XXXXXXXXXX.XX.XXXXXXXXXX.X",
    "X..........................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]


class Board:
    def __init__(self):
        pass

    def __getitem__(self, key):
        if key.x >= self.width:
            return None
        if key.y >= self.height:
            return None
        return self.tiles[int(key.y)][int(key.x)]

    def wrap(self, pos):
        return Vector2(
            (pos.x % self.width + self.width) % self.width,
            (pos.y % self.height + self.height) % self.height,
        )

    def get_wrapped(self, key):
        key = self.wrap(key)
        return self.tiles[int(key.y)][int(key.x)]

    def set_wrapped(self, key, val):
        key = self.wrap(key)
        self.tiles[int(key.y)][int(key.x)] = val


speed = 3


class Pacman:
    def __init__(self, pos):
        self.pos = pos
        self.dir = Vector2(0)

    def render(self, screen, offset, scale):
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            offset + self.pos * scale,
            scale / 2,
        )

    def can_move_toward(self, dir, board):
        target_idx = self.pos + dir
        target_idx.x = floor(target_idx.x)
        target_idx.y = floor(target_idx.y)
        target_tile = board.get_wrapped(target_idx)
        return target_tile != Tile.Wall and target_tile != Tile.Gate

    def update(self, dt, board):
        # Get intended direction
        keys = pygame.key.get_pressed()
        new_dir = Vector2(0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_dir.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_dir.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            new_dir.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            new_dir.x += 1
        if new_dir.x != 0:
            new_dir.y = 0

        # Set direction
        if new_dir.length() > 0 and self.can_move_toward(new_dir, board):
            if self.dir.dot(new_dir) == 0:
                if new_dir.x != 0 and (self.pos.y % 1 > 0.4 and self.pos.y % 1 < 0.6):
                    self.pos.y = floor(self.pos.y) + 0.5
                    self.dir = new_dir
                elif new_dir.y != 0 and (self.pos.x % 1 > 0.4 and self.pos.x % 1 < 0.6):
                    self.pos.x = floor(self.pos.x) + 0.5
                    self.dir = new_dir
            else:
                self.dir = new_dir
        elif not self.can_move_toward(self.dir * 0.5, board):
            self.dir = Vector2(0)

        # Update position
        self.pos += self.dir * dt * speed
        self.pos = board.wrap(self.pos)


class Ghost:
    class State(Enum):
        Normal = 0
        Fleeing = 1
        Respawning = 2

    colors = [(255, 128, 255), (255, 128, 0), (0, 255, 255), (255, 0, 0)]

    def __init__(self, id, pos):
        self.id = id
        self.pos = pos
        self.state = Ghost.State.Normal

    def render(self, screen, offset, scale):
        color = [
            Ghost.colors[self.id],
            (0, 0, 255),
            (255, 255, 255),
        ][self.state.value]
        tl = offset + self.pos * scale + Vector2(scale * 0.1, 0)
        size = Vector2(scale * 0.8, scale)
        pygame.draw.rect(screen, color, (tl, size))

    def update(self, dt):
        pass


class Game:
    def __init__(self):
        self.board = Board()
        self.board.height = len(board_spec)
        self.board.width = len(board_spec[0])
        self.board.tiles = []
        self.ghosts = []
        self.score = 0
        self.flee_timer = 0
        for j, line in enumerate(board_spec):
            row = []
            for i, c in enumerate(line):
                match c:
                    case "X":
                        row.append(Tile.Wall)
                    case " ":
                        row.append(Tile.Empty)
                    case ".":
                        row.append(Tile.Pellet)
                    case "o":
                        row.append(Tile.Power)
                    case "-":
                        row.append(Tile.Gate)
                    case "1" | "2" | "3" | "4":
                        row.append(Tile.Empty)
                        id = "1234".index(c)
                        while len(self.ghosts) <= id:
                            self.ghosts.append(Ghost(0, Vector2()))
                        self.ghosts[id] = Ghost(id, Vector2(i, j))
                    case "S":
                        row.append(Tile.Empty)
                        self.pac = Pacman(Vector2(i, j) + Vector2(0.5))
            self.board.tiles.append(row)

    def update(self, dt):
        self.pac.update(dt, self.board)
        for ghost in self.ghosts:
            ghost.update(dt)

        match self.board.get_wrapped(self.pac.pos):
            case Tile.Pellet:
                self.board.set_wrapped(self.pac.pos, Tile.Empty)
                self.score += 1
            case Tile.Power:
                self.board.set_wrapped(self.pac.pos, Tile.Empty)
                self.score += 1
                self.flee_timer = 10
                for ghost in self.ghosts:
                    ghost.state = Ghost.State.Fleeing

        self.flee_timer = max(0, self.flee_timer - dt)
        if self.flee_timer == 0:
            for ghost in self.ghosts:
                if ghost.state == Ghost.State.Fleeing:
                    ghost.state = Ghost.State.Normal

    def render(self, screen):
        screen_size = Vector2(screen.get_width(), screen.get_height())
        scale = min(screen_size.x / self.board.width, screen_size.y / self.board.height)
        screen.fill((0, 0, 0))
        offset = Vector2(
            screen_size.x / 2 - scale * self.board.width / 2,
            screen_size.y / 2 - scale * self.board.height / 2,
        )
        # Board
        for j, row in enumerate(self.board.tiles):
            for i, tile in enumerate(row):
                corner = offset + Vector2(i, j) * scale
                size = Vector2(scale)
                center = corner + size / 2
                size += Vector2(1, 1)  # Render fix
                match tile:
                    case Tile.Wall:
                        pygame.draw.rect(screen, (0, 0, 244), (corner, size))
                    case Tile.Pellet:
                        pygame.draw.circle(screen, (255, 255, 128), center, scale / 8)
                    case Tile.Power:
                        pygame.draw.circle(screen, (255, 255, 128), center, scale / 3)
                    case Tile.Gate:
                        corner.y += scale * 0.4
                        size.y *= 0.2
                        pygame.draw.rect(screen, (255, 255, 255), (corner, size))

        # Pacman
        self.pac.render(screen, offset, scale)

        # Ghosts
        for ghost in self.ghosts:
            ghost.render(screen, offset, scale)


def text(str, size, color):
    """Create a text surface with a cached font"""
    if size not in text_dict:
        text_dict[size] = pygame.font.Font(pygame.font.get_default_font(), size)
    return text_dict[size].render(str, True, color)


text_dict = {}

# Initialization
pygame.init()
pygame.font.init()
pygame.display.set_caption("Pop the Lock")
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
clock = pygame.time.Clock()
game = Game()

running = True

# Main loop
while running:

    # Handle events
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_SPACE:
                        game.space()

    # Update
    game.update(clock.tick(120) / 1000)

    # Render
    game.render(screen)
    pygame.display.flip()

pygame.quit()
