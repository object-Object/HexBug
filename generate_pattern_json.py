import json

from hexdecode.buildpatterns import build_registry

# used for my vscode extension
registry = build_registry()
with open("registry.json", "w", encoding="utf-8") as f:
    json.dump(registry.name_to_translation, f)
