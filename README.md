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
5. Download the following files to the `data/` directory:
    * Hex Casting:
        * [RegisterPatterns.java](https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java)
        * [GravityApiInterop.java](https://github.com/gamma-delta/HexMod/blob/main/Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity/GravityApiInterop.java)
        * [PekhuiInterop.java](https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/interop/pehkui/PehkuiInterop.java)
        * [en_us.json](https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/resources/assets/hexcasting/lang/en_us.json)
    * Hexal (rename these files, but keep the extensions the same):
        * [RegisterPatterns.java](https://github.com/Talia-12/Hexal/blob/main/Common/src/main/java/ram/talia/hexal/common/casting/RegisterPatterns.java)
        * [en_us.json](https://github.com/Talia-12/Hexal/blob/main/Common/src/main/resources/assets/hexal/lang/en_us.json)
6. Run the bot: `python main.py`
