# command/group/parameter name:
#       |------------------------------|


# command/group/parameter description:
#       |--------------------------------------------------------------------------------------------------|


# common parameters

-parameter_visibility = visibility
-parameter_visibility_description = 回复对所有人可见还是仅自己可见。

# /decode

group_decode = decode
    .description = 使用揭示解码导出的iota。
-decode_contents_description = 对iota使用揭示的输出结果，直接从latest.log复制而来。
-decode_tab-width = tab_width
-decode_tab-width_description = 每级缩进的空格数。

# /decode text

command_decode-text = text
    .description = 使用揭示解码导出的iota。
    .parameter_text = text
    .parameter_text_description = { -decode_contents_description }
    .parameter_flatten-list = { -decode_flatten-list }
    .parameter_flatten-list_description = { -decode_flatten-list_description }
    .parameter_tab-width = { -decode_tab-width }
    .parameter_tab-width_description = { -decode_tab-width_description }
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }

# /decode file

command_decode-file = file
    .description = 使用揭示解码包含iota的导出文件。
    .parameter_file = file
    .parameter_file_description = { -decode_contents_description }
    .parameter_flatten-list = { -decode_flatten-list }
    .parameter_flatten-list_description = { -decode_flatten-list_description }
    .parameter_tab-width = { -decode_tab-width }
    .parameter_tab-width_description = { -decode_tab-width_description }
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }

# /mod

command_mod = mod
    .description = 显示HexBug所支持模组的信息和链接。
    .parameter_mod = mod
    .parameter_mod_description = 所查找模组的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_loaders = 支持的加载器
    .text_curseforge = CurseForge
    .text_modrinth = Modrinth
    .text_source-github = GitHub
    .text_source-codeberg = Codeberg
    .text_patterns = 图案
    .text_overloads = 重载
    .text_overloads-value =
        { $first_party } 第一方
        { $third_party } 第三方
    .text_special = 特殊处理程序
    .text_categories = 类别
    .text_entries = 条目
    .text_pages = 可链接页面
    .text_recipes = 配方

# /mods

command_mods = mods
    .description = 列出HexBug支持的所有模组，可进行筛选。
    .parameter_author = author
    .parameter_author_description = 仅显示作者为所给GitHub用户的模组。
    .parameter_modloader = modloader
    .parameter_modloader_description = 仅显示支持所给加载器的模组。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title =
        { $modloader ->
            [None] 已加载模组
           *[other] 已加载模组（{ $modloader }）
        }
    .text_footer-normal = 总计：{ $mods }
    .text_footer-filtered = 总计：{ $mods }/{ $total }
    .text_no-mods-found = ⚠️ 未找到符合所给筛选条件的模组。

# /pattern

group_pattern = pattern
    .description = 用于查找和渲染图案的命令。

# /pattern name

command_pattern-name = name
    .description = 按名称查找图案。
    .parameter_info = name
    .parameter_info_description = 所查找图案的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }

# /pattern special

command_pattern-special = special
    .description = 使用特殊处理程序生成图案（如簿记员之策略）。
    .parameter_info = name
    .parameter_info_description = 所生成图案的名称。
    .parameter_value = value
    .parameter_value_description = 特殊处理程序接受的值（如v-vv---v）。具体格式由所生成图案决定。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }

# /pattern raw

command_pattern-raw = raw
    .description = 根据笔迹签名生成图案。
    .parameter_direction = { -parameter_direction }
    .parameter_direction_description = { -parameter_direction_description }
    .parameter_signature = { -parameter_signature }
    .parameter_signature_description = { -parameter_signature_description }
    .parameter_hide-stroke-order = { -parameter_hide-stroke-order }
    .parameter_hide-stroke-order_description = { -parameter_hide-stroke-order_description }
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }

# /pattern check

command_pattern-check = check
    .description = 检验图案是否已存在于HexBug支持的任意模组中。
    .parameter_signature = { -parameter_signature }
    .parameter_signature_description = { -parameter_signature_description }
    .parameter_pattern-type = type
    .parameter_pattern-type_description = 检验冲突时将图案视作所给类型。
    .parameter_direction = { -parameter_direction }
    .parameter_direction_description = { -parameter_direction_description }
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title =
        { $conflicts ->
            [0] 未找到冲突。
           *[other] 已找到冲突！
        }
    .text_timeout = ⚠️ 超时：{ $time }秒。
    .text_conflict-signature = 签名
    .text_conflict-shape = 形状
    .text_conflict-prefix = 前缀
    .text_conflict-regex = 正则表达式

# /status

command_status = status
    .description = 显示关于HexBug的信息。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title = HexBug状态
    .text_commit = 已部署的提交
    .text_commit-unknown = 未知
    .text_deployment-time = 部署时间
    .text_deployment-time-unknown = 未知
    .text_uptime = 运行时间
    .text_installs = 安装情况
    .text_installs-value =
        { $servers }个服务器
        { $users }个个人用户
    .text_mods = 模组
    .text_patterns = 图案
    .text_categories = 类别
    .text_entries = 条目
    .text_pages = 可链接页面
    .text_recipes = 配方
-parameter_direction = direction
-parameter_direction_description = 图案的起始方向（如SOUTH_EAST）。
-parameter_show-signatures = show_signatures
-parameter_show-signatures_description = 在内嵌脚注处显示图案的签名。
-parameter_signature = signature
-parameter_signature_description = 图案的笔迹签名（如deaqq）。
-parameter_hide-stroke-order = hide_stroke_order
-parameter_hide-stroke-order_description = 渲染图案时隐藏笔顺（如卓越法术等）。
choice_HexBug-utils-discord-visibility-Visibility =
    .PUBLIC = 所有人
    .PRIVATE = 仅自己
per-world-pattern-added = ✅ **图案已添加。**
per-world-pattern-contributor = 添加者：{ $name }
choice_HexBug-cogs-app-commands-pattern-PatternCheckType =
    .NORMAL = 常规
    .PER-WORLD = 笔顺因世界而异
    .REGEX = 正则表达式
    .SPECIAL-PREFIX = 特殊处理程序前缀
choice_HexBug-cogs-app-commands-info-InfoMessage =
    .addons = 附属
    .bosnia = Bosnia
    .bosnia_text_description = 植物魔法。
    .bug-report = 漏洞反馈
    .bug-report_text_description =
        请勿在Discord中反馈漏洞。可选择向模组GitHub的漏洞追踪器反馈。

        咒法学：https://github.com/gamma-delta/HexMod/issues
        PAUCAL：https://github.com/gamma-delta/PAUCAL/issues
        附属：`/mod`
    .crashlog = 崩溃日志
    .crashlog_text_description =
        可使用[mclo.gs](https://mclo.gs)（首选）、[Pastebin](https://pastebin.com)等服务发送崩溃日志。
        请*勿*直接以消息或文件形式上传至Discord。
    .forum = 论坛
    .forum_text_title = petrak@的模组论坛
    .forum_text_description =
        分享和浏览酷炫咒术、寻找帮助、讨论petrak@的模组，尽在{ "[" }论坛](https://forum.petra-k.at/ucp.php?mode=register)。

        { "**" }快捷链接**
        { "[" }General Chat](https://forum.petra-k.at/viewforum.php?f=7)
        { "[" }Akashic Records](https://forum.petra-k.at/viewforum.php?f=2)
        { "[" }Hexcasting Help](https://forum.petra-k.at/viewforum.php?f=5)
        { "[" }Miner's Lung](https://forum.petra-k.at/viewforum.php?f=9)
        { "[" }Bliss Mods](https://forum.petra-k.at/viewforum.php?f=10)
    .great-spells = 卓越法术
    .gtp-itemdrop = 卓越传送掉落物品
    .gtp-itemdrop_text_description =
        对自身施放卓越传送时，物品栏中的每个物品（手持槽和模组新增槽位中的除外）都有可能掉落在目的地，掉落的概率各异。
        物品栏三行物品的概率为N/10,000。快捷栏物品的概率为N/20,000。盔甲槽物品的概率为N/40,000。
        N为卓越传送所获偏移向量的长度。若你处于1.19.2版本及以下，此法术有32,768米的范围上限，超过上限的传送会失败，但物品会照常掉落。
    .patterns = patterns.csv
    .pluralkit = PluralKit
    .pluralkit_text_description =
        { "**" }`[BOT]`消息是做什么的？**
        这是PluralKit，为多意识体准备的Discord机器人。多意识体（Plurality），即在一个身体内存在多个意识的体验。

        { "[" }PluralKit](https://pluralkit.me/)  |  [更多有关多意识体的信息](https://morethanone.info/)
    .tools = 工具
choice_HexBug-cogs-app-commands-patterns-StackOrder =
    .BOTTOM-TO-TOP = 从底至顶
    .TOP-TO-BOTTOM = 从顶至底
book-category = 类别
book-entry = 条目
book-placeholder-page-title = { $entry }，第{ $index }页
group_book = book
    .description = 用于获取网页手册内容链接的命令。
command_book-home = home
    .description = 获取所给模组网页手册的链接。
    .parameter_mod = mod
    .parameter_mod_description = 所查找模组的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_categories = 类别
    .text_entries = 条目
    .text_pages = 可链接页面
    .text_recipes = 配方
command_book-category = category
    .description = 获取模组网页手册中特定类别的链接。
    .parameter_category = category
    .parameter_category_description = 所查找类别的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title = { "[" }类别] { $name }
command_book-entry = entry
    .description = 获取模组网页手册中特定条目的链接。
    .parameter_entry = entry
    .parameter_entry_description = 所查找条目的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title = { "[" }条目] { $name }
command_book-page = page
    .description = 获取模组网页手册中特定页面（若有锚点）的链接。
    .parameter_page = page
    .parameter_page_description = 所查找页面的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title = { "[" }页面] { $title }
command_book-recipe = recipe
    .description = 获取模组网页手册中特定配方的链接。
    .parameter_recipes = item
    .parameter_recipes_description = 所合成物品的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title = { "[" }配方] { $title }
    .text_page = 页面
command_book-search = search
    .description = 在所有模组手册中搜索文本，使用Tantivy的查询语言。
    .parameter_query = query
    .parameter_query_description = 所查询的内容。
    .parameter_mod = mod
    .parameter_mod_description = 仅显示来自所给模组的搜索结果。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
command_changelog = changelog
    .description = 显示HexBug的更新日志。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
-decode_flatten-list = flatten_list
-decode_flatten-list_description = 若解码的iota是列表，则取消缩进，并用<>括起各iota。
command_entry-point = 打开法杖网格
    .description = 打开法杖网格绘制图案。
command_info = info
    .description = 显示预先写好的消息。
    .parameter_message = message
    .parameter_message_description = 所显示消息的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_footer-usage-count = 显示次数：{ $count }
    .text_footer-days-since = 自上一次显示的时间：{ $days }天
command_palette = palette
    .description = 显示所给的HexBug图案配色。
    .parameter_palette = palette
    .parameter_palette_description = 所显示配色的名称。
    .parameter_hide-stroke-order = { -parameter_hide-stroke-order }
    .parameter_hide-stroke-order_description = { -parameter_hide-stroke-order_description }
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_rgb = RGB
    .text_hex = Hex
    .text_int = Int
    .text_colors =
        笔划：
        { $colors }

        重叠：
        { $overlap }

        笔顺不定：
        { $per_world }
command_pattern-build = build
    .description = 通过方向按钮逐笔划绘制图案。
    .parameter_direction = direction
    .parameter_direction_description = 图案的起始方向（如SOUTH_EAST）。
    .parameter_signature = signature
    .parameter_signature_description = 图案的初始笔迹签名（如deaqq）。
    .parameter_hide-stroke-order = { -parameter_hide-stroke-order }
    .parameter_hide-stroke-order_description = { -parameter_hide-stroke-order_description }
group_patterns = patterns
    .description = 用于生成和渲染任意数量个图案的命令。
command_patterns-draw = draw
    .description = 在法杖网格中绘制图案并将结果显示于消息。
    .parameter_show-signatures = { -parameter_show-signatures }
    .parameter_show-signatures_description = { -parameter_show-signatures_description }
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_empty = 等待图案中……
command_patterns-hex = hex
    .description = 显示图案列表。
    .parameter_hex = hex
    .parameter_hex_description = 任意数量个需显示的图案，以逗号分隔。接受缩写和简写。
    .parameter_show-signatures = { -parameter_show-signatures }
    .parameter_show-signatures_description = { -parameter_show-signatures_description }
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
command_patterns-number = number
    .description = 生成并显示会压入所给有理数的图案序列。
    .parameter_number = number
    .parameter_number_description = 所压入的数。接受小数和分数。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
command_patterns-swindler = swindler
    .description = 生成并显示按所给指示重排栈的骗徒之策略所对应的Lehmer数。
    .parameter_order = order
    .parameter_order_description = before和after参数从顶至底还是从底至顶给出栈中各元素。
    .parameter_before = before
    .parameter_before_description = 重排前栈中元素的排列，可用逗号或空格分隔。
    .parameter_after = after
    .parameter_after_description = 重排后栈中元素的排列，可用逗号或空格分隔。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
group_per-world-pattern = per-world-pattern
    .description = 用于增补和查询服务器中笔顺因世界而异图案的命令。
command_per-world-pattern-add = add
    .description = 向服务器数据库新增一则笔顺因世界而异的图案。
    .parameter_direction = { -parameter_direction }
    .parameter_direction_description = { -parameter_direction_description }
    .parameter_signature = { -parameter_signature }
    .parameter_signature_description = { -parameter_signature_description }
command_per-world-pattern-list = list
    .description = 列出服务器数据库中所有笔顺因世界而异的图案。
    .parameter_contributor = contributor
    .parameter_contributor_description = 仅列出由所给用户添加的图案。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
    .text_title = 笔顺因世界而异的图案
    .text_no-patterns-found = ⚠️ 未找到图案。
command_per-world-pattern-name = name
    .description = 按名称查询服务器数据库中笔顺因世界而异的图案。
    .parameter_entry = name
    .parameter_entry_description = 所查询图案的名称。
    .parameter_visibility = { -parameter_visibility }
    .parameter_visibility_description = { -parameter_visibility_description }
command_per-world-pattern-remove = remove
    .description = 从服务器中移除某个笔顺因世界而异的图案。
    .parameter_entry = name
    .parameter_entry_description = 所移除图案的名称。只能移除由你添加的图案。
    .text_removed = ✅ **图案已移除。**
group_per-world-pattern-manage = per-world-pattern-manage
    .description = 用于管理服务器中笔顺因世界而异图案签名的高权限命令。
command_per-world-pattern-manage-add = add
    .description = 向服务器数据库新增不在HexBug注册表中的、笔顺因世界而异的图案。
    .parameter_pattern-id = id
    .parameter_pattern-id_description = 所新增图案的ID（如hexcasting:create_lava）。
    .parameter_direction = { -parameter_direction }
    .parameter_direction_description = { -parameter_direction_description }
    .parameter_signature = { -parameter_signature }
    .parameter_signature_description = { -parameter_signature_description }
command_per-world-pattern-manage-remove = remove
    .description = 从服务器数据库中移除由其他用户添加的、笔顺因世界而异的图案。
    .parameter_entry = name
    .parameter_entry_description = 所移除图案的名称。
    .text_removed = ✅ **图案已移除。**
command_per-world-pattern-manage-remove-all = remove-all
    .description = 清空服务器数据库中笔顺因世界而异的图案。
    .parameter_contributor = contributor
    .parameter_contributor_description = 仅移除由所给用户添加的图案。
    .text_confirm-all = 是否确认从服务器中移除**{ $count }个图案**？
    .text_confirm-user = 是否确认从服务器中移除由{ $user }添加的**{ $count }个图案**？
    .text_cancel = 取消
    .text_remove = 移除图案
    .text_cancelled = 已取消。
    .text_removed = 已移除{ $count }个图案。
