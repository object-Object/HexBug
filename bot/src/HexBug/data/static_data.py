from typing import Any

from hexdoc.core import ResourceLocation
from yarl import URL

from .hex_math import HexDir
from .mods import Modloader, StaticModInfo
from .patterns import StaticPatternInfo
from .special_handlers import (
    MaskSpecialHandler,
    NumberSpecialHandler,
    OverevaluateTailDepthSpecialHandler,
    SpecialHandler,
)

MODS: list[StaticModInfo] = [
    StaticModInfo(
        id="hexcasting",
        name="Hex Casting",
        description="A mod for Forge and Fabric adding stack-based programmable spellcasting, inspired by Psi.",
        icon_url=URL(
            "https://media.forgecdn.net/avatars/thumbnails/535/944/64/64/637857298951404372.png"
        ),
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
        icon_url=URL(
            "https://raw.githubusercontent.com/object-Object/Caduceus/9737367b932ee5241615ea6d96fe6897ff8ea704/common/src/main/resources/assets/caduceus/icon.png"
        ),
        curseforge_slug="caduceus",
        modrinth_slug="caduceus",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="complexhex",
        name="Complex Hex",
        description="Adds complex numbers, quaternions, BIT displays, and bubbles.",
        icon_url=URL(
            "https://raw.githubusercontent.com/kineticneticat/ComplexHex/7b5e4b402cbcefbf37891b4714abeb37da9419be/common/src/main/resources/icon.png"
        ),
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
        icon_url=URL(
            "https://raw.githubusercontent.com/miyucomics/special-efhexs/81157d804c0e51a3082a1b328483425dec49f5da/src/main/resources/assets/efhexs/icon.png"
        ),
        curseforge_slug=None,
        modrinth_slug=None,
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="ephemera",
        name="Ephemera",
        description="An addon for Hex Casting with no particular theme.",
        icon_url=URL(
            "https://raw.githubusercontent.com/beholderface/Ephemera/bb4af6c760c0f0d7c4fe258e9459fbb609dcaa2c/fabric/src/main/resources/icon.png"
        ),
        curseforge_slug="ephemera",
        modrinth_slug="ephemera",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexal",
        name="Hexal",
        description="Adds many utility patterns/spells (eg. entity health, item smelting), autonomous casting with wisps, and powerful item manipulation/storage.",
        icon_url=URL(
            "https://cdn.modrinth.com/data/aBVJ6Q36/e2bfd87a5e333a972c39d12a1c4e55add7616785.jpeg"
        ),
        curseforge_slug="hexal",
        modrinth_slug="hexal",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="hexcassettes",
        name="Hexcassettes",
        description="Adds a method to delay hexes into the future, with a touch of playfulness and whimsy!",
        icon_url=URL(
            "https://raw.githubusercontent.com/miyucomics/hexcassettes/87fcc6422b5a995f7a70f3dae207ef420d55ebc7/src/main/resources/assets/hexcassettes/icon.png"
        ),
        curseforge_slug=None,
        modrinth_slug="hexcassettes",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexcellular",
        name="Hexcellular",
        description="Adds property iota to Hexcasting for easy syncing, storage, and communication of iota.",
        icon_url=URL(
            "https://raw.githubusercontent.com/miyucomics/hexcellular/d1b0b04332d01d05ecaab41617e36972d292069d/src/main/resources/assets/hexcellular/icon.png"
        ),
        curseforge_slug=None,
        modrinth_slug="hexcellular",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexchanting",
        name="Hexchanting",
        description="Imbue your equipment with the power of Hex Casting.",
        icon_url=URL(
            "https://raw.githubusercontent.com/arconyx/hexchanting/b737ba89641663ed83fc543d67a5fe447f2dac2a/src/main/resources/assets/hexchanting/icon.png",
        ),
        curseforge_slug=None,
        modrinth_slug="hexchanting",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hexdebug",
        name="HexDebug",
        description="Adds items and patterns to allow debugging hexes in VSCode, and a block to make editing hexes ingame much easier.",
        icon_url=URL(
            "https://raw.githubusercontent.com/object-Object/HexDebug/fa871595c3e5e8bc21e32170d6607bc172e2b951/Common/src/main/resources/icon.png"
        ),
        curseforge_slug="hexdebug",
        modrinth_slug="hexdebug",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hexdim",
        name="Hexxy Dimensions",
        description="Adds pocket dimensions.",
        icon_url=URL(
            "https://raw.githubusercontent.com/walksanatora/hexxy-dimensions/513e2f89c1bb88dff743f165a8e3e040a8596f5d/doc/icon.png"
        ),
        curseforge_slug=None,
        modrinth_slug="hexdim",
        modloaders=[Modloader.FABRIC],
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
        id="hexical",
        name="Hexical",
        description="A fun addon containing genie lamps, mage blocks, specks, world scrying, and more!",
        icon_url=URL(
            "https://raw.githubusercontent.com/miyucomics/hexical/09f8dc140b0075454fc4dbe7a4d6dbeac30354cc/src/main/resources/assets/hexical/icon.png"
        ),
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
        icon_url=URL(
            "https://raw.githubusercontent.com/miyucomics/hexodus/42a13fbd998689c70e90e1c40179cd35504c9477/src/main/resources/assets/hexodus/icon.png"
        ),
        curseforge_slug=None,
        modrinth_slug=None,
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hexpose",
        name="Hexpose",
        description="A library addon for Hexcasting that adds many scrying patterns and the iotas for other addons to use.",
        icon_url=URL(
            "https://cdn.modrinth.com/data/VWvaiZqR/92684dcd340ede08e3a9a5314221bc59f34072dd.png"
        ),
        curseforge_slug=None,
        modrinth_slug="hexpose",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hexstruction",
        name="HexStruction",
        description="Adds the ability to create, manipulate, and use Structure iotas.",
        icon_url=URL(
            "https://cdn.modrinth.com/data/dGRSMTTM/2a6bc4b80b41f5a464409827df5b4e85929e5cd5.png"
        ),
        curseforge_slug="hexstruction",
        modrinth_slug="hexstruction",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="hextended",
        name="Hextended Staves",
        description="Bolster your magic stick collection.",
        icon_url=URL(
            "https://raw.githubusercontent.com/abilliontrillionstars/hextended-staves/e3d6a09dbbdb425bfeca40c41f58928d01b24c65/common/src/main/icon.png"
        ),
        curseforge_slug="hextended-staves",
        modrinth_slug="hextended-staves",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
    StaticModInfo(
        id="hextrogen",
        name="Hextrogen",
        description="Adds interop with Create: Estrogen.",
        icon_url=URL(
            "https://raw.githubusercontent.com/miyucomics/hextrogen/da935ed8dbe3958180e45fe031c9aa42a9fbd901/src/main/resources/assets/hextrogen/icon.png"
        ),
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
        icon_url=URL(
            "https://cdn.modrinth.com/data/ybwf7iLN/6b830c0683581bf124c5b83ab33b0965b982e832.png"
        ),
        curseforge_slug="hierophantics",
        modrinth_slug="hierophantics",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="ioticblocks",
        name="IoticBlocks",
        description="Adds patterns for reading and writing iotas to/from blocks, and an API for addon developers to easily add iota reading/writing support to their blocks.",
        icon_url=URL(
            "https://raw.githubusercontent.com/object-Object/IoticBlocks/99a2c20a1e91b8fc0319dce133aac7766a34e024/common/src/main/resources/assets/ioticblocks/icon.png"
        ),
        curseforge_slug="ioticblocks",
        modrinth_slug="ioticblocks",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="lapisworks",
        name="Lapisworks",
        description="Harness Lapis' enchanting power with Hex Casting's media and enchant yourself.",
        icon_url=URL(
            "https://cdn.modrinth.com/data/YPwDELmO/4b950eeaccc76fe5dd989aac30bb6750c12979cf.png"
        ),
        curseforge_slug=None,
        modrinth_slug="lapisworks",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="lessertp",
        name="Lesser Teleport",
        description="A port of Lesser Teleport from HexKinetics.",
        icon_url=URL(
            "https://raw.githubusercontent.com/Real-Luxof/Lesser-Teleport/d74d97975d04b5d13b175ba39aa2b85ab397977e/src/main/resources/assets/lessertp/icon.png"
        ),
        curseforge_slug=None,
        modrinth_slug="lesser-teleport",
        modloaders=[Modloader.FABRIC],
    ),
    StaticModInfo(
        id="moreiotas",
        name="MoreIotas",
        description="Adds iotas for strings, matrices, types, and items.",
        icon_url=URL(
            "https://raw.githubusercontent.com/FallingColors/MoreIotas/9d053970db7cc4d4c29b12632521bf532612adf3/Common/src/main/resources/logo.png"
        ),
        curseforge_slug="moreiotas",
        modrinth_slug="moreiotas",
        modloaders=[Modloader.FABRIC, Modloader.FORGE],
    ),
    StaticModInfo(
        id="oneironaut",
        name="Oneironaut",
        description="An addon for Hex Casting centered around exploration and use of the Noosphere.",
        icon_url=URL(
            "https://raw.githubusercontent.com/beholderface/oneironaut/e3768da4faf3ea50e889178d26fa6d003f40a28b/fabric/src/main/resources/icon.png"
        ),
        curseforge_slug="oneironaut",
        modrinth_slug="oneironaut",
        modloaders=[Modloader.FABRIC, Modloader.QUILT],
    ),
    StaticModInfo(
        id="overevaluate",
        name="Overevaluate",
        description="Adds sets and patterns for advanced metaevals and stack manipulation.",
        icon_url=URL(
            "https://raw.githubusercontent.com/miyucomics/overevaluate/d81fcc6e28558800b185df8c0d4b2c23844a09b6/src/main/resources/assets/overevaluate/icon.png"
        ),
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
        icon_url=URL(
            "https://cdn.modrinth.com/data/3DnSSjl3/47d6ade3a5550904b56d119c9ba14f59e26966bb.png"
        ),
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

EXTRA_PATTERNS: list[StaticPatternInfo] = [
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "escape"),
        startdir=HexDir.WEST,
        signature="qqqaw",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "open_paren"),
        startdir=HexDir.WEST,
        signature="qqq",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "close_paren"),
        startdir=HexDir.EAST,
        signature="eee",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "undo"),
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
    ]
}

DISABLED_PATTERNS: set[ResourceLocation] = {
    # commented out, but the regex doesn't account for that
    # https://github.com/FallingColors/Hexal/blob/efe2b7df1e/Common/src/main/java/ram/talia/hexal/common/lib/hex/HexalActions.kt#L210
    ResourceLocation("hexal", "gate/mark/num/get"),
    ResourceLocation("hexal", "mote/count/get"),
    ResourceLocation("hexal", "mote/combine"),
    # unused
    ResourceLocation("moreiotas", "altadd"),
    # undocumented
    ResourceLocation("complexhex", "chloe/copy"),
    ResourceLocation("complexhex", "chloe/make"),
    ResourceLocation("complexhex", "cnarg"),
    ResourceLocation("ephemera", "hashbits"),
    ResourceLocation("hexical", "disguise_mage_block"),
    ResourceLocation("hexical", "tweak_mage_block"),
    ResourceLocation("hexpose", "entity_name"),
    ResourceLocation("hextweaks", "you_like_drinking_potions"),
    ResourceLocation("lapisworks", "empty_prfn"),
    ResourceLocation("oneironaut", "advanceautomaton"),
    ResourceLocation("oneironaut", "checksignature"),
    ResourceLocation("oneironaut", "erosionshield"),
    ResourceLocation("oneironaut", "getsoulprint"),
    ResourceLocation("oneironaut", "signitem"),
    # conflicts
    ResourceLocation("hexical", "age_scroll"),  # shape: hexical:greater_blink
    ResourceLocation("hexstruction", "bounding_box"),  # shape: hexical:greater_blink
    # lmao what
    ResourceLocation("ephemera", "no"),
    ResourceLocation("hextweaks", "suicide"),
    ResourceLocation("oneironaut", "circle"),
    # lapisworks? apparently it doesn't
    ResourceLocation("lapisworks", "create_enchsent2"),
    ResourceLocation("lapisworks", "create_enchsent3"),
    ResourceLocation("lapisworks", "create_enchsent4"),
    ResourceLocation("lapisworks", "create_enchsent5"),
    ResourceLocation("lapisworks", "create_enchsent6"),
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
            "hexdebug:*",
            "hexical:gauntlet_staff",
            "hexical:lightning_rod_staff",
            "hextended:livingwood_staff",
            "hextended:staff/livingwood",
            "hextended:staff/long/extended_staff",
        ]
    },
}
