# HexBug

A Discord bot for the Hex Casting mod. `buildpatterns.py`, `revealparser.py`, and `hexast.py` are heavily based on code from [hexdecode](https://github.com/gchpaco/hexdecode) and are licensed separately from the rest of the project. **Minimum Python version: 3.11.0**.

## Setup

1. Clone this repo, including submodules: `git clone --recurse-submodules <url>`
2. Set up a venv using Python 3.11 and enter it
3. [Install Rust](https://www.rust-lang.org/tools/install) (for building `hexnumgen` in the next step)
4. Install deps: `pip install -e '.[dev]' --find-links ./vendor`
   * If the above command fails with a message related to `hexnumgen`, try this one instead: `pip install -e '.[dev,target-any]' --find-links ./vendor`
6. Create a file named `.env` following this template:

    ```env
    BOT_ID="12345678"
    HEALTH_CHECK_CHANNEL_ID="12345678"
    TOKEN="your-bot-token"
    LOG_WEBHOOK_URL="https://discord.com/api/webhooks/id/token"
    HEALTH_CHECK_WEBHOOK_URL="https://discord.com/api/webhooks/id/token"
    ```

7. Run the bot: `python main.py`

## Scraping web book types

Run `nox -s scrape_book_types`.

## Depending on HexBug

Note: I haven't tested these steps very thoroughly, so YMMV. Open an issue or ping me on Discord if something's broken.

1. Clone this repo somewhere, including submodules: `git clone --recurse-submodules <url>`
2. In your project, run `pip install 'path/to/HexBug[scripts]'`
3. Import from `HexBug`, eg. `from HexBug.utils.generate_image import draw_single_pattern`

Alternatively, if you don't need anything which depends on the mod submodules, you *should* be able to install directly from Git:
`pip install git+https://github.com/object-Object/HexBug.git`
