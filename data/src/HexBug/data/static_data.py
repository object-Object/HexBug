from typing import Any

from hexdoc.core import ResourceLocation
from yarl import URL

from .hex_math import HexDir
from .mods import Modloader, StaticModInfo
from .patterns import StaticPatternInfo
from .special_handlers import (
    ComplexHexLongSpecialHandler,
    HexFlowNumberSpecialHandler,
    HexTraceSpecialHandler,
    MaskSpecialHandler,
    NumberSpecialHandler,
    OverevaluateTailDepthSpecialHandler,
    SpecialHandler,
)
from .utils.collections import ResourceSet

MODS: list[StaticModInfo] = [
    StaticModInfo(
        id="hexcasting",
        name="Hex Casting",
        description="A mod for Forge and Fabric adding stack-based programmable spellcasting, inspired by Psi.",
        icon_url=URL("Common/src/main/resources/logo.png"),
        curseforge_slug="hexcasting",
        modrinth_slug="hex-casting",
        modloaders=[
            Modloader.FABRIC,
            Modloader.FORGE,
            Modloader.NEOFORGE,
            Modloader.QUILT,
        ],
    ),
    StaticModInfo(
        id="caduceus",
        name="Caduceus",
        description="A Clojure-based addon for advanced meta-evaluation related to jump iotas.",
        # permalink because caduceus hasn't released its new icon yet
        icon_url=URL(
            "https://raw.githubusercontent.com/object-Object/Caduceus/4bdfeada6ebc2448b66c7b861accdea864afb4f3/common/src/main/resources/assets/caduceus/icon.png"
        ),
        curseforge_slug="caduceus",
        modrinth_slug="caduceus",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="complexhex",
        name="Complex Hex",
        description="Adds complex numbers, quaternions, BIT displays, and bubbles.",
        icon_url=URL("common/src/main/resources/icon.png"),
        curseforge_slug=None,
        modrinth_slug="complex-hex",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="dthexcasting",
        name="Dynamic Trees - Hexcasting",
        description="Makes Hex Casting compatible with Dynamic Trees, adding dynamically growing versions of the all edified trees.",
        icon_url=URL(
            "https://media.forgecdn.net/avatars/thumbnails/1185/235/64/64/638759222267068311.png"
        ),
        curseforge_slug="dynamic-trees-hexcasting",
        modrinth_slug="dynamic-trees-hexcasting",
        modloaders=[Modloader.FORGE],
    ),
    StaticModInfo(
        id="efhexs",
        name="Special Efhexs",
        description="An addon dedicated to special effects via particles and sounds.",
        icon_url=URL("src/main/resources/assets/efhexs/icon.png"),
        curseforge_slug=None,
        modrinth_slug=None,
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="ephemera",
        name="Ephemera",
        description="An addon for Hex Casting with no particular theme.",
        icon_url=URL("fabric/src/main/resources/icon.png"),
        curseforge_slug="ephemera",
        modrinth_slug="ephemera",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hex_ars_link",
        name="Hex-Ars Linker",
        description="Link Ars Nouveau mana to Hex Casting media & cast Ars Nouveau spells inside Hex Casting.",
        icon_url=URL("common/src/main/resources/cover.png"),
        curseforge_slug="hex-ars-linker",
        modrinth_slug="hex-ars-linker",
        modloaders=[Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexal",
        name="Hexal",
        description="Adds many utility patterns/spells (eg. entity health, item smelting), autonomous casting with wisps, and powerful item manipulation/storage.",
        icon_url=URL("Common/src/main/resources/logo.png"),
        curseforge_slug="hexal",
        modrinth_slug="hexal",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexcassettes",
        name="Hexcassettes",
        description="Adds a method to delay hexes into the future, with a touch of playfulness and whimsy!",
        icon_url=URL("src/main/resources/assets/hexcassettes/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hexcassettes",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexcellular",
        name="Hexcellular",
        description="Adds property iota to Hexcasting for easy syncing, storage, and communication of iota.",
        icon_url=URL("src/main/resources/assets/hexcellular/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hexcellular",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexchanting",
        name="Hexchanting",
        description="Imbue your equipment with the power of Hex Casting.",
        icon_url=URL("src/main/resources/assets/hexchanting/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hexchanting",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hexdebug",
        name="HexDebug",
        description="Adds items and patterns to allow debugging hexes in VSCode, and a block to make editing hexes ingame much easier.",
        icon_url=URL("Common/src/main/resources/icon.png"),
        curseforge_slug="hexdebug",
        modrinth_slug="hexdebug",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexdim",
        name="Hexxy Dimensions",
        description="Adds pocket dimensions.",
        icon_url=URL("doc/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hexdim",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hexflow",
        name="HexFlow",
        description="Adds several new patterns for better control of spell executions.",
        icon_url=URL("common/src/main/resources/logo.png"),
        curseforge_slug="hexflow",
        modrinth_slug="hexflow",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexgender",
        name="HexGender",
        description="Adds patterns for changing your gender via Wildfire's Female Gender Mod.",
        icon_url=URL(
            "https://media.forgecdn.net/avatars/1184/151/638757987531288199.webp"
        ),
        curseforge_slug="hexgender",
        modrinth_slug="hexgender",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexic",
        name="Hexic",
        description="Miscellaneous neat features and QoL patterns for Hex Casting.",
        icon_url=URL("src/main/resources/assets/hexic/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hexic",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexical",
        name="Hexical",
        description="A fun addon containing genie lamps, mage blocks, specks, world scrying, and more!",
        icon_url=URL("src/main/resources/assets/hexical/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hexical",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexmapping",
        name="HexMapping",
        description="Adds patterns to put markers on various web maps.",
        icon_url=URL(
            "https://media.forgecdn.net/avatars/thumbnails/1183/716/64/64/638757456658646386.png"
        ),
        curseforge_slug="hexmapping",
        modrinth_slug="hexmapping",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexodus",
        name="Hexodus",
        description="A gravity addon for Hex Casting.",
        icon_url=URL("src/main/resources/assets/hexodus/icon.png"),
        curseforge_slug=None,
        modrinth_slug=None,
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hexoverpowered",
        name="HexOverpowered",
        description="Adds some OP stuff for Hex Casting.",
        icon_url=URL("common/src/main/resources/logo.png"),
        curseforge_slug="hexoverpowered",
        modrinth_slug="hexoverpowered",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexparse",
        name="HexParse",
        description="Provides a pair of patterns and a set of commands to convert custom code into a list iota.",
        icon_url=URL("common/src/main/resources/logo.png"),
        curseforge_slug="hexparse",
        modrinth_slug="hexparse",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexpose",
        name="Hexpose",
        description="A library addon for Hexcasting that adds many scrying patterns and the iotas for other addons to use.",
        icon_url=URL("src/main/resources/assets/hexpose/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hexpose",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hexstruction",
        name="HexStruction",
        description="Adds the ability to create, manipulate, and use Structure iotas.",
        icon_url=URL("common/src/main/resources/assets/hexstruction/icon.png"),
        curseforge_slug="hexstruction",
        modrinth_slug="hexstruction",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hextended",
        name="Hextended Staves",
        description="Bolster your magic stick collection.",
        icon_url=URL("common/src/main/icon.png"),
        curseforge_slug="hextended-staves",
        modrinth_slug="hextended-staves",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hextrace",
        name="Hex Trace",
        description="Allows adding tracers to iotas to help with debugging.",
        icon_url=None,
        curseforge_slug=None,
        modrinth_slug=None,
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hextrogen",
        name="Hextrogen",
        description="Adds interop with Create: Estrogen.",
        icon_url=URL("src/main/resources/assets/hextrogen/icon.png"),
        curseforge_slug=None,
        modrinth_slug="hextrogen",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hextweaks",
        name="HexTweaks",
        description="Adds grand spells, rituals, and turtle casting.",
        icon_url=URL(
            "https://cdn.modrinth.com/data/pim6pG9O/0f36451e826a46c00d337d7ef65e62c87bc40eba.png"
        ),
        curseforge_slug=None,
        modrinth_slug="hextweaks",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexweb",
        name="HexWeb",
        description="Adds patterns for making HTTP requests via OkHTTP, as well as creating and manipulating JSON objects.",
        icon_url=URL(
            "https://media.forgecdn.net/avatars/thumbnails/1184/119/64/64/638757930272038947.png"
        ),
        curseforge_slug="hexweb",
        modrinth_slug="hexweb",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hierophantics",
        name="Hierophantics",
        description="Addon for Hex Casting that lets you work with extracted minds to create conditional hexes, merge villagers, and cast spells for less media.",
        icon_url=URL("common/src/main/resources/assets/hierophantics/icon.png"),
        curseforge_slug="hierophantics",
        modrinth_slug="hierophantics",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="ioticblocks",
        name="IoticBlocks",
        description="Adds patterns for reading and writing iotas to/from blocks, and an API for addon developers to easily add iota reading/writing support to their blocks.",
        icon_url=URL("common/src/main/resources/assets/ioticblocks/icon.png"),
        curseforge_slug="ioticblocks",
        modrinth_slug="ioticblocks",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="lapisworks",
        name="Lapisworks",
        description="Harness Lapis' enchanting power with Hex Casting's media and enchant yourself.",
        icon_url=URL("src/main/resources/assets/lapisworks/icon.png"),
        curseforge_slug=None,
        modrinth_slug="lapisworks",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="lessertp",
        name="Lesser Teleport",
        description="A port of Lesser Teleport from HexKinetics.",
        icon_url=URL("src/main/resources/assets/lessertp/icon.png"),
        curseforge_slug=None,
        modrinth_slug="lesser-teleport",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="mediatransport",
        name="mediatransport",
        description="Figura integration for Hex Casting.",
        icon_url=URL("common/src/main/resources/assets/mediatransport/icon.png"),
        curseforge_slug=None,
        modrinth_slug="mediatransport",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="moreiotas",
        name="MoreIotas",
        description="Adds iotas for strings, matrices, types, and items.",
        icon_url=URL("Common/src/main/resources/logo.png"),
        curseforge_slug="moreiotas",
        modrinth_slug="moreiotas",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="oneironaut",
        name="Oneironaut",
        description="An addon for Hex Casting centered around exploration and use of the Noosphere.",
        icon_url=URL("fabric/src/main/resources/icon.png"),
        curseforge_slug="oneironaut",
        modrinth_slug="oneironaut",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="overevaluate",
        name="Overevaluate",
        description="Adds sets and patterns for advanced metaevals and stack manipulation.",
        icon_url=URL("src/main/resources/assets/overevaluate/icon.png"),
        curseforge_slug=None,
        modrinth_slug=None,
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="scryglass",
        name="Scryglass",
        description="A Hexcasting addon to draw things on your screen!",
        icon_url=None,
        curseforge_slug=None,
        modrinth_slug=None,
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="slate_work",
        name="Slate Works",
        description="An addon for improving and adding to Spell Circles in many different ways.",
        icon_url=URL("src/main/resources/assets/slate_work/icon.png"),
        curseforge_slug=None,
        modrinth_slug="slate-works",
        modloaders=[Modloader.FABRIC],
    ),
]
"""The master list of mods supported by HexBug.

Hex Casting is guaranteed to be the first mod in this list. All other mods are sorted
alphabetically by name.
"""
MODS[1:] = sorted(MODS[1:], key=lambda m: m.name)
assert MODS[0].id == "hexcasting"

CONSIDERATION = ResourceLocation("hexcasting", "escape")
INTROSPECTION = ResourceLocation("hexcasting", "open_paren")
RETROSPECTION = ResourceLocation("hexcasting", "close_paren")
EVANITION = ResourceLocation("hexcasting", "undo")

EXTRA_PATTERNS: list[StaticPatternInfo] = [
    StaticPatternInfo(
        id=CONSIDERATION,
        startdir=HexDir.WEST,
        signature="qqqaw",
    ),
    StaticPatternInfo(
        id=INTROSPECTION,
        startdir=HexDir.WEST,
        signature="qqq",
    ),
    StaticPatternInfo(
        id=RETROSPECTION,
        startdir=HexDir.EAST,
        signature="eee",
    ),
    StaticPatternInfo(
        id=EVANITION,
        startdir=HexDir.EAST,
        signature="eeedw",
    ),
]

SPECIAL_HANDLERS: dict[ResourceLocation, SpecialHandler[Any]] = {
    handler.id: handler
    for handler in [
        NumberSpecialHandler(
            id=ResourceLocation("hexcasting", "number"),
        ),
        MaskSpecialHandler(
            id=ResourceLocation("hexcasting", "mask"),
        ),
        OverevaluateTailDepthSpecialHandler(
            id=ResourceLocation("overevaluate", "nephthys"),
            direction=HexDir.SOUTH_EAST,
            prefix="deaqqd",
            initial_depth=1,
            tail_chars="qe",
        ),
        OverevaluateTailDepthSpecialHandler(
            id=ResourceLocation("overevaluate", "sekhmet"),
            direction=HexDir.SOUTH_WEST,
            prefix="qaqdd",
            initial_depth=0,
            tail_chars="qe",
        ),
        OverevaluateTailDepthSpecialHandler(
            id=ResourceLocation("overevaluate", "geb"),
            direction=HexDir.WEST,
            prefix="aaeaad",
            initial_depth=1,
            tail_chars="w",
        ),
        OverevaluateTailDepthSpecialHandler(
            id=ResourceLocation("overevaluate", "nut"),
            direction=HexDir.EAST,
            prefix="aawdde",
            initial_depth=1,
            tail_chars="w",
        ),
        ComplexHexLongSpecialHandler(
            id=ResourceLocation("complexhex", "long"),
        ),
        HexFlowNumberSpecialHandler(
            id=ResourceLocation("hexflow", "noob_num"),
        ),
        HexTraceSpecialHandler(
            id=ResourceLocation("hextrace", "trace"),
        ),
    ]
}

# don't try to load these
DISABLED_PATTERNS: set[ResourceLocation] = {
    # conflicts
    ResourceLocation("hexstruction", "bounding_box"),  # shape: hexical:greater_blink
    ResourceLocation("lapisworks", "empty_prfn"),  # signature: hexal:mote/storage/get
    # unreasonably long angle signature
    ResourceLocation("hexic", "whatthefuck"),
    # not real patterns
    ResourceLocation("hexcasting", "const/vec/x"),
    ResourceLocation("hexcasting", "const/vec/y"),
    ResourceLocation("hexcasting", "const/vec/z"),
}

# load these, but suppress the warning if we can't find any operators
UNDOCUMENTED_PATTERNS = ResourceSet(
    values=[
        # unused
        ResourceLocation("moreiotas", "altadd"),
        # undocumented
        ResourceLocation("complexhex", "chloe/copy"),
        ResourceLocation("complexhex", "chloe/make"),
        ResourceLocation("complexhex", "cnarg"),
        ResourceLocation("ephemera", "hashbits"),
        ResourceLocation("hexic", "dye_offhand"),
        ResourceLocation("hexic", "spellmind/restore"),
        ResourceLocation("hexic", "spellmind/save"),
        ResourceLocation("hexic", "tripwire"),
        ResourceLocation("hexical", "disguise_mage_block"),
        ResourceLocation("hexical", "tweak_mage_block"),
        ResourceLocation("hexpose", "entity_name"),
        ResourceLocation("hextweaks", "you_like_drinking_potions"),
        ResourceLocation("lapisworks", "empty_prfn"),
        ResourceLocation("lapisworks", "writable_offhand"),
        ResourceLocation("oneironaut", "advanceautomaton"),
        ResourceLocation("oneironaut", "checksignature"),
        ResourceLocation("oneironaut", "erosionshield"),
        ResourceLocation("oneironaut", "getsoulprint"),
        ResourceLocation("oneironaut", "signitem"),
        # lmao what
        ResourceLocation("ephemera", "no"),
        ResourceLocation("hexic", "free"),
        ResourceLocation("hexic", "malloc"),
        ResourceLocation("hextweaks", "suicide"),
        ResourceLocation("oneironaut", "circle"),
    ],
    patterns=[
        # undocumented
        ResourceLocation("hexic", "prop_*"),
        # lmao what
        ResourceLocation("hexic", "jvm/*"),
        ResourceLocation("hexic", "nbt/*"),
    ],
)

# suppress warnings for these special handler conflicts
# (special handler, conflicting pattern, conflicting value)
SPECIAL_HANDLER_CONFLICTS: set[tuple[ResourceLocation, ResourceLocation, Any]] = {
    (
        ResourceLocation("complexhex", "long"),
        ResourceLocation("hexal", "mote/trade/get"),
        6,
    ),
    (
        ResourceLocation("hextrace", "trace"),
        ResourceLocation("hexflow", "weak_escape"),
        "w",
    ),
}

# suppress failure to generate page title
UNTITLED_PAGES: set[tuple[ResourceLocation, str]] = {
    (ResourceLocation("hexcasting", "items/splicing_table"), "cost"),
}

# replace the pattern's name entirely
PATTERN_NAME_OVERRIDES: dict[ResourceLocation, str] = {
    ResourceLocation("hexpose", "read_book"): "Reading Purification (book)",
    ResourceLocation("hexpose", "create_text"): "Reading Purification (text)",
}

# append the mod's name to the pattern's name
DISAMBIGUATED_PATTERNS: set[ResourceLocation] = set()

DISABLED_PAGES: set[str] = set()

HEXDOC_PROPS: dict[str, Any] = {
    "modid": "hexbug",
    "book": "hexcasting:thehexbook",
    "resource_dirs": [
        *({"modid": mod.id, "external": False} for mod in MODS),
        {"modid": "minecraft"},
        {"modid": "hexdoc"},
    ],
    "extra": {"hexcasting": {"pattern_stubs": []}},
    "textures": {
        "missing": [
            "minecraft:chest",
            "minecraft:shield",
            "dthexcasting:*",
            "dynamictrees:*",
            "emi:*",
            "hexical:gauntlet_staff",
            "hexical:lightning_rod_staff",
            "hextended:livingwood_staff",
            "hextended:staff/livingwood",
            "hextended:staff/long/extended_staff",
        ]
    },
}
