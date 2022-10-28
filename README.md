# HexBug
A Discord bot for the Hex Casting mod. `buildpatterns.py`, `revealparser.py`, and `hexast.py` are heavily based on code from [hexdecode](https://github.com/gchpaco/hexdecode) and are licensed separately from the rest of the project.

## Setup
1. Clone this repo, including submodules: `git clone --recurse-submodules <url>`
2. Optionally, set up a venv and enter it
3. Install deps: `pip install -r requirements.txt`
4. Create a file named `.env` following this template:
    ```env
    TOKEN="your-bot-token"
    ```
5. Run the bot: `python main.py`
