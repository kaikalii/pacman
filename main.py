import pygame
from pygame import Vector2
from enum import Enum


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
    "      .XX X 1234 X XX.      ",
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
        return self.tiles[key.y][key.x]


class Entity:
    def __init__(self, pos):
        self.pos = pos
        self.dest = pos
        self.prog = 0

    def render_pos(self):
        return Vector2(
            lerp(self.pos.x, self.dest.x, self.prog),
            lerp(self.pos.y, self.dest.y, self.prog),
        )

    def update(self, dt):
        self.prog += dt
        if self.prog >= 1:
            self.pos = self.dest
            self.prog %= 1
            return True
        else:
            return False


class Pacman(Entity):
    def __init__(self, pos):
        super().__init__(pos)

    def render(self, screen, offset, scale):
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            offset + self.render_pos() * scale + Vector2(scale) / 2,
            scale / 2,
        )

    def update(self, dt, board):
        super().update(dt)


class Ghost(Entity):
    colors = [(255, 128, 255), (255, 128, 0), (0, 255, 255), (255, 0, 0)]

    def __init__(self, id, pos):
        super().__init__(pos)
        self.id = id
        self.fleeing = False

    def render(self, screen, offset, scale):
        color = (0, 0, 255) if self.fleeing else Ghost.colors[self.id]
        tl = offset + self.render_pos() * scale + Vector2(scale * 0.1, 0)
        size = Vector2(scale * 0.8, scale)
        pygame.draw.rect(screen, color, (tl, size))


class Game:
    def __init__(self):
        self.board = Board()
        self.board.height = len(board_spec)
        self.board.width = len(board_spec[0])
        self.board.tiles = []
        self.ghosts = [None, None, None, None]
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
                        self.ghosts[id] = Ghost(id, Vector2(i, j))
                    case "S":
                        row.append(Tile.Empty)
                        self.pac = Pacman(Vector2(i, j))
            self.board.tiles.append(row)

    def update(self, dt):
        self.pac.update(dt, self.board)
        for ghost in self.ghosts:
            ghost.update(dt)

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
