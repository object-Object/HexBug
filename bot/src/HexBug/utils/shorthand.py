from hexdoc.core import ResourceLocation

SUFFIXES = {
    " reflection": ["", " ref", " refl"],
    " purification": ["", " pur", " prfn", " prf"],
    " distillation": ["", " dist", " distill"],
    " exaltation": ["", " ex", " exalt"],
    " decomposition": ["", " dec", " decomp"],
    " disintegration": ["", " dis", " disint"],
    " gambit": ["", " gam"],
}

FORBIDDEN_NAMES = {
    stripped
    for old_value, new_values in SUFFIXES.items()
    for name in [old_value] + new_values
    if (stripped := name.strip())
}

REPLACEMENTS = [
    SUFFIXES,
    {"vector ": ["vec "]},
    {
        "'s": ["", "s"],
        "s'": ["", "s"],
    },
    {":": [""]},
    {"ii": ["2"]},
]


# this is genuinely cursed, but it still works
def get_shorthand_names(id: ResourceLocation, name: str):
    yield str(id).lower()
    yield id.path.lower()

    names = [name.lower()]
    yield name.lower()

    for replacements in REPLACEMENTS:
        for name in names:
            for old_value, new_values in replacements.items():
                if old_value in name:
                    for new_value in new_values:
                        new_name = name.replace(old_value, new_value).strip()
                        names.append(new_name)
                        if new_name not in FORBIDDEN_NAMES:
                            yield new_name
