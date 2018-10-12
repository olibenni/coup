{-# LANGUAGE TypeApplications, AllowAmbiguousTypes, DataKinds, DeriveGeneric,
             DuplicateRecordFields, FlexibleContexts, NoMonomorphismRestriction,
             RankNTypes #-}
module Coup where

import qualified Data.Sequence as Seq
import Data.Sequence hiding (take, splitAt, replicate, zip, filter, length, drop)
import Control.Monad.State.Lazy
import Data.Foldable (toList)

import GHC.Generics
import Test.QuickCheck (shuffle, generate)
import Control.Exception (try, IOException)
import Lens.Micro.Platform
import Data.Generics.Product

data Character = Ambassador | Assassin | Captain
               | Countessa  | Duke
  deriving (Show, Eq, Read)

data Action = BlockForeignAid | BlockSteal  | BlockAssassinate
            | Coup            | Assassinate | ForeignAid
            | Income          | Taxes       | Steal
            | SwapInfluence
  deriving (Show, Eq, Read, Ord, Enum)

action :: Character -> [Action]
action Ambassador = [BlockSteal, SwapInfluence]
action Assassin   = [Assassinate]
action Captain    = [Steal, BlockSteal]
action Duke       = [BlockForeignAid, Taxes]
action Countessa  = [BlockAssassinate]

toBlock :: Action -> Maybe Action
toBlock ForeignAid = Just BlockForeignAid
toBlock Steal = Just BlockSteal
toBlock Assassinate = Just BlockAssassinate
toBlock _ = Nothing

challengeable :: Action -> Bool
challengeable =  flip elem [Taxes, Assassinate, Steal
                           , SwapInfluence, BlockSteal
                           , BlockForeignAid, BlockAssassinate]

hasTarget :: Action -> Bool
hasTarget = flip elem [Coup, Steal, Assassinate]


data Player = Pl { cards :: Either Character (Character, Character)
                 , coins :: Int, color :: Color }
  deriving (Generic, Show)

data Color = Red | Green | Blue | White | Black | Purple
  deriving (Show, Eq, Read, Ord, Enum, Bounded)

data GameState = GSt { players :: Seq Player, deck :: [Character], revealed :: [Character] }
  deriving (Generic, Show)

type Game = StateT GameState IO

isColor :: Color -> Player -> Bool
isColor c = (c ==) . color

currentPlayer :: Lens' GameState Player
currentPlayer = field @"players" . lens (^?! _head) (flip (_head .~))

player :: Color -> Lens' GameState Player
player col = field @"players" . lens get set
  where get s = Seq.filter (isColor col) s ^?! _head
        set s b = case (findIndexL (isColor col) s) of Just i -> update i b s
                                                       _ -> s
nextPlayer :: Game ()
nextPlayer = field @"players" %= shiftl
  where shiftl :: Seq a -> Seq a
        shiftl (x :<| xs) = (xs :|> x)
        shiftl a = a

getChoice :: (Show a, Read a, Eq a, Foldable t, Show (t a)) => String -> t a -> IO (a, [a])
getChoice msg choices =
  do putStrLn msg
     let cs = toList choices
     forM (zip [1..] cs) $ \(n,c) -> putStrLn $ (show n) ++ ". " ++ (show c)
     r <- try @IOException (readLn @Int)
     case r of Right r | (0 < r && r <= (length cs)) ->
                return (cs !! (r - 1), (take (r-1) cs ++ (drop r cs)))
               _ -> do putStrLn "Invalid choice, try again"
                       getChoice msg choices

dropPlayer :: Color -> Game ()
dropPlayer d = field @"players" %= (Seq.filter (not . isColor d))

giveUpInfluence :: Color -> Game ()
giveUpInfluence col =
 do cards <- use (player col . field @"cards")
    case cards of
      Left c -> do field @"revealed" %= (c:)
                   dropPlayer col
      Right cs -> do (c,[other]) <- lift (getChoice "Pick a card to keep " (cs ^.. each))
                     player col . field @"cards" .= Left c
                     field @"revealed" %= (other:)

chooseTwo :: (Show a, Read a, Eq a) => String ->  [a] -> IO ((a,a), [a])
chooseTwo msg opts = do putStrLn msg
                        (c1, r1) <- getChoice "Choose first: " opts
                        (c2, r2) <- getChoice "Choose second: " r1
                        return ((c1,c2), r2)

shuffleDeck :: [a] -> IO [a]
shuffleDeck =  generate . shuffle

payForAction :: Action -> Game ()
payForAction Assassinate = currentPlayer . field @"coins" %= (flip (-) 3)
payForAction Coup        = currentPlayer . field @"coins" %= (flip (-) 7)
payForAction _ = return ()

effect :: Action -> Maybe Color -> Game ()
effect Income _ = currentPlayer . field @"coins" %= (+1)
effect ForeignAid _ = currentPlayer . field @"coins" %= (+2)
effect Coup (Just col) = giveUpInfluence col
effect Taxes _ = currentPlayer . field @"coins" %= (+3)


effect Assassinate (Just col) = giveUpInfluence col
effect Steal (Just col) =
 do cs <- (min 2) <$> use (player col . field @"coins")
    player col . field @"coins" %= (flip (-) cs)
    currentPlayer . field @"coins" %= (+ cs)
effect SwapInfluence _ =
  do (choices, rest) <- splitAt 2 . deck <$> get
     cards <- use (currentPlayer . field @"cards")
     let msg = "Choose card to keep: "
     (nc, r) <- lift $ case cards of Left hc     -> ( _1 %~ Left) <$> getChoice msg (hc:choices)
                                     Right (a,b) -> ( _1 %~ Right) <$> chooseTwo msg (a:b:choices)
     field @"deck" <~ (lift $ shuffleDeck $ r ++ rest)
     currentPlayer . field @"cards" .= nc
effect c Nothing | hasTarget c = error (show c ++ " without target!")
effect _ _ = error "Invalid effect!"

newPlayer :: Color -> (Character, Character) -> Player
newPlayer col chars = Pl {color = col, cards = Right chars, coins = 2}

initialState :: Int -> IO GameState
initialState numPlayers =
  do (playerCards, rest) <- splitAt (2*numPlayers) <$> shuffleDeck initialDeck
     let players = map (uncurry newPlayer) $ zip colors (toPairs playerCards)
     return (GSt { players = fromList players , deck = rest, revealed = []})
  where colors = take numPlayers [Red .. ]
        toPairs (x:y:ys) = (x,y):(toPairs ys)
        toPairs [] = []
        toPairs _ = error "Invalid card split"
        initialDeck = [Ambassador, Assassin, Captain, Countessa, Duke] >>= (replicate 3)

startGame :: IO ()
startGame = do
  (numP, _) <- getChoice "Choose number of players: " [3,4,5,6]
  inSt <- initialState numP
  print inSt
  execStateT gameRound inSt >>= print

otherPlayers :: Game [Color]
otherPlayers = (map color . toList) <$> use (field @"players" . _tail)

allPlayers :: Game [Color]
allPlayers = (map color . toList) <$> use (field @"players")

chooseTarget :: Game Color
chooseTarget = do colors <- otherPlayers
                  (^. _1) <$> (lift . getChoice "Choose a target:") colors

say :: String ->  Game ()
say = lift . putStrLn

endOfRound :: Game ()
endOfRound = do
  st <- get
  lift (print st)
  case (players st) of (p :<| Empty) -> say (show (color p) ++ " wins!")
                       _ -> do nextPlayer
                               gameRound
checkBlocks :: Game (Maybe Color)
checkBlocks = do
  (b, _) <- lift $ getChoice "Is there a block?"  [True, False]
  if b then Just <$> (^. _1)
                 <$> (otherPlayers >>= (\x -> (lift $ getChoice "Choose blocking player:" x)))
       else return Nothing

revealAndReplace :: Character -> Game Character
revealAndReplace c = do
  say $ "Revealed card: " ++ (show c)
  deck <- use (field @"deck")
  field @"deck" <~ (lift $ shuffleDeck $ (c:deck))
  (nc:deck) <- use (field @"deck")
  field @"deck" .= deck
  return nc

replaceCard :: Color -> Action -> Game ()
replaceCard doer act =
  do cards <- use (player doer . field @"cards")
     case cards of
       Left c | elem act (action c) -> cpCards . _Left <~ revealAndReplace c
       Right (a,b) | elem act (action a) -> cpCards . _Right . _1 <~ revealAndReplace a
       Right (a,b) | elem act (action b) -> cpCards . _Right . _2 <~ revealAndReplace b
       Right (a,b) | elem act ((action a) ++ (action b)) ->
         do (c,[d]) <- lift $ getChoice "Choose card to reveal:" [a,b]
            nc <- revealAndReplace c
            cpCards . _Right .= (nc,d)
       _ -> error "Player had invalid cards!"
  where cpCards = player doer . field @"cards"

challenge :: Color -> Action -> Game Bool
challenge doer act =
 if (not (challengeable act)) then return False
 else do
    (c, _) <- lift $ getChoice "Is there a challenge?"  [True, False]
    if c then do
          players <- filter (not . (== doer)) <$> allPlayers
          who <- (^. _1) <$> (lift $ getChoice "Who is challenging?" players)
          actions <- either action ((>>= action) . toList) <$> use (player doer . field @"cards")
          lift (print actions)
          if not (act `elem` actions)
            then do say $ "Challenge successful! " ++ (show doer) ++ " must give up influence."
                    giveUpInfluence doer
                    return True
            else do say $ "Challenge unsuccessful! " ++ (show who) ++ " must give up influence."
                    giveUpInfluence who
                    replaceCard doer act
                    return False
    else return False

gameRound :: Game ()
gameRound = do cp <- use currentPlayer
               say $ "Current Player: " ++ show cp
               act <- if mustCoup cp then say "You must coup." >> return Coup
                      else fst <$> (lift $ getChoice "Choose an action: " $
                                                case cp of p | canCoup p        -> [Coup .. ]
                                                           p | canAssassinate p -> [Assassinate ..]
                                                           _                    -> [ForeignAid ..])
               target <- if hasTarget act
                         then Just <$> chooseTarget
                         else return Nothing
               challengeSuccess <- challenge (color cp) act

               unless challengeSuccess $ do
                 payForAction act
                 let resolves = effect act target
                 case toBlock act of
                   Just blockAction -> do blocker <- checkBlocks
                                          case blocker of
                                            Just someone  -> challenge someone blockAction >>= flip when resolves
                                            Nothing -> resolves
                   Nothing -> resolves
               endOfRound

  where mustCoup p = (coins p) >= 10
        canCoup p = (coins p) >= 7
        canAssassinate p = (coins p) >= 3

main :: IO ()
main = startGame
