from actions import *


class Card:
    def __repr__(self):
        return self.__class__.__name__


class Duke(Card):
    action = TakeThree
    block_action = BlockTakeTwo


class Assassin(Card):
    action = Assassinate
    block_action = None


class Captain(Card):
    action = Steal
    block_action = BlockSteal


class Contessa(Card):
    action = None
    block_action = BlockAssassinate


class Ambassador(Card):
    action = ChangeCards
    block_action = BlockSteal
