class Action:
    can_be_challenged = True
    requires_victim = True
    cost = 0

    def __init__(self, creator, victim=None):
        self.creator = creator
        self.victim = victim
        if self.requires_victim and victim is None:
            raise Exception("Missing victim for action")
        if self.cost > creator.coins:
            raise Exception("Not enough coins to pay for action cost")
        self.creator.coins -= self.cost

    @property
    def can_be_blocked(self):
        return self.blocked_by is not None

    @property
    def blocked_by(self):
        return None

    def resolve(self):
        raise NotImplementedError


class Coup(Action):
    name = "Coup"
    can_be_challenged = False
    cost = 7

    def resolve(self):
        self.victim.loose_life()


class TakeOne(Action):
    name = "Take One"
    can_be_challenged = False
    requires_victim = False

    def resolve(self):
        self.creator.coins += 1


class TakeTwo(Action):
    name = "Take Two"
    can_be_challenged = False
    requires_victim = False

    @property
    def blocked_by(self):
        return BlockTakeTwo

    def resolve(self):
        self.creator.coins += 2


class TakeThree(Action):
    name = "Take Three"
    requires_victim = False

    def resolve(self):
        self.creator.coins += 3


class Steal(Action):
    name = "Steal"

    @property
    def blocked_by(self):
        return BlockSteal

    def resolve(self):
        coins = self.victim.get_robbed()
        self.creator.coins += coins


class ChangeCards(Action):
    name = "Change Cards"
    requires_victim = False

    def resolve(self):
        self.creator.draw_two_and_return_two()


class Assassinate(Action):
    name = "Assassinate"
    cost = 3

    @property
    def blocked_by(self):
        return BlockAssassinate

    def resolve(self):
        self.victim.loose_life()


class BlockAction(Action):
    requires_victim = False

    def resolve(self):
        pass


class BlockTakeTwo(BlockAction):
    name = "Block Take Two"


class BlockAssassinate(BlockAction):
    name = "Block Assassinate"


class BlockSteal(BlockAction):
    name = "Block Steal"

actions = [TakeOne, TakeTwo, TakeThree, Steal, ChangeCards, Assassinate, Coup]
