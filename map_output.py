import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame

import threading
import queue


def midcolor(color1, color2):
    return tuple((a+b)//2 for a, b in zip(color1, color2))


class Colors:

    reliefs = [
        (100, 100, 100),
        (255, 255, 255),

        (100, 100, 200),
        (200, 100, 100),

        (205, 205, 205),
        (155, 155, 155),
        (105, 105, 105),
        # (205, 55, 55)
    ]

    temperatures = [
        (16, 91, 222),
        (16, 194, 222),
        (16, 222, 44),
        (222, 147, 16),
        (222, 44, 16)
    ]

    colors = [
    [
        (97, 242, 255),
        (99, 209, 255),
        (93, 166, 255),
        (87, 129, 255),
        (100, 109, 233)
    ],
    [
        (238, 230, 36),
        (161, 229, 55),
        (109, 204, 0),
        (53, 193, 110),
        (0, 161, 87)
    ],
    [
        (206, 193, 75),
        (185, 167, 51),
        (149, 142, 0),
        (121, 134, 69),
        (130, 157, 87)
    ],
    [
        (206, 193, 155),
        (185, 167, 154),
        (149, 142, 142),
        (121, 134, 141),
        (147, 171, 168)

    ],
    [
        (230, 172, 151),
        (209, 185, 171),
        (194, 194, 204),
        (220, 224, 231),
        (223, 233, 240)
    ]
]



class Output:

    def clear(self):
        pass

    def tile_relief(self, tile):
        pass

    def map_relief(self, grid):
        pass

    def overlay_temperature(self, tile, landmass, resolution=1):
        pass


class PyGame(Output):

    def __init__(self, height, width, pixel_size=2):

        self.height = height
        self.width = width
        self.pixel_size = pixel_size

        self.dimensions = (width*pixel_size, height*pixel_size)

        self.queue = queue.Queue()

    def run(self, main_loop):

        self.window = pygame.display.set_mode(self.dimensions)
        pygame.display.set_caption("Map Generator")

        self.thread = threading.Thread(target=main_loop)
        self.thread.daemon = True
        self.thread.start()

        self.event_loop()

    def event_check(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

    def event_loop(self):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.event_check()
            items = 0
            while not self.queue.empty():
                self.event_check()
                code, data = self.queue.get()
                if code == 'pixel':
                    pos, color = data
                    self.window.set_at(pos, color)
                elif code == 'clear':
                    self.window.fill((0, 0, 0))
                if items % 200 == 0:
                    pygame.display.update()
                items += 1
            pygame.display.update()

    def clear(self):
        self.queue.put(('clear', None))

    def plot(self, pos, color):
        for x_off in range(self.pixel_size):
            for y_off in range(0, self.pixel_size):
                x = pos[0]*self.pixel_size + x_off
                y = pos[1]*self.pixel_size + y_off
                self.queue.put(('pixel', ((x, y), color)))

    def tile_relief(self, tile):
        color = Colors.reliefs[tile.value]
        self.plot((tile.x, tile.y), color)

    def tile_temperature(self, tile, resolution=1):
        color = Colors.temperatures[tile.value]
        for x_off in range(resolution):
            for y_off in range(resolution):
                x = tile.x*resolution + x_off
                y = tile.y*resolution + y_off
                self.plot((x, y), color)

    def map_relief(self, grid):
        for col in grid:
            for tile in col:
                self.tile_relief(tile)

    def overlay_temperature(self, tile, landmass, resolution=1):
        x_off = tile.x*resolution
        y_off = tile.y*resolution
        for x in range(resolution):
            if x+x_off >= self.width:
                break
            for y in range(resolution):
                if y+y_off >= self.height:
                    break
                under_tile = landmass[x+x_off][y+y_off]
                color = Colors.colors[under_tile.value][tile.value]
                self.plot((x+x_off, y+y_off), color)
