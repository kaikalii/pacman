import pygame
from pygame import Vector2
from enum import Enum


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
    "      .XX X      X XX.      ",
    "XXXXXX.XX X      X XX.XXXXXX",
    "     X.XX XXXXXXXX XX.X     ",
    "     X.XX          XX.X     ",
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
        self.height = len(board_spec)
        self.width = len(board_spec[0])
        self.tiles = []
        for line in board_spec:
            row = []
            for c in line:
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
            self.tiles.append(row)

    def __getitem__(self, key):
        if key.x >= self.width:
            return None
        if key.y >= self.height:
            return None
        return self.tiles[key.y][key.x]


class Game:
    def __init__(self):
        self.board = Board()
        self.pos = Vector2(13, 16)

    def update(self, dt):
        pass

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
                size = Vector2(scale, scale)
                center = corner + size / 2
                size += Vector2(1, 1)  # Render fix
                match tile:
                    case Tile.Wall:
                        pygame.draw.rect(screen, (0, 0, 244), (corner, size))
                    case Tile.Pellet:
                        pygame.draw.circle(screen, (255, 255, 0), center, scale / 8)
                    case Tile.Power:
                        pygame.draw.circle(screen, (255, 255, 0), center, scale / 3)
                    case Tile.Gate:
                        corner.y += scale * 0.4
                        size.y *= 0.2
                        pygame.draw.rect(screen, (255, 255, 255), (corner, size))


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
