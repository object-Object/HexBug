# command/group/parameter name:
#       |------------------------------|

# command/group/parameter description:
#       |--------------------------------------------------------------------------------------------------|

# common parameters

-parameter_visibility =
        visibility
-parameter_visibility_description =
        回复对所有人可见还是仅自己可见。

# /decode

group_decode =
        decode
    .description =
        使用揭示解码导出的iota。

-decode_contents_description =
        对iota使用揭示的输出结果，直接从latest.log复制而来。

-decode_tab-width =
        tab_width
-decode_tab-width_description =
        每级缩进的空格数。

# /decode text

command_decode-text =
        text
    .description =
        使用揭示解码导出的iota。

    .parameter_text =
        text
    .parameter_text_description = {-decode_contents_description}

    .parameter_tab-width = {-decode_tab-width}
    .parameter_tab-width_description = {-decode_tab-width_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /decode file

command_decode-file =
        file
    .description =
        使用揭示解码包含iota的导出文件的内容。

    .parameter_file =
        file
    .parameter_file_description = {-decode_contents_description}

    .parameter_tab-width = {-decode_tab-width}
    .parameter_tab-width_description = {-decode_tab-width_description}

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /mod

command_mod =
        mod
    .description =
        显示HexBug所支持的模组的信息和链接。

    .parameter_mod =
        mod
    .parameter_mod_description =
        所查找模组的名称。

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /mods

command_mods =
        mods
    .description =
        列出HexBug支持的所有模组，过滤可选。

    .parameter_author =
        author
    .parameter_author_description =
        仅显示作者为该GitHub用户的模组。

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern

group_pattern =
        pattern
    .description =
        查找和渲染图案的命令。

# /pattern name

command_pattern-name =
        name
    .description =
        按名称查找图案。

    .parameter_info =
        name
    .parameter_info_description =
        所查找图案的名称。

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern special

command_pattern-special =
        special
    .description =
        使用特殊处理程序生成图案（如簿记员之策略）。

    .parameter_info =
        name
    .parameter_info_description =
        所生成图案的名称。

    .parameter_value =
        value
    .parameter_value_description =
        特殊处理程序接受的值（如v-vv---v）。具体格式由所生成图案决定。

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern raw

command_pattern-raw =
        raw
    .description =
        根据笔迹朝向特征生成图案。

    .parameter_direction =
        direction
    .parameter_direction_description =
        图案的起始方向（如SOUTH_EAST）。

    .parameter_signature =
        signature
    .parameter_signature_description =
        图案的笔迹朝向特征（如deaqq）。

    .parameter_hide-stroke-order =
        hide_stroke_order
    .parameter_hide-stroke-order_description =
        若为true，则在渲染图案时隐藏笔顺（类似卓越法术）。

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

# /pattern check

command_pattern-check =
        check
    .description =
        检验图案是否已存在于任意HexBug支持的模组中。

    .parameter_signature =
        signature
    .parameter_signature_description =
        图案的笔迹朝向特征（如deaqq）。

    .parameter_is-per-world =
        is_per_world
    .parameter_is-per-world_description =
        若为true，则同时检验是否存在形状相同、笔顺不同，且不随世界不同而改变的图案。

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

    .text_title =
        { $conflicts ->
            [0] 未找到冲突。
            *[other] 已找到冲突！
        }

# /status

command_status =
        status
    .description =
        显示关于HexBug的信息。

    .parameter_visibility = {-parameter_visibility}
    .parameter_visibility_description = {-parameter_visibility_description}

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
