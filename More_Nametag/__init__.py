from mcdreforged.api.all import *

import json
import os
import re

CONFIG_PATH = os.path.join('config', 'more_nametag.json')
DATA_PATH = os.path.join('config', 'nametag_data.json')

# 颜色代码映射
COLOR_CODES = {
    'black': '§0', 'dark_blue': '§1', 'dark_green': '§2',
    'dark_aqua': '§3', 'dark_red': '§4', 'dark_purple': '§5',
    'gold': '§6', 'gray': '§7', 'dark_gray': '§8',
    'blue': '§9', 'green': '§a', 'aqua': '§b',
    'red': '§c', 'light_purple': '§d', 'yellow': '§e',
    'white': '§f', 'reset': '§r'
}

def convert_gradient(text):
    text = re.sub(r'&g(\S+)', r'<gradient>\1</gradient>', text)
    colors = ['§c', '§6', '§e', '§a', '§b', '§9', '§d']
    result = []
    tag = re.search(r'<gradient>(.*?)</gradient>', text)
    if tag:
        content = tag.group(1)
        for i, char in enumerate(content):
            color = colors[i % len(colors)]
            result.append(f'{color}{char}')
        return text.replace(tag.group(0), ''.join(result))
    return text

class Config:
    def __init__(self):
        self.allowed_colors = ['red', 'blue', 'green', 'gradient']
        self.max_length = 16
        self.enable_gradient = True

    @classmethod
    def load(cls):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                cfg = cls()
                cfg.allowed_colors = data.get('allowed_colors', cfg.allowed_colors)
                cfg.max_length = data.get('max_length', cfg.max_length)
                cfg.enable_gradient = data.get('enable_gradient', cfg.enable_gradient)
                return cfg
        except:
            return cls()

class NameTagData:
    def __init__(self):
        self.data = {}

    def load(self):
        try:
            with open(DATA_PATH, 'r') as f:
                self.data = json.load(f)
        except:
            self.data = {}

    def save(self):
        with open(DATA_PATH, 'w') as f:
            json.dump(self.data, f)

    def set_tag(self, player, tag):
        self.data[player] = tag
        self.save()

def build_help():
    return RTextList(
        '!!nametag set [&g内容] - 设置称号（&g开头自动渐变）\n',
        '!!nametag color <颜色> - 选择颜色\n',
        '可用颜色：', ', '.join(COLOR_CODES.keys())
    )

def on_load(server: PluginServerInterface, prev_module):
    server.register_help_message('!!nametag', '自定义玩家称号')
    server.register_command(
        Literal('!!nametag').
        then(Literal('set').arg('text').runs(set_tag_command)).
        then(Literal('color').arg('color').suggests(lambda: COLOR_CODES.keys()).runs(set_color_command)).
        then(Literal('preview').runs(preview_command))
    )

@new_thread
def set_tag_command(source: CommandSource, context):
    if not isinstance(source, PlayerCommandSource) or not source.has_permission(3):
        source.reply('§c需要管理员权限（3级）以上才能使用此命令')
        return
    
    player = source.player
    tag = context['text'].replace('&', '§')
    
    # 长度和颜色验证
    if len(tag) > config.max_length:
        source.reply(f'称号过长（最大{config.max_length}字符）')
        return
    
    NameTagData().set_tag(player, tag)
    source.get_server().execute(f'tellraw {player} {{"text":"称号已更新：", "extra":[{{"text":"{tag}"}}]}}')

@new_thread
def set_color_command(source: CommandSource, context):
    if not isinstance(source, PlayerCommandSource) or not source.has_permission(3):
        source.reply('§c需要管理员权限（3级）以上才能使用此命令')
        return
    
    color = context['color']
    if color not in config.allowed_colors:
        source.reply(f'不支持的颜色，可用颜色：{config.allowed_colors}')
        return
    
    player = source.player
    data = NameTagData()
    current_tag = data.data.get(player, '')
    
    # 移除现有颜色代码
    clean_tag = re.sub(r'§[0-9a-f]', '', current_tag)
    new_tag = COLOR_CODES.get(color, '') + clean_tag
    
    if len(new_tag) > config.max_length:
        source.reply(f'添加颜色后超过长度限制（最大{config.max_length}字符）')
        return
    
    data.set_tag(player, new_tag)
    source.reply(f'§a颜色已应用！当前称号：{new_tag}')

@new_thread
def preview_command(source: CommandSource):
    if not isinstance(source, PlayerCommandSource) or not source.has_permission(3):
        source.reply('§c需要管理员权限才能预览')
        return
    
    player = source.player
    current_tag = NameTagData().data.get(player, '无')
    
    # 生成渐变预览
    sample_text = '我的酷炫称号'
    if config.enable_gradient:
        preview_text = convert_gradient(f'<gradient>{sample_text}</gradient>')
    else:
        preview_text = sample_text
    
    source.get_server().execute(
        f'tellraw {player} '
        '["",'
        '{"text":"[预览] ","color":"gray"},'
        f'{{"text":"{preview_text}","italic":true}}]'
    )

@listener
def on_player_joined(server: ServerInterface, player: str, info: Info):
    tag = NameTagData().data.get(player)
    if tag:
        server.execute(f'tellraw {player} {{"text":"你的称号已加载：", "extra":[{{"text":"{tag}"}}]}}')
        server.execute(f'team modify nametag suffix {{"text":" {tag}"}}')