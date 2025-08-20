from mcdreforged.api.decorator import new_thread
from mcdreforged.api.command import Literal, Text
from mcdreforged.api.rtext import RTextList
from mcdreforged.api.types import PluginServerInterface, ServerInterface, Info, CommandSource, PlayerCommandSource
from typing import List, Dict, Optional
import json
import os
import re

# 常量定义
CONFIG_PATH = os.path.join('config', 'more_nametag.json')
DATA_PATH = os.path.join('config', 'nametag_data.json')

class Config:
    """插件配置类"""
    def __init__(self):
        self.admin_permission_level = 3
        self.max_length = 16
        self.presets = {
            'vip': '§6[VIP] §f{player}',
            'mod': '§2[MOD] §f{player}',
            'admin': '§4[ADMIN] §f{player}'
        }

    @classmethod
    def load(cls):
        """加载配置文件"""
        if not os.path.exists(CONFIG_PATH):
            return cls()
        try:
            with open(CONFIG_PATH, 'r', encoding='utf8') as f:
                data = json.load(f)
                config = cls()
                config.admin_permission_level = data.get('admin_permission_level', config.admin_permission_level)
                config.max_length = data.get('max_length', config.max_length)
                config.presets = data.get('presets', config.presets)
                return config
        except:
            return cls()

    def save(self):
        """保存配置文件"""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf8') as f:
            json.dump({
                'admin_permission_level': self.admin_permission_level,
                'max_length': self.max_length,
                'presets': self.presets
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

    def remove_tag(self, player):
        """移除玩家称号"""
        if player in self.data:
            del self.data[player]
            self.save()
            return True
        return False

def build_help_message():
    """构建帮助消息"""
    return RTextList(
        '!!nametag set <玩家> <称号> - 设置玩家称号\n',
        '!!nametag remove <玩家> - 移除玩家称号\n',
        '!!nametag preset <玩家> <预设> - 应用预设称号\n',
        '!!nametag preset list - 列出所有预设\n',
        '!!nametag preset add <名称> <内容> - 添加新预设 (需要level 4)\n',
        '!!nametag preset remove <名称> - 删除预设 (需要level 4)'
    )

# 全局配置实例
config = Config.load()

def on_player_joined(server: ServerInterface, player: str, info: Info):
    """玩家加入事件处理"""
    if (tag := NameTagManager().get_tag(player)) is not None:
        server.say(RTextList(f'§a玩家 {player} 已加载称号：', tag))
        server.execute(f'team modify nametag suffix {{"text":" {tag}"}}')

def on_load(server: PluginServerInterface, prev_module):
    """插件加载入口"""
    NameTagManager().load()

    # 注册帮助消息
    server.register_help_message('!!nametag', '玩家称号管理')

    # 构建命令树
    nametag_command = Literal('!!nametag').requires(
        lambda src: src.has_permission(config.admin_permission_level)
    ).runs(lambda src: src.reply(build_help_message()))

    # 设置称号命令
    set_command = Literal('set').then(
        Text('player').then(
            Text('tag').runs(set_tag_command)
        )
    )

    # 移除称号命令
    remove_command = Literal('remove').then(
        Text('player').runs(remove_tag_command)
    )

    # 预设管理命令
    preset_command = Literal('preset').then(
        Text('player').then(
            Text('preset_name').runs(preset_apply_command)
        )
    ).then(
        Literal('list').runs(preset_list_command)
    ).then(
        Literal('add').requires(
            lambda src: src.has_permission(4)
        ).then(
            Text('preset_name').then(
                Text('preset_content').runs(preset_add_command)
            )
        )
    ).then(
        Literal('remove').requires(
            lambda src: src.has_permission(4)
        ).then(
            Text('preset_name').runs(preset_remove_command)
        )
    )

    # 注册主命令
    nametag_command.then(set_command).then(remove_command).then(preset_command)
    server.register_command(nametag_command)

    # 注册玩家加入事件
    server.register_event_listener(
        'mcdr.player_joined',
        on_player_joined
    )

@new_thread
def set_tag_command(source: CommandSource, ctx: dict):
    """设置玩家称号"""
    player = ctx['player']
    tag = ctx['tag']

    # 验证称号长度
    if len(tag) > config.max_length:
        source.reply(f'§c称号过长（最大{config.max_length}字符）')
        return

    NameTagManager().set_tag(player, tag)
    source.reply(RTextList(
        f'§a已为玩家 {player} 设置称号：',
        tag
    ))

@new_thread
def remove_tag_command(source: CommandSource, ctx: dict):
    """移除玩家称号"""
    player = ctx['player']
    if NameTagManager().remove_tag(player):
        source.reply(f'§a已移除玩家 {player} 的称号')
    else:
        source.reply(f'§c玩家 {player} 没有设置称号')

@new_thread
def preset_apply_command(source: CommandSource, ctx: dict):
    """应用预设称号"""
    player = ctx['player']
    preset_name = ctx['preset_name']

    if preset_name not in config.presets:
        source.reply(f'§c无效预设，可用预设：{", ".join(config.presets.keys())}')
        return

    tag = config.presets[preset_name].replace('{player}', player)
    NameTagManager().set_tag(player, tag)
    source.reply(RTextList(
        f'§a已为玩家 {player} 应用预设 {preset_name}：',
        tag
    ))

@new_thread
def preset_list_command(source: CommandSource):
    """列出所有预设"""
    if not config.presets:
        source.reply('§c当前没有预设称号')
        return

    msg = RTextList('§a可用预设称号：\n')
    for name, template in config.presets.items():
        msg.append(f'§6{name}§f: {template}\n')
    source.reply(msg)

@new_thread
def preset_add_command(source: CommandSource, ctx: dict):
    """添加新预设"""
    preset_name = ctx['preset_name']
    preset_content = ctx['preset_content']

    if preset_name in config.presets:
        source.reply(f'§c预设 {preset_name} 已存在')
        return

    config.presets[preset_name] = preset_content
    config.save()
    source.reply(f'§a已添加预设 {preset_name}：{preset_content}')

@new_thread
def preset_remove_command(source: CommandSource, ctx: dict):
    """删除预设"""
    preset_name = ctx['preset_name']
    if preset_name not in config.presets:
        source.reply(f'§c预设 {preset_name} 不存在')
        return
    
    del config.presets[preset_name]
    config.save()
    source.reply(f'§a已删除预设 {preset_name}')