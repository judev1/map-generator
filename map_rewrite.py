from map_output import Output
import random
import math


class Tile:

    def __init__(self, grid, pos, value):
        """ Describes an individual tile in the grid """

        self.grid = grid
        self.pos = pos
        self.x, self.y = pos
        self.value = value

        self.has_collapsed_adjacent = False

    def __repr__(self):
        return f'<Tile {self.pos} {self.value}>'

    def get_tiles(self, layer):

        tiles = list()
        x, y = self.pos
        grid = self.grid
        if y - layer >= 0:
            for off in range(-layer, layer):
                if x + off < 0 or x + off > grid.width - 1:
                    continue
                tiles.append(grid[x + off][y - layer])
        if x + layer < grid.width:
            for off in range(-layer, layer):
                if y + off < 0 or y + off > grid.height - 1:
                    continue
                tiles.append(grid[x + layer][y + off])
        if y + layer < grid.height:
            for off in range(layer, -layer, -1):
                if x + off < 0 or x + off > grid.width - 1:
                    continue
                tiles.append(grid[x + off][y + layer])
        if x - layer >= 0:
            for off in range(layer, -layer, -1):
                if y + off < 0 or y + off > grid.height - 1:
                    continue
                tiles.append(grid[x - layer][y + off])
        return tiles

    def load_adjacent(self, layers=1):
        """ Finds and stores all adjacent tiles. The importance of layers is to
            prevent incompatable tiles from being plotted too close to one
            another """

        self.adjacent = list()
        for layer in range(layers):
            self.adjacent.append(self.get_tiles(layer+1))

    def collapse(self, value):
        self.value = value
        for tile in self.adjacent[0]:
            tile.has_collapsed_adjacent = True


class Grid:

    def __init__(self, height, width, grid=None, default=-1):
        """ Creates a grid of tiles """

        self.height = height
        self.width = width

        if grid is None:
            grid = list()
            for x in range(width):
                grid.append(list())
                for y in range(height):
                    tile = Tile(self, (x, y), default)
                    grid[-1].append(tile)
        self.grid = grid

    def copy(self):
        """ Creates a copy of the grid """

        gridCopy = list()
        for col in self.grid:
            gridCopy.append(list())
            for tile in col:
                tileCopy = Tile(gridCopy, tile.pos, tile.value)
                tileCopy.has_collapsed_adjacent = tile.has_collapsed_adjacent
                if hasattr(tile, "adjacent"):
                    tileCopy.adjacent = tile.adjacent
                gridCopy[-1].append(tileCopy)
        return Grid(self.height, self.width, gridCopy)

    def __getitem__(self, row):
        """ Returns a tile at a given position """

        return self.grid[row]

    def find_next(self, tiles):
        """ Finds the next tile to collapse """

        for tile in tiles:
            if tile.has_collapsed_adjacent:
                tiles.remove(tile)
                return tile

        return tiles.pop()


class Map:

    water = 0
    land = 1

    layers = 2 # Can be modified
    climates = 5 # Must be constant

    def __init__(self, height, width, seed=None, output=Output()):
        """ Creates a new map with the given height and width, seed and output
            object """

        # Dimensions of the map
        self.height = height
        self.width = width

        # Generates a random 32 bit integer, allowing for 4,294,967,296 unique
        # seeds, if one is not provided
        if seed is None:
            seed = random.randint(0, 2**32-1)
        self.seed = seed

        # Stores an object to output the map
        self.output = output

        # Stores the states of the map so actions can be undone without
        # regenerating each state of the map
        self.states = list()

    def copy(self):
        """ Creates a copy of the map """

        map = Map(self.height, self.height, self.seed, self.output)
        if hasattr(self, 'landmass'):
            map.landmass = self.landmass.copy()
        if hasattr(self, 'heatmap'):
            map.heatmap = self.heatmap.copy()
        return map

    def save_state(self):
        """ Saves the current state of the map """

        self.states.append(self.copy())
        self.seed = random.randint(0, 2**32-1)

    def restore_state(self, index=-1):
        """ Restores the map to the given state """

        # # Resets the seed if the state does not share the same seed with the
        # # current map
        # if self.states[index].seed != self.seed:
        seed = self.states[index].seed

        # Remove all states from and including the given state
        del self.states[index:]

        if self.states:
            self.__dict__ = self.states[-1].__dict__
            self.seed = seed
            if hasattr(self, "landmass"):
                self.output.map_relief(self.landmass)
        else:
            new_map = Map(self.height, self.width, seed, self.output)
            self.__dict__ = new_map.__dict__
            self.output.clear()

    def generate_landmass(self, waterborder=4, control=10000):
        """ Generates land using wave function collapse """

        def in_bounds(x, y):
            """ Returns whether the given position is inside the water
                border """

            if x >= waterborder and x < self.width - waterborder:
                if y >= waterborder and y < self.height - waterborder:
                    return True

        def random_coords(x1, y1, x2, y2):
            """ Returns a random coordinate within the given range """

            x = random.randint(x1, x2)
            y = random.randint(y1, y2)
            return x, y

        def pick_value(tile, control):
            """ Picks a value for the given tile """

            def a(n):
                if n == 1:
                    return 1
                return a(n-1) + n*((n-1)**2)

            water = [[0 for i in range(Map.layers)], 0]
            land = [[0 for i in range(Map.layers)], 0]
            total = 8*a(Map.layers)
            for i in range(Map.layers):
                for adjacent in tile.adjacent[i]:
                    if adjacent.value == Map.water:
                        water[0][i] += 1
                        water[1] += 8*(Map.layers-i)*((Map.layers-i)**2)
                    elif adjacent.value == Map.land:
                        land[0][i] += 1
                        land[1] += 8*(Map.layers-i)*((Map.layers-i)**2)

            chance = random.randint(1, control)
            if chance == 1:
                return Map.water
            elif chance == 2:
                return Map.land

            chance = random.randint(1, total)
            if chance <= water[1]:
                return Map.water
            elif chance <= water[1] + land[1]:
                return Map.land

            chance = random.randint(1, 8)
            if chance <= water[0][0]:
                return Map.water
            elif chance <= water[0][0] + land[0][0]:
                return Map.land

            chance = random.randint(1, water[1] + land[1])
            if chance <= water[1]:
                return Map.water
            elif chance <= water[1] + land[1]:
                return Map.land

        random.seed(self.seed)
        self.landmass = Grid(self.height, self.width)

        # Creates a list of all tiles in the grid and shuffles it
        tiles = list()
        for x in range(self.width):
            for y in range(self.height):
                # If the tile is out of bounds, it is collapses to water
                tile = self.landmass[x][y]
                tile.load_adjacent(Map.layers)
                if not in_bounds(x, y):
                    tile.collapse(Map.water)
                    self.output.tile_relief(tile)
                else:
                    tiles.append(tile)
        random.shuffle(tiles)

        # Chooses a number of tiles that will be automatically determined to be
        # land and water
        landpoints = random.randint(2, 10)
        waterpoints = random.randint(0, 2)

        # The range of coordinates for the tiles that start off as land
        # and water
        off = waterborder
        ranges = (off, off, self.width-off, self.height-off)

        for i in range(landpoints):
            while True:
                x, y = random_coords(*ranges)
                if self.landmass[x][y].value == -1:
                    break
            tile = self.landmass[x][y]
            tile.collapse(Map.land)
            self.output.tile_relief(tile)

        for i in range(waterpoints):
            while True:
                x, y = random_coords(*ranges)
                if self.landmass[x][y].value == -1:
                    break
            tile = self.landmass[x][y]
            tile.collapse(Map.water)
            self.output.tile_relief(tile)

        while tiles:
            tile = self.landmass.find_next(tiles)
            tile.collapse(pick_value(tile, control))
            self.output.tile_relief(tile)

        self.save_state()

    def remove_lone_tiles(self, threshold=0):
        """ Removes tiles that are surrounded by tiles of the opposite value """

        for x in range(self.width):
            for y in range(self.height):
                count = 0
                tile = self.landmass[x][y]
                for adjacent in tile.adjacent[0]:
                    if adjacent.value == tile.value:
                        count += 1
                if count <= threshold:
                    if tile.value == Map.land:
                        tile.collapse(Map.water)
                        self.output.tile_relief(tile)
                    elif tile.value == Map.water:
                        tile.collapse(Map.land)
                        self.output.tile_relief(tile)

        self.save_state()

    def centre_landmass(self):
        """ Positions the landmass in the centre of the map """

        # Finds the bounds of the landmass
        x1 = self.width // 2
        y1 = self.height // 2
        x2 = self.width // 2
        y2 = self.height // 2

        for x in range(self.width):
            for y in range(self.height):
                tile = self.landmass[x][y]
                if tile.value == Map.land:
                    if x < x1:
                        x1 = x
                    if y < y1:
                        y1 = y
                    if x > x2:
                        x2 = x
                    if y > y2:
                        y2 = y

        # Shifts the landmass to the centre of the map
        dx = (self.width - (x2 - x1)) // 2 - x1
        dy = (self.height - (y2 - y1)) // 2 - y1

        new_landmass = Grid(self.height, self.width, default=Map.water)
        for x in range(self.width):
            for y in range(self.height):
                if self.landmass[x][y].value == Map.land:
                    new_landmass[x+dx][y+dy].value = Map.land
                    self.output.tile_relief(new_landmass[x+dx][y+dy])
        for x in range(self.width):
            for y in range(self.height):
                if self.landmass[x][y].value == Map.land:
                    if new_landmass[x][y].value == Map.water:
                        self.output.tile_relief(new_landmass[x][y])

        self.landmass = new_landmass
        self.save_state()

    def generate_heatmap(self, resolution=4, control=10000):
        """ Generates a heatmap using the landmass """

        def eliminate_possibilities(tile):
            """ Eliminates possibilities for the tile based on its neighbours """

            possibilities = [i for i in range(Map.climates)]
            for i, layer in enumerate(tile.adjacent):
                for adjacent in layer:
                    value = adjacent.value
                    if value == -1:
                        continue
                    for possibility in possibilities.copy():
                        if possibility > value + (i + 1):
                            possibilities.remove(possibility)
                        elif possibility < value - (i + 1):
                            possibilities.remove(possibility)
                    if len(possibilities) == 1:
                        return possibilities
            return possibilities

        if not hasattr(self, 'landmass'):
            raise Exception('Landmass has not been generated')


        width = math.ceil(self.width / resolution)
        height = math.ceil(self.height / resolution)

        random.seed(self.seed)
        self.heatmap = Grid(height, width)
        self.resolution = resolution

        tiles = list()
        for x in range(width):
            for y in range(height):
                tile = self.heatmap[x][y]
                tile.load_adjacent(Map.climates) # 5
                tiles.append(tile)
        random.shuffle(tiles)

        tile = tiles.pop()
        tile.collapse(2)
        self.output.overlay_temperature(tile, self.landmass, resolution)

        while tiles:
            tile = self.heatmap.find_next(tiles)
            possibilities = eliminate_possibilities(tile)
            tile.collapse(random.choice(possibilities))
            self.output.overlay_temperature(tile, self.landmass, resolution)

        self.save_state()

    def soften_heatmap(self):
        """ Softens the heatmap """

        def pick_value(tile):
            """ Returns a new value for the tile """

            def a(n):
                if n == 1:
                    return 1
                return a(n-1) + 8**(n-1)

            frequency = [0 for i in range(Map.climates)]
            for i, layer in enumerate(tile.adjacent):
                for adjacent in layer:
                    value = adjacent.value
                    if value == -1:
                        continue
                    frequency[value] += a(Map.climates-i)

            temperatures = list(range(Map.climates))

            return random.choices(temperatures, frequency)[0]

        if not hasattr(self, 'heatmap'):
            raise Exception('Heatmap has not been generated')

        random.seed(self.seed)
        new_heatmap = Grid(self.height, self.width)

        tiles = list()
        for x in range(self.heatmap.width):
            for y in range(self.heatmap.height):
                value = self.heatmap[x][y].value
                for x_off in range(self.resolution):
                    for y_off in range(self.resolution):
                        x_res_off = x*self.resolution + x_off
                        y_res_off = y*self.resolution + y_off
                        tile = new_heatmap[x_res_off][y_res_off]
                        tile.value = value
                        tiles.append(tile)
                        tile.load_adjacent(Map.climates) # 5
        random.shuffle(tiles)

        while tiles:
            tile = new_heatmap.find_next(tiles)
            tile.collapse(pick_value(tile))
            self.output.overlay_temperature(tile, self.landmass)

        self.resolution = 1
        self.heatmap = new_heatmap
        self.save_state()

    def outline_landmass(self):
        """ Outlines the landmass """

        for x in range(self.width):
            for y in range(self.height):
                tile = self.landmass[x][y]
                if tile.value == Map.water:
                    tile.load_adjacent(1)
                    for adjacent in tile.adjacent[0]:
                        if adjacent.x != tile.x and adjacent.y != tile.y:
                            continue
                        if adjacent.value == Map.land:
                            self.output.plot(tile.pos, (255, 255, 255))
                            break

    def generate_terrain(self):
        """ Generates mountains and lakes on the landmass"""

        pass