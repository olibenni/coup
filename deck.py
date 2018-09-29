import random
from card import Duke, Assassin, Captain, Contessa, Ambassador


class Deck:
    cards = []

    def __init__(self):
        self.cards = [Duke(), Assassin(), Captain(), Contessa(), Ambassador()] * 3
        self.shuffle()

    def draw(self):
        return self.cards.pop()

    def add(self, card):
        self.cards.append(card)

    def shuffle(self):
        random.shuffle(self.cards)


class GraveYard:
    cards = []

    def add(self, card):
        self.cards.append(card)
