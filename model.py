import random


class Model():
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def generate_level(self):
        level = [[-1 for x in range(self.width)] for y in range(self.height)]

        places = []
        for y in range(self.height):
            for x in range(self.width):
                places.append((x, y))
        random.shuffle(places)

        card_index = 0
        while len(places) >= 2:
            (x, y) = places.pop(0)
            level[y][x] = card_index
            (x, y) = places.pop(0)
            level[y][x] = card_index

            card_index += 1

        return level
