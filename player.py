from actions import actions, BlockAction

class Player:
    def __init__(self, game, name, seat):
        self.game = game
        self.name = name
        self.seat = seat
        self.coins = 2
        self.cards = []
        self.draw_cards()

    def draw_cards(self):
        self.cards.append(self.game.deck.draw())
        self.cards.append(self.game.deck.draw())

    def loose_life(self):
        print(self.cards)
        if len(self.cards) > 1:
            selected_card = "0"
            while selected_card not in "12":
                selected_card = input("{}, Select card to discard [1/2]: ".format(self.name))
            self.cards.pop(int(selected_card) - 1)  # Todo: put in graveyard for display
        else:
            self.game.remove_player(self)

    def request_action(self):
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
        selected_player = None
        selectable_players = [player for player in self.game.players if player != self]
        while selected_player not in [player.seat + 1 for player in selectable_players]:
            for player in selectable_players:
                print("[{}] {}".format(player.seat + 1, player.name))
            selected_player = int(input("{}, Select victim: ".format(self.name)))

        return self.game.players[selected_player - 1]

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
        allowed_actions = []
        for card in self.cards:
            if card.action:
                allowed_actions.append(card.action.name)
            if card.block_action:
                allowed_actions.append(card.block_action.name)
        return action.name in allowed_actions

    def get_robbed(self):
        coins = min(max(self.coins, 0), 2)
        self.coins -= coins
        return coins

    def draw_two_and_return_two(self):
        self.draw_cards()
        print(self.cards)
        valid_card_selection = "1234" if len(self.cards) == 4 else "123"
        for i in range(2):
            selected_card = "0"
            while selected_card not in valid_card_selection:
                selected_card = input("{}, Select card to return: ".format(self.name))

            self.game.deck.add(self.cards.pop(int(selected_card) - 1))
            valid_card_selection = valid_card_selection[:-1]

        self.game.deck.shuffle()

    def __str__(self):
        return self.name
