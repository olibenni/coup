from actions import actions, Coup


class Player:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.coins = 2
        self.cards = []
        self.draw_cards()

    def draw_cards(self):
        self.draw_card()
        self.draw_card()

    def draw_card(self):
        self.cards.append(self.game.deck.draw())

    def loose_life(self):
        print(self.cards)
        if len(self.cards) > 1:
            selected_card = "0"
            while selected_card not in "12":
                selected_card = input("{}, Select card to discard [1/2]: ".format(self.name))
            self.cards.pop(int(selected_card) - 1)  # Todo: put in graveyard for display
        elif len(self.cards) == 1:
            self.game.remove_player(self)

    def request_action(self):
        if self.coins >= 10:
            print("{} you must perform a coup since you have 10 or more coins".format(self.name))
            return Coup

        print("{}, select action".format(self.name))
        for i, action in enumerate(actions):
            if action.cost <= self.coins:
                print("[{}] {}".format(i + 1, action.name))
            else:
                print("[{}] {}. NOT ENOUGH COINS".format(i + 1, action.name))

        while True:
            selection = input("Action #: ")
            if selection not in "1234567":
                print("Invalid selection")
                continue

            action = actions[int(selection) - 1]
            if action.cost > self.coins:
                print("You cannot perform {}. Coins needed {}".format(action.name, action.cost))
                continue

            return action

    def select_victim(self):
        selected_player = "0"
        selectable_players = [player for player in self.game.players if player != self]
        while selected_player not in "".join([str(i + 1) for i in range(len(selectable_players))]):
            for i, player in enumerate(selectable_players):
                print("[{}] {}".format(i + 1, player.name))
            selected_player = input("{}, Select victim: ".format(self.name))

        return selectable_players[int(selected_player) - 1]

    def performs_challenge(self):
        res = None
        while res not in ["y", "n"]:
            res = input("{} do you challenge? [y/N]: ".format(self.name)) or "n"

        return res == "y"

    def performs_block(self):
        res = None
        while res not in ["y", "n"]:
            res = input("{} do you block? [y/N]: ".format(self.name)) or "n"

        return res == "y"

    def pass_challenge(self, action):
        return self._get_card_for_action(action) is not None

    def get_robbed(self):
        coins = min(max(self.coins, 0), 2)
        self.coins -= coins
        return coins

    def draw_two_and_return_two(self):
        self.draw_cards()
        valid_card_selection = "1234" if len(self.cards) == 4 else "123"
        for i in range(2):
            print(self.cards)
            selected_card = "0"
            while selected_card not in valid_card_selection:
                selected_card = input("{}, Select card to return: ".format(self.name))

            self.game.deck.add(self.cards.pop(int(selected_card) - 1))
            valid_card_selection = valid_card_selection[:-1]

        self.game.deck.shuffle()

    def won_challenge(self, action):
        card = self._get_card_for_action(action)
        self.game.deck.add(card)
        self.cards.remove(card)
        self.game.deck.shuffle()
        self.draw_card()

    def _get_card_for_action(self, action):
        for card in self.cards:
            if card.action and card.action.name == action.name:
                return card
            if card.block_action and card.block_action.name == action.name:
                return card

    def __str__(self):
        return self.name
