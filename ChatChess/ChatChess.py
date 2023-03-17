import chess
import chess.pgn
import openai

# Exception for bad player move
class badPlayerMoveError(Exception):
    pass

# Exception for bad bot move
class badGPTMoveError(Exception):
    pass

def printDebug(input, self):
    if self.printDebug:
        print(input)

class Game:
    def __init__(self, apiKey):
        openai.api_key = apiKey
        self.maxTokens = 10
        self.maxFails = 5
        self.prompt = {"normal" : "Reply next chess move as {}. Only say the move. {}",
                       "failed" : "Reply next chess move as {}. Play one of these moves: {}. Only say the move. {}",
                       "start" : "Say the first move to play in chess in standard notation"}

        self.board = chess.Board()
        self.fails = 0
        self.message = ""

        self.printDebug = False

    ## Chess-related

    ## Player/GPT-related

    # Combine pushing player move and returning GPT move
    def play(self, move):
        printDebug("play", self)
        if self.board.is_game_over():
            return

        self.pushPlayerMove(move)
        return self.getGPTMove()

    # Push move made by player
    def pushPlayerMove(self, move):
        try:
            self.board.push_san(move)
            return
        except:
            pass

        try:
            self.board.push(move)
            return
        except:
            pass

        try:
            capitalizeMove = move[0].capitalize() + move[1:]
            self.board.push_san(capitalizeMove)
            return
        except:
            pass

        raise badPlayerMoveError("The move inputted can't be played")

    # Return GPT move including retrying on failed attempts
    def getGPTMove(self):
        printDebug("getGPTMove", self)
        if self.board.is_game_over():
            return

        for i in range(5):
            try:
                return self.handleResponse(self.askGPT(self.createPrompt()))
            except badGPTMoveError:
                pass

        self.message = f"Move fail limit reached ({self.fails})"
        return

    # Create prompt based on current position
    def createPrompt(self):
        printDebug("createPrompt", self)
        if self.board.turn == chess.WHITE:
            color = "white"
        else:
            color = "black"

        if self.board.board_fen() == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
            currPrompt = self.prompt["start"]
        elif not self.fails == 0:
            currPrompt = self.prompt["failed"].format(color, str(self.board.legal_moves)[36:-1], str(chess.pgn.Game.from_board(self.board))[93:-2])
        else:
            currPrompt = self.prompt["normal"].format(color, str(chess.pgn.Game.from_board(self.board))[93:-2])
        printDebug(currPrompt, self)
        return currPrompt

    # Ask ChatGPT for the move
    def askGPT(self, currPrompt) -> str:
        printDebug("askGPT", self)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=self.maxTokens,
            messages=[{"role": "system", "content": currPrompt}]
        )
        return response.choices[0]["message"]["content"]

    # Handle move returned from ChatGPT
    def handleResponse(self, completion):
        printDebug("handleCompletion", self)
        # erase special characters
        move = completion.replace("\n", "").replace(".", "").replace(" ", "")

        # erase ints at beggining of reply
        for i in range(len(move)):
            try:
                placeholder = int(move[i])
            except:
                move = move[i:]
                break

        printDebug(move, self)

        # capitelize peice
        if len(move) > 2:
            move = move[0].capitalize() + move[1:]

        # try simply
        try:
            self.board.push_san(move)
            self.message = f"Move normal: {move} Fails: {self.fails}"
            self.fails = 0
            return move
        except:
            pass

        # try making first move lowercase (pawn move)
        try:
            ModMove = move[0].lower() + move[1:]
            self.board.push_san(ModMove)
            self.message = f"Move lower: {move} Fails: {self.fails}"
            self.fails = 0
            return move[0].lower() + move[1:]
        except:
            pass

        # try to scan whole string for a move
        move = completion
        for chars in range(len(move), 0, -1):
            for i in range(len(move)):
                try:
                    self.board.push_san(move[i:i + chars])
                    self.message = f"Move scan: {move[i:i + chars]} Fails: {self.fails}"
                    self.fails = 0
                    return move[i:i + chars]
                except:
                    pass

        self.fails += 1
        raise badGPTMoveError("The move ChatGPT gave can't be played")
