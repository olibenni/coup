from player import Player
from deck import Deck


class Game:
    current_player = None  # Cannot be relied on outside of game scope!
    players = []
    deck = Deck()

    def start(self):
        number_of_players = "0"
        while number_of_players not in "23456":
            number_of_players = input("How many players (2-6): ")

        for i in range(int(number_of_players)):
            name = input("Name for player {}: ".format(i + 1))
            self.players.append(Player(self, name))

        self.current_player = self.players[-1]

    def next_turn(self):
        self.current_player = self.next_player(self.current_player)
        print("======================================================")
        for player in self.players:
            print([player.name, "Coins: {}".format(player.coins)], player.cards)
        print("======================================================")

    @property
    def over(self):
        return len(self.players) == 1

    def next_player(self, player):
        seat = self.players.index(player)
        next_seat = (seat + 1) % len(self.players)
        return self.players[next_seat]

    def previous_player(self, player):
        seat = self.players.index(player)
        next_seat = (seat - 1) % len(self.players)
        return self.players[next_seat]

    def round_of_challenges(self, player, action):
        challenging_player = self.next_player(player)
        while challenging_player is not player:
            if challenging_player.performs_challenge():
                if player.pass_challenge(action):
                    challenging_player.loose_life()
                    player.won_challenge(action)
                    return player  # Failed challenge
                else:
                    player.loose_life()
                    return challenging_player  # Successful challenge

            challenging_player = game.next_player(challenging_player)

        return player  # No challenge made

    def round_of_blocks(self, player, victim, action):
        blocking_player = self.next_player(player)
        while blocking_player is not player:
            if victim is not None and blocking_player is not victim:
                # Only victim can block
                pass
            elif blocking_player.performs_block():
                # If no victim, all can block
                blocking_action = action.blocked_by(blocking_player)
                challenge_winner = game.round_of_challenges(blocking_player, blocking_action)
                if blocking_player is not challenge_winner:
                    return player  # Block failed, player wins

                return blocking_player  # Block successful

            blocking_player = game.next_player(blocking_player)

        return player  # No block made, player wins

    def remove_player(self, player):
        if player in self.players:
            if player is self.current_player:
                self.current_player = self.previous_player(self.current_player)
            self.players.remove(player)
            print("XXX Death of player {} XXX".format(player.name))

if __name__ == "__main__":
    game = Game()
    game.start()
    while not game.over:
        game.next_turn()
        current_player = game.current_player
        selected_victim = None

        selected_action = current_player.request_action()
        if selected_action.requires_victim:
            selected_victim = current_player.select_victim()

        selected_action = selected_action(current_player, selected_victim)

        if selected_action.can_be_challenged:
            challenge_winner = game.round_of_challenges(current_player, selected_action)
            if current_player is not challenge_winner:
                continue  # Action successfully challenged

        if selected_action.can_be_blocked is True:
            block_winner = game.round_of_blocks(current_player, selected_victim, selected_action)
            if current_player is not block_winner:
                continue  # Action successfully blocked

        selected_action.resolve()

    print("Game Over!!, Winner is {}".format(game.players[0]))
