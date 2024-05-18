# Trivia-King

Trivia-King is a client-server application that implements a fast-paced trivia contest. Players receive random facts that are either true or false and must answer correctly as quickly as possible. The game ends as soon as a player provides the correct answer.

## How to Play:

1. **Start the Client and Server:**
    - Start both the client and server (the order doesn't matter).
2. **Wait for Connection**
3. **Player Connection:**
    - After a player connects, the game will wait 10 seconds before starting. If a new player connects, the timer resets.
4. **Gameplay:**
    - The server sends a question to each client and waits for answers.
    - Possible answers are:
        - For true: **TY1ty**
        - For false: **FN0fn**
    - If a client answers correctly, the game ends.
    - If no one answers correctly, the server moves to the next question.
    - If 10 seconds pass without a correct answer, the server moves to the next question.
5. **End of Game:**
    - Clients will be notified about the winner and provided with some game statistics.

## Key Features

* If a server crashes mid-game, the clients will know and return to a state of looking for a server - they won't crash.
* If a client is disconnected mid-game, the server will remove them from its list of clients and continue the game with the rest.
* If the last client disconnects from the server, the game will be stopped and the server will go back to the state of waiting for clients.
* The server dynamically finds a free port to use.
* You can run multiple servers and clients simultaneously from this code.

## How to Install:

1. **Clone the Repository:**
    ```sh
    git clone https://github.com/manuelruff/Trivia-King.git
    ```
2. **Install Dependencies:**
    ```sh
    pip install keyboard
    ```
