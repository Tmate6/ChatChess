import chess
import chess.pgn
import openai
import threading
import queue

class TimeoutException(Exception):
    pass

# Exception for bad input move
class BadInputMoveError(Exception):
    pass

# Exception for bad bot move
class BadGPTMoveError(Exception):
    pass

class BadMoveError(Exception):
    pass

def printDebug(input, self):
    if self.printDebug:
        print(input)

class Game:
    def __init__(self, apiKey):
        openai.api_key = apiKey
        self.maxTokens = 10
        self.maxFails = 5
        self.maxTime = 5
        self.prompt = {"normal" : "Reply next chess move as {}. Only say the move. {}",
                       "failed" : "Reply next chess move as {}. Play one of these moves: {}. Only say the move. {}",
                       "start" : "Say the first move to play in chess in standard notation"}

        self.board = chess.Board()
        self.fails = 0

        self.move = {"input": {"san": "", "uci": ""}, "ChatGPT": {"san": "", "uci": ""}}
        self.message = ""

        self.printDebug = False

    # Combine handling player move and returning ChatGPT move
    def play(self, move):
        printDebug("play", self)
        if self.board.is_game_over():
            return

        self.handleInputMove(move)
        return self.getGPTMove()

    # Return ChatGPT move including retrying on failed attempts
    def getGPTMove(self):
        printDebug("getGPTMove", self)
        if self.board.is_game_over():
            return

        for i in range(5):
            try:
                return self.handleGPTMove(self.askGPT(self.createPrompt()))
            except TimeoutException:
                self.fails += 1
                printDebug("TimeoutException", self)
            except BadGPTMoveError:
                self.fails += 1
                printDebug("BadGPTMoveError", self)
            except BadInputMoveError:
                printDebug("BadInputMoveError", self)

        self.message = f"Move fail limit reached ({self.fails})"
        return

    ## ChatGPT querying
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
        def askGPTThread(q, maxTokens, currPrompt):
            q.put(openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    max_tokens=maxTokens,
                    messages=[{"role": "system", "content": currPrompt}]
                ).choices[0]["message"]["content"])

        # Create thread to timeout if takes too long
        q = queue.Queue()
        thread = threading.Thread(target=askGPTThread, args=(q, self.maxTokens, currPrompt))
        thread.start()
        thread.join(self.maxTime)

        if thread.is_alive():
            raise TimeoutException
        else:
            return q.get()

    ## Move handling
    def handleResponse(self, response, player):
        move = response
        # capitelize peice
        if len(move) > 2:
            move = move[0].capitalize() + move[1:]

        # try simply
        try:
            self.move[player]["uci"] = self.board.parse_san(move)
            self.move[player]["san"] = move
            self.board.push_san(move)
            self.message = f"Move normal: {move} Player: {player} Fails: {self.fails}"
            return move
        except:
            pass

        # try making first move lowercase (pawn move)
        try:
            modMove = move[0].lower() + move[1:]
            self.move[player]["uci"] = self.board.parse_san(modMove)
            self.move[player]["san"] = modMove
            self.board.push_san(modMove)
            self.message = f"Move lower: {move} Player: {player} Fails: {self.fails}"
            return move[0].lower() + move[1:]
        except:
            pass

        # try to scan whole string for a move
        move = response
        for chars in range(len(move), 0, -1):
            for i in range(len(move)):
                try:
                    self.move[player]["uci"] = self.board.parse_san(move[i:i + chars])
                    self.move[player]["san"] = move[i:i + chars]
                    self.board.push_san(move[i:i + chars])
                    self.message = f"Move scan: {move[i:i + chars]} Player: {player} Fails: {self.fails}"
                    return move[i:i + chars]
                except:
                    pass

        raise BadMoveError("The given move can't be played")

    # Handle move returned from ChatGPT
    def handleGPTMove(self, completion):
        printDebug("handleGPTResponse", self)

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

        try:
            self.handleResponse(move, "ChatGPT")
            self.fails = 0
        except BadMoveError:
            raise BadGPTMoveError("The move ChatGPT gave can't be played")

    # Handle inputted move
    def handleInputMove(self, move):
        try:
            self.handleResponse(move, "input")
            self.fails = 0
        except BadMoveError:
            raise BadInputMoveError("The move inputted can't be played")
