# ChatChess
A simple python package to play chess with ChatGPT

## Installation

```python
pip install chatchess
```

## Usage

Import the package:
```python
from ChatChess import ChatChess
```

First a `Game` object needs to be decalerd as follows:
```python
bot = ChatChess.Game("OPENAI_API_KEY")
```

### Additional parameters:

- `bot.maxTokens = 10`: Set max_tokens passed to ChatGPT on each move
- `bot.maxFails = 5`: Amount of times to retry sending prompt to ChatGPT when invalid move is returned
- `bot.prompt = {"normal" : "", "failed" : "", "start" : ""}`: The prompts to send to ChatGPt at each game state
- `bot.board = chess.Board()`: Chess board object
- `bot.message = ""`: Set to move into after each GPT move
- `bot.printDebug = False`: Print debug info - occaisonaly useful

### Functions

**Main functions**

- `move = bot.play("e4")`: Plays the player's move, then ChatGPT's response - returns ChatGPT's move
- `move = getGPTMove()`: Plays ChatGPT's move in the current position - returns ChatGPT's move

**Other functions**

- `bot.pushPlayerMove("e4")`: Push a move without ChatGPT responding
- `prompt = bot.createPrompt()`: Creates prompt to send to ChatGPT based on current position and previous fails - returns prompt
- `response = bot.askGPT(prompt)`: Queries ChatGPT prompt based on set parameters
- `move = bot.handleResponse(response)`: Gets move from reponse - returns move

## Examples

### Simple player vs ChatGPT game
```python
from ChatChess import ChatChess

bot = ChatChess.Game("OPENAI_API_KEY")  # Set API key

while True:
  print(bot.board())  # Print the board
  bot.play(input("Make a move: "))  # Ask player to make a move, then ChatGPT responds
  if bot.board.is_game_over():  # Break if game over
    break
```

### Simple ChatGPT vs ChatGPT game from a set position
```python
import chess
import chess.fen
from ChatChess import ChatChess

bot = ChatChess.Game("OPENAI_API_KEY")  # Set API key
bot.board = chess.Board("rnbq1bnr/ppppkppp/8/4p3/4P3/8/PPPPKPPP/RNBQ1BNR w - - 2 3")  # Set position

while True:
  bot.getGPTMove()  # Ask ChatGPT to make a move
  print(bot.message)  # Print move and info
  if bot.board.is_game_over():  # Break if game over
    print(str(chess.pgn.Game.from_board(bot.board)))
    break
```

## Info
### Uses
- python-chess - https://github.com/niklasf/python-chess
- openai-python - https://github.com/openai/openai-python
