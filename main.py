import pygame
from pygame import Vector2
from enum import Enum
from math import floor, sqrt
from astar import find_path


# Constants
speed = 4
dot_score = 10
power_score = 50
ghost_mul = 100
scared_duration = 8
eaten_speed_mul = 2
scared_speed_mul = 0.7
top_size = 2


def lerp(a, b, t):
    return a + (b - a) * t


class Tile(Enum):
    Empty = 0
    Wall = 1
    Dot = 2
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


def floor_pos(pos: Vector2):
    return Vector2(int(pos.x), int(pos.y))


class Board:

    def __init__(self):
        self.tiles = []
        self.time = 0
        self.max_dots = 0
        self.width = 0
        self.height = 0

    def __getitem__(self, key):
        if key.x < 0 or key.x >= self.width:
            return None
        if key.y < 0 or key.y >= self.height:
            return None
        return self.tiles[int(key.y)][int(key.x)]

    def scatter(self):
        return (self.time**2 % 100) ** 1.2 < 10

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

    def pathable_neighbors(self, start: Vector2):
        start = floor_pos(start)
        pathable = []
        for x, y in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            dir = Vector2(x, y)
            tile = self[start + dir]
            if tile and tile != Tile.Wall:
                pathable.append(start + dir)
        return pathable


class Pacman:
    def __init__(self, spawn):
        self.spawn = spawn
        self.reset()

    def reset(self):
        self.pos = self.spawn
        self.dir = Vector2(0)
        self.queue = None
        self.size = 1

    def render(self, screen, offset, scale):
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            offset + self.pos * scale,
            scale / 2 * self.size,
        )

    def can_move_toward(self, dir, board):
        target_tile = board.get_wrapped(floor_pos(self.pos + dir))
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
        if new_dir.length() > 0:
            if self.can_move_toward(new_dir, board):
                if self.dir.dot(new_dir) == 0:
                    if new_dir.x != 0:
                        if self.pos.y % 1 > 0.4 and self.pos.y % 1 < 0.6:
                            self.pos.y = floor(self.pos.y) + 0.5
                            self.dir = new_dir
                        else:
                            self.queue = new_dir
                    elif new_dir.y != 0:
                        if self.pos.x % 1 > 0.4 and self.pos.x % 1 < 0.6:
                            self.pos.x = floor(self.pos.x) + 0.5
                            self.dir = new_dir
                        else:
                            self.queue = new_dir
                else:
                    self.dir = new_dir
                    self.queue = None
            else:
                self.queue = new_dir
        elif self.queue and self.can_move_toward(self.queue, board):
            if self.queue.x != 0:
                if self.pos.y % 1 > 0.4 and self.pos.y % 1 < 0.6:
                    self.pos.y = floor(self.pos.y) + 0.5
                    self.dir = self.queue
                    self.queue = None
            elif self.queue.y != 0:
                if self.pos.x % 1 > 0.4 and self.pos.x % 1 < 0.6:
                    self.pos.x = floor(self.pos.x) + 0.5
                    self.dir = self.queue
                    self.queue = None
        elif not self.can_move_toward(self.dir * 0.5, board):
            self.dir = Vector2(0)

        # Update position
        self.pos += self.dir * dt * speed
        self.pos = board.wrap(self.pos)


class Ghost:
    class State(Enum):
        ChaseScatter = 0
        Scared = 1
        Eaten = 2

    colors = [(255, 0, 0), (0, 255, 255), (255, 128, 255), (255, 128, 0)]

    def __init__(self, id, spawn: Vector2):
        self.id = id
        self.spawn: Vector2 = spawn
        self.reset()

    def reset(self):
        self.pos: Vector2 = self.spawn
        self.dest = None
        self.state = Ghost.State.ChaseScatter

    def update(self, dt, pac: Pacman, ghosts, board: Board):
        speed_mul = speed * (
            eaten_speed_mul
            if self.state == Ghost.State.Eaten
            else scared_speed_mul if self.state == Ghost.State.Scared else 1
        )
        if self.dest:
            # Move toward destination
            diff = self.dest - self.pos
            if diff.length() < dt * speed_mul:
                self.pos = self.dest
                self.dest = None
                if (
                    self.state == Ghost.State.Eaten
                    and (self.pos - self.spawn).length() < 0.1
                ):
                    self.state = Ghost.State.ChaseScatter
            elif diff.length() > 0:
                self.pos = self.pos + dt * speed_mul * diff.normalize()
        else:
            # Choose new destination
            start = (int(self.pos.x), int(self.pos.y))
            scatters = dest = [
                Vector2(board.width - 2, 1),
                Vector2(board.width - 2, board.height - 2),
                Vector2(1, 1),
                Vector2(1, board.height - 2),
            ]
            match self.state:
                case Ghost.State.ChaseScatter:
                    if board.scatter():
                        dest = scatters[self.id % 4]
                    else:
                        match self.id:
                            case 0:
                                dest = pac.pos
                            case 1:
                                dest = lerp(pac.pos, ghosts[0].pos, 2)
                                if board[dest] == Tile.Wall:
                                    dest = pac.pos
                            case 2:
                                for mul in [2, 1]:
                                    if pac.can_move_toward(mul * pac.dir, board):
                                        dest = pac.pos + mul * pac.dir
                                        break
                                else:
                                    dest = pac.pos
                            case 3:
                                if (self.pos - pac.pos).length() <= 8:
                                    dest = scatters[3]
                                else:
                                    dest = pac.pos
                            case _:
                                dest = self.pos
                case Ghost.State.Scared:
                    dest = scatters[self.id % 4]
                case Ghost.State.Eaten:
                    dest = self.spawn
            dest = (int(dest.x), int(dest.y))
            path = find_path(
                start,
                dest,
                lambda pos: [
                    (v[0], v[1])
                    for v in board.pathable_neighbors(Vector2(pos[0], pos[1]))
                ],
                heuristic_cost_estimate_fnct=lambda a, b: sqrt(
                    (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                ),
            )
            path = [x for x in path] if path else []
            if len(path) >= 2:
                self.dest = Vector2(path[1][0], path[1][1]) + Vector2(0.5)

    def render(self, screen, offset, scale, scared_timer):
        color = (
            Ghost.colors[self.id]
            if self.state == Ghost.State.ChaseScatter
            else (
                (0, 0, 255)
                if self.state == Ghost.State.Scared
                and (scared_timer > 2 or scared_timer % 0.4 < 0.2)
                else (255, 255, 255)
            )
        )
        if self.state == Ghost.State.Eaten:
            tl = offset + (self.pos - Vector2(0.5)) * scale + Vector2(0, scale * 0.4)
            size = Vector2(scale, scale * 0.2)
        else:
            tl = (
                offset
                + (self.pos - Vector2(0.5, 0.1)) * scale
                + Vector2(scale * 0.1, 0)
            )
            size = Vector2(scale * 0.8, scale * 0.6)
            pygame.draw.circle(
                screen,
                color,
                offset + (self.pos - Vector2(0, 0.1)) * scale,
                0.4 * scale,
            )
        pygame.draw.rect(screen, color, (tl, size))


class Game:
    class State:
        Start = 0
        Playing = 1
        Dying = 2
        Lose = 3
        Win = 4

    def __init__(self):
        self.state = Game.State.Start
        self.board = Board()
        self.board.height = len(board_spec)
        self.board.width = len(board_spec[0])
        self.ghosts: list[Ghost] = []
        self.score = 0
        self.scared_timer = 0
        self.dots_eaten = 0
        self.ghosts_eaten = 0
        self.lives = 2
        for j, line in enumerate(board_spec):
            row = []
            for i, c in enumerate(line):
                match c:
                    case "X":
                        row.append(Tile.Wall)
                    case " ":
                        row.append(Tile.Empty)
                    case ".":
                        row.append(Tile.Dot)
                        self.board.max_dots += 1
                    case "o":
                        row.append(Tile.Power)
                        self.board.max_dots += 1
                    case "-":
                        row.append(Tile.Gate)
                    case "1" | "2" | "3" | "4":
                        row.append(Tile.Empty)
                        id = "1234".index(c)
                        while len(self.ghosts) <= id:
                            self.ghosts.append(Ghost(0, Vector2()))
                        self.ghosts[id] = Ghost(id, Vector2(i, j) + Vector2(0.5))
                    case "S":
                        row.append(Tile.Empty)
                        self.pac = Pacman(Vector2(i, j) + Vector2(0.5))
            self.board.tiles.append(row)

    def update(self, dt):
        match self.state:
            case Game.State.Playing:
                # Update entities
                self.pac.update(dt, self.board)
                for ghost in self.ghosts:
                    ghost.update(dt, self.pac, self.ghosts, self.board)

                # Eat dots
                match self.board.get_wrapped(self.pac.pos):
                    case Tile.Dot:
                        self.board.set_wrapped(self.pac.pos, Tile.Empty)
                        self.score += dot_score
                        self.dots_eaten += 1
                    case Tile.Power:
                        self.board.set_wrapped(self.pac.pos, Tile.Empty)
                        self.score += power_score
                        self.dots_eaten += 1
                        self.scared_timer = scared_duration
                        for ghost in self.ghosts:
                            ghost.state = Ghost.State.Scared

                # Pac/Ghost collision
                for ghost in self.ghosts:
                    if (ghost.pos - self.pac.pos).length() < 0.3:
                        match ghost.state:
                            case Ghost.State.ChaseScatter:
                                self.state = Game.State.Dying
                                return
                            case Ghost.State.Scared:
                                ghost.state = Ghost.State.Eaten
                                self.ghosts_eaten += 1
                                self.score += ghost_mul * 2 ** min(self.ghosts_eaten, 4)

                # Win condition
                if self.dots_eaten == self.board.max_dots:
                    self.state = Game.State.Win
                    return

                self.board.time += dt

                # Scared timer
                self.scared_timer = max(0, self.scared_timer - dt)
                if self.scared_timer == 0:
                    for ghost in self.ghosts:
                        if ghost.state == Ghost.State.Scared:
                            ghost.state = Ghost.State.ChaseScatter
            case Game.State.Dying:
                self.pac.size = max(0, self.pac.size - 0.5 * dt)
                if self.pac.size == 0:
                    if self.lives == 0:
                        self.state = Game.State.Lose
                    else:
                        self.lives = 1
                        self.pac.reset()
                        for ghost in self.ghosts:
                            ghost.reset()
                        self.state = Game.State.Playing

    def space(self):
        match self.state:
            case Game.State.Start | Game.State.Lose | Game.State.Win:
                self.__init__()
                self.state = Game.State.Playing

    def render(self, screen):
        screen_size = Vector2(screen.get_width(), screen.get_height())
        scale = min(
            screen_size.x / (self.board.width + top_size),
            screen_size.y / (self.board.height + top_size),
        )
        screen.fill((0, 0, 0))
        top_offset = Vector2(0, top_size * scale)
        offset = (
            (screen_size - top_offset) / 2
            - Vector2(
                scale * self.board.width / 2,
                scale * self.board.height / 2,
            )
            + top_offset
        )
        match self.state:
            case Game.State.Start:
                screen.blit(
                    text("PAC-MAN", scale * 4, (255, 255, 0)),
                    offset + Vector2(0, scale * top_size),
                )
                screen.blit(
                    text("Press SPACE to start", scale * 2, (255, 255, 0)),
                    offset + Vector2(0, scale * (top_size + 6)),
                )
            case Game.State.Playing:
                self.render_game(screen, scale, offset)
            case Game.State.Dying:
                self.render_game(screen, scale, offset)
            case Game.State.Lose:
                self.render_game(screen, scale, offset)
                draw_rect_alpha(screen, (0, 0, 0, 180), (Vector2(), screen_size))
                screen.blit(
                    text("GAME OVER!", scale * 4, (255, 255, 0)),
                    offset + Vector2(0, scale * top_size),
                )
                screen.blit(
                    text("Press SPACE to play again", scale * 2, (255, 255, 0)),
                    offset + Vector2(0, scale * (top_size + 6)),
                )
            case Game.State.Win:
                self.render_game(screen, scale, offset)
                draw_rect_alpha(screen, (0, 0, 0, 180), (Vector2(), screen_size))
                screen.blit(
                    text("YOU WIN!", scale * 4, (255, 255, 0)),
                    offset + Vector2(0, scale * top_size),
                )
                screen.blit(
                    text("Press SPACE to play again", scale * 2, (255, 255, 0)),
                    offset + Vector2(0, scale * (top_size + 6)),
                )

    def render_game(self, screen, scale, offset):

        # Score
        screen.blit(
            text(str(self.score).zfill(4), top_size * scale, "white"),
            offset - Vector2(0, top_size * scale),
        )

        # Lives
        for i in range(self.lives):
            pos = offset + scale * Vector2(self.board.width - 0.5 - i, -0.5)
            pygame.draw.circle(screen, (255, 255, 0), pos, scale * 0.5)

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
                    case Tile.Dot:
                        pygame.draw.circle(screen, (255, 255, 128), center, scale / 8)
                    case Tile.Power:
                        pygame.draw.circle(screen, (255, 255, 128), center, scale / 3)
                    case Tile.Gate:
                        corner.y += scale * 0.4
                        size.y *= 0.2
                        pygame.draw.rect(screen, (255, 255, 255), (corner, size))

        if self.state == Game.State.Playing:
            self.pac.render(screen, offset, scale)

        # Ghosts
        for ghost in self.ghosts:
            ghost.render(screen, offset, scale, self.scared_timer)

        if self.state != Game.State.Playing:
            self.pac.render(screen, offset, scale)


def text(str, size, color):
    """Create a text surface with a cached font"""
    size = int(size)
    if size not in text_dict:
        text_dict[size] = pygame.font.Font(pygame.font.get_default_font(), size)
    return text_dict[size].render(str, True, color)


text_dict = {}


def draw_rect_alpha(surface, color, rect):
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)


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
