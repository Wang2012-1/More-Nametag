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
    # 简单渐变处理示例（需要扩展实现）
    return text.replace('<gradient>', '§c§l').replace('</gradient>', '§r')

class Config:
    def __init__(self):
        self.allowed_colors = ['red', 'blue', 'green', 'gradient']
        self.max_length = 16

    @classmethod
    def load(cls):
        # 配置文件加载逻辑
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
        '!!nametag set <内容> - 设置称号\n',
        '!!nametag color <颜色> - 选择颜色\n',
        '可用颜色：', ', '.join(COLOR_CODES.keys())
    )

...
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
    if not isinstance(source, PlayerCommandSource):
        source.reply('仅玩家可使用此命令')
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
    # 颜色处理逻辑（略）

@new_thread
def preview_command(source: CommandSource):
    # 预览逻辑（略）

@listener
def on_player_joined(server: ServerInterface, player: str, info: Info):
    tag = NameTagData().data.get(player)
    if tag:
        server.execute(f'tellraw {player} {{"text":"你的称号已加载：", "extra":[{{"text":"{tag}"}}]}}')
        server.execute(f'team modify nametag suffix {{"text":" {tag}"}}')