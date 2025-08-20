from mcdreforged.api.decorator import new_thread
from mcdreforged.api.command import Literal
from mcdreforged.api.rtext import RTextList
from mcdreforged.api.types import PluginServerInterface, ServerInterface, Info,CommandSource, PlayerCommandSource
from typing import List, Dict, Optional
import json
import os
import re
import math

# 常量定义
CONFIG_PATH = os.path.join('config', 'more_nametag.json')
DATA_PATH = os.path.join('config', 'nametag_data.json')

# 颜色代码映射
COLOR_MAP = {
    'black': '§0', 'dark_blue': '§1', 'dark_green': '§2',
    'dark_aqua': '§3', 'dark_red': '§4', 'dark_purple': '§5',
    'gold': '§6', 'gray': '§7', 'dark_gray': '§8',
    'blue': '§9', 'green': '§a', 'aqua': '§b',
    'red': '§c', 'light_purple': '§d', 'yellow': '§e',
    'white': '§f', 'reset': '§r'
}

# 渐变颜色预设
GRADIENT_PRESETS = {
    'rainbow': ['§c', '§6', '§e', '§a', '§b', '§9', '§d'],
    'fire': ['§c', '§6', '§e'],
    'ice': ['§b', '§9', '§f'],
    'nature': ['§2', '§a', '§e']
}

class Config:
    """插件配置类"""
    def __init__(self):
        self.allowed_colors = ['red', 'blue', 'green', 'gradient']
        self.max_length = 16
        self.enable_gradient = True
        self.gradient_preset = 'rainbow'
    
    @classmethod
    def load(cls):
        """加载配置文件"""
        if not os.path.exists(CONFIG_PATH):
            return cls()
        try:
            with open(CONFIG_PATH, 'r', encoding='utf8') as f:
                data = json.load(f)
                config = cls()
                config.allowed_colors = data.get('allowed_colors', config.allowed_colors)
                config.max_length = data.get('max_length', config.max_length)
                config.enable_gradient = data.get('enable_gradient', config.enable_gradient)
                config.gradient_preset = data.get('gradient_preset', config.gradient_preset)
                return config
        except:
            return cls()

    def save(self):
        """保存配置文件"""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf8') as f:
            json.dump({
                'allowed_colors': self.allowed_colors,
                'max_length': self.max_length,
                'enable_gradient': self.enable_gradient,
                'gradient_preset': self.gradient_preset
            }, f, indent=2)

class NameTagManager:
    """称号数据管理器"""
    def __init__(self):
        self.data = {}

    def load(self):
        """加载数据文件"""
        try:
            if os.path.exists(DATA_PATH):
                with open(DATA_PATH, 'r', encoding='utf8') as f:
                    self.data = json.load(f)
        except:
            self.data = {}

    def save(self):
        """保存数据到文件"""
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        with open(DATA_PATH, 'w', encoding='utf8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def set_tag(self, player, tag):
        """设置玩家称号"""
        self.data[player] = tag
        self.save()

    def get_tag(self, player):
        """获取玩家称号"""
        return self.data.get(player)

def convert_to_gradient(text, gradient_colors=None):
    """
    改进版渐变文本转换
    :param text: 包含<gradient>标签的文本
    :param gradient_colors: 自定义颜色序列
    :return: 转换后的带颜色代码文本
    """
    if gradient_colors is None:
        gradient_colors = GRADIENT_PRESETS.get(config.gradient_preset, GRADIENT_PRESETS['rainbow'])
    
    def process_gradient(match):
        content = match.group(1)
        if not content:
            return ''
        
        result = []
        color_count = len(gradient_colors)
        
        for i, char in enumerate(content):
            pos = i / max(1, len(content) - 1)
            color_index = min(int(pos * color_count), color_count - 1)
            color = gradient_colors[color_index]
            result.append(f'{color}{char}')
        
        return ''.join(result)
    
    # 处理标准渐变标签
    processed = re.sub(r'<gradient>(.*?)</gradient>', process_gradient, text)
    # 处理简写格式
    processed = re.sub(r'&g([^\s]+)', r'<gradient>\1</gradient>', processed)
    
    return processed

def build_help_message():
    """构建帮助消息"""
    return RTextList(
        '!!nametag set <内容> - 设置称号（支持&g开头自动渐变）\n',
        '!!nametag color <颜色> - 选择颜色\n',
        '!!nametag preset <预设名> - 设置渐变预设\n',
        '可用颜色：', ', '.join(COLOR_MAP.keys()) + '\n',
        '渐变预设：', ', '.join(GRADIENT_PRESETS.keys())
    )

# 全局配置实例
config = Config.load()

def on_player_joined(server: ServerInterface, player: str, info: Info):
    """玩家加入事件处理"""
    if (tag := NameTagManager().get_tag(player)) is not None:
        server.say(RTextList(f'§a玩家 {player} 已加载称号：', tag))
        server.execute(f'team modify nametag suffix {{"text":" {tag}"}}')

def on_player_left(server: ServerInterface, player: str):
    """玩家离开事件处理（示例）"""
    if config.debug_mode:
        server.logger.info(f'玩家 {player} 已离开服务器')

def on_server_start(server: PluginServerInterface):
    """服务器启动事件处理（示例）"""
    server.logger.info('称号插件已就绪')

def on_load(server: PluginServerInterface, prev_module):
    """插件加载入口"""
    NameTagManager().load()
    
    # 注册帮助消息
    server.register_help_message('!!nametag', '自定义玩家称号')
    
    # 注册命令（使用手动参数解析）
    server.register_command(
        Literal('!!nametag').
        then(Literal('set').runs(set_tag_command)).
        then(Literal('color').runs(set_color_command)).
        then(Literal('preset').runs(set_preset_command)).
        then(Literal('preview').runs(preview_command))
    )
    
    # 手动注册事件监听器
    server.register_event_listener(
        'mcdr.player_joined',  # 等同于LiteralEvent.PLAYER_JOINED
        on_player_joined,
        priority=1000
    )
    
    # 注册其他事件示例
    server.register_event_listener(
        'mcdr.player_left',  # 等同于LiteralEvent.PLAYER_LEFT
        on_player_left,
        priority=500
    )
    
    server.register_event_listener(
        'mcdr.server_startup',  # 等同于ServerEvent.SERVER_STARTUP
        on_server_start,
        priority=100
    )

@new_thread
def set_tag_command(source: CommandSource):
    """处理设置称号命令"""
    if not isinstance(source, PlayerCommandSource):
        source.reply('§c只有玩家可以使用此命令')
        return
    
    # 手动解析命令参数
    args = source.get_info().content.split()
    if len(args) < 3:
        source.reply('§c用法: !!nametag set <称号内容>')
        return
    
    player = source.player
    raw_tag = ' '.join(args[2:])
    processed_tag = raw_tag.replace('&', '§')
    
    if '§g' in processed_tag:
        if not config.enable_gradient:
            source.reply('§c渐变功能已被管理员禁用')
            return
        processed_tag = convert_to_gradient(processed_tag.replace('§g', '<gradient>') + '</gradient>')
    
    if len(processed_tag) > config.max_length:
        source.reply(f'§c称号过长（最大{config.max_length}字符）')
        return
    
    NameTagManager().set_tag(player, processed_tag)
    source.reply(RTextList('§a称号已更新：', processed_tag))

@new_thread
def set_color_command(source: CommandSource):
    """处理颜色设置命令"""
    if not isinstance(source, PlayerCommandSource):
        source.reply('§c只有玩家可以使用此命令')
        return
    
    # 手动解析命令参数
    args = source.get_info().content.split()
    if len(args) < 3:
        source.reply('§c用法: !!nametag color <颜色>')
        return
    
    color = args[2]
    if color not in config.allowed_colors:
        source.reply(f'§c不支持的颜色，可用颜色：{", ".join(config.allowed_colors)}')
        return
    
    player = source.player
    manager = NameTagManager()
    current_tag = manager.get_tag(player) or ''
    clean_tag = re.sub(r'§[0-9a-f]', '', current_tag)
    new_tag = COLOR_MAP.get(color, '') + clean_tag
    
    if len(new_tag) > config.max_length:
        source.reply(f'§c添加颜色后超过长度限制（最大{config.max_length}字符）')
        return
    
    manager.set_tag(player, new_tag)
    source.reply(RTextList('§a颜色已应用！当前称号：', new_tag))

@new_thread
def set_preset_command(source: CommandSource):
    """设置渐变预设"""
    if not isinstance(source, PlayerCommandSource):
        source.reply('§c只有玩家可以使用此命令')
        return
    
    # 手动解析命令参数
    args = source.get_info().content.split()
    if len(args) < 3:
        source.reply('§c用法: !!nametag preset <预设名>')
        return
    
    preset = args[2]
    if preset not in GRADIENT_PRESETS:
        source.reply(f'§c无效预设，可用预设：{", ".join(GRADIENT_PRESETS.keys())}')
        return
    
    config.gradient_preset = preset
    config.save()
    source.reply(f'§a渐变预设已设置为：{preset}')

@new_thread
def preview_command(source: CommandSource):
    """预览称号效果"""
    if not isinstance(source, PlayerCommandSource):
        source.reply('§c只有玩家可以预览称号')
        return
    
    sample_text = '示例称号'
    if config.enable_gradient:
        preview_text = convert_to_gradient(f'<gradient>{sample_text}</gradient>')
    else:
        preview_text = sample_text
    
    source.reply(RTextList('§7[预览] §o', preview_text))