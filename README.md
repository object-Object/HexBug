# HexBug

A Discord bot for the Hex Casting mod. `buildpatterns.py`, `revealparser.py`, and `hexast.py` are heavily based on code from [hexdecode](https://github.com/gchpaco/hexdecode) and are licensed separately from the rest of the project. **Minimum Python version: 3.11.0**.

## Setup

1. Clone this repo, including submodules: `git clone --recurse-submodules <url>`
2. Set up a venv using Python 3.11 and enter it
3. [Install Rust](https://www.rust-lang.org/tools/install) (for building `hexnumgen` in the next step)
4. Install deps: `pip install -r requirements.txt`
5. Create a file named `.env` following this template:

    ```env
    TOKEN="your-bot-token"
    LOG_WEBHOOK_URL="https://discord.com/api/webhooks/id/token"
    ```

6. Run the bot: `python main.py`

## Scraping web book types

Run `python scrape_book_types.py | tee utils/book_types.py && python -m black utils/book_types.py`.
