from mcdreforged.api.all import *
import json
import os
import time
from typing import Dict, List

METADATA = {
    'id': 'simple_title_plugin',
    'version': '1.0.0',
    'name': 'SimpleTitlePlugin',
    'description': '一个简单可用的MCDR称号插件',
    'author': 'MCDR Community',
    'dependencies': {
        'mcdreforged': '>=2.0.0'
    }
}

class TitleManager:
    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.data_dir = server.get_data_folder()
        self.player_file = os.path.join(self.data_dir, 'players.json')
        self.titles_file = os.path.join(self.data_dir, 'titles.json')
        self.config_file = os.path.join(self.data_dir, 'config.json')
        
        # 确保目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.players: Dict[str, dict] = {}
        self.titles: Dict[str, dict] = {}
        self.config: Dict[str, any] = {}
        
        self.load_all_data()

    def load_all_data(self):
        self.load_config()
        self.load_titles()
        self.load_players()

    def load_config(self):
        default_config = {
            "chat_format": "{} {}: {}",
            "enable_tab_display": True,
            "update_interval": 10,
            "default_title": "default"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = {**default_config, **json.load(f)}
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存配置失败: {e}")

    def load_titles(self):
        default_titles = {
            "default": {
                "display": "§7[村民]",
                "permission": "title.default",
                "description": "默认称号"
            },
            "vip": {
                "display": "§6[VIP]",
                "permission": "title.vip",
                "description": "VIP会员称号"
            },
            "hero": {
                "display": "§c[英雄]",
                "permission": "title.hero",
                "description": "英雄称号"
            }
        }
        
        if os.path.exists(self.titles_file):
            try:
                with open(self.titles_file, 'r', encoding='utf-8') as f:
                    self.titles = {**default_titles, **json.load(f)}
            except:
                self.titles = default_titles
        else:
            self.titles = default_titles
            self.save_titles()

    def save_titles(self):
        try:
            with open(self.titles_file, 'w', encoding='utf-8') as f:
                json.dump(self.titles, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存称号配置失败: {e}")

    def load_players(self):
        if os.path.exists(self.player_file):
            try:
                with open(self.player_file, 'r', encoding='utf-8') as f:
                    self.players = json.load(f)
            except:
                self.players = {}
        else:
            self.players = {}
            self.save_players()

    def save_players(self):
        try:
            with open(self.player_file, 'w', encoding='utf-8') as f:
                json.dump(self.players, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存玩家数据失败: {e}")

    def ensure_player(self, player_name: str) -> bool:
        if player_name not in self.players:
            self.players[player_name] = {
                'titles': ['default'],
                'current': 'default'
            }
            self.save_players()
            return True
        return False

    def get_player_titles(self, player_name: str) -> List[str]:
        self.ensure_player(player_name)
        return self.players[player_name].get('titles', [])

    def get_current_title(self, player_name: str) -> str:
        self.ensure_player(player_name)
        return self.players[player_name].get('current', 'default')

    def set_current_title(self, player_name: str, title_id: str) -> bool:
        if title_id in self.get_player_titles(player_name):
            self.players[player_name]['current'] = title_id
            self.save_players()
            self.update_player_display(player_name)
            return True
        return False

    def grant_title(self, player_name: str, title_id: str) -> bool:
        self.ensure_player(player_name)
        if title_id not in self.players[player_name]['titles']:
            self.players[player_name]['titles'].append(title_id)
            self.save_players()
            return True
        return False

    def revoke_title(self, player_name: str, title_id: str) -> bool:
        if player_name in self.players and title_id in self.players[player_name]['titles']:
            self.players[player_name]['titles'].remove(title_id)
            if self.get_current_title(player_name) == title_id:
                self.players[player_name]['current'] = 'default'
            self.save_players()
            self.update_player_display(player_name)
            return True
        return False

    def update_player_display(self, player_name: str):
        """更新玩家显示名称"""
        if not self.config.get("enable_tab_display", True):
            return
            
        current_title = self.get_current_title(player_name)
        title_display = self.titles.get(current_title, {}).get('display', '')
        
        # 简单的显示名称更新
        try:
            display_name = f"{title_display} {player_name}"
            # 使用MCDR的API执行命令
            self.server.execute(f'execute as {player_name} run data merge entity {player_name} {{CustomName:\'"{display_name}"\', CustomNameVisible:1b}}')
        except Exception as e:
            self.server.logger.debug(f"更新玩家显示名称失败: {e}")

    def format_chat_message(self, player_name: str, message: str) -> str:
        """格式化聊天消息"""
        current_title = self.get_current_title(player_name)
        title_display = self.titles.get(current_title, {}).get('display', '')
        chat_format = self.config.get("chat_format", "{} {}: {}")
        
        return chat_format.format(title_display, player_name, message)

# 全局变量
title_manager = None

def on_load(server: PluginServerInterface, old):
    global title_manager
    title_manager = TitleManager(server)
    
    server.register_help_message('!!title', '显示称号系统帮助')
    register_commands(server)
    
    # 启动定时更新任务
    start_update_task(server)

def register_commands(server: PluginServerInterface):
    """注册所有命令"""
    
    # 列表命令
    def list_titles(source: CommandSource):
        if not source.is_player:
            source.reply("§c只有玩家才能使用此命令")
            return
            
        player = source.player
        titles = title_manager.get_player_titles(player)
        
        if not titles:
            source.reply("§e你还没有任何称号")
            return
            
        source.reply("§6=== 你的称号 ===")
        current_title = title_manager.get_current_title(player)
        
        for title_id in titles:
            title_info = title_manager.titles.get(title_id, {})
            display = title_info.get('display', title_id)
            status = "§a✔" if title_id == current_title else "§7-"
            source.reply(f" {status} §r{display} §8(§7{title_id}§8)")
    
    # 使用命令
    def use_title(source: CommandSource, ctx: dict):
        if not source.is_player:
            source.reply("§c只有玩家才能使用此命令")
            return
            
        player = source.player
        title_id = ctx['title_id']
        
        if title_id not in title_manager.get_player_titles(player):
            source.reply(f"§c你没有称号: §e{title_id}")
            return
            
        if title_manager.set_current_title(player, title_id):
            title_display = title_manager.titles.get(title_id, {}).get('display', '')
            source.reply(f"§a已切换称号: {title_display}")
        else:
            source.reply("§c切换称号失败")
    
    # 授予命令
    def grant_title(source: CommandSource, ctx: dict):
        if not source.has_permission(3):
            source.reply("§c你需要至少3级权限")
            return
            
        player = ctx['player']
        title_id = ctx['title_id']
        
        if title_id not in title_manager.titles:
            source.reply(f"§c称号不存在: §e{title_id}")
            return
            
        if title_manager.grant_title(player, title_id):
            title_display = title_manager.titles.get(title_id, {}).get('display', '')
            source.reply(f"§a已授予玩家 §e{player} §a称号: {title_display}")
            
            # 如果玩家在线，立即更新显示
            if player in server.get_online_players():
                title_manager.update_player_display(player)
        else:
            source.reply(f"§c玩家 §e{player} §c已经拥有该称号")
    
    # 收回命令
    def revoke_title(source: CommandSource, ctx: dict):
        if not source.has_permission(3):
            source.reply("§c你需要至少3级权限")
            return
            
        player = ctx['player']
        title_id = ctx['title_id']
        
        if title_manager.revoke_title(player, title_id):
            source.reply(f"§a已收回玩家 §e{player} §a的称号: §e{title_id}")
        else:
            source.reply(f"§c玩家 §e{player} §c没有该称号")
    
    # 当前命令
    def current_title(source: CommandSource):
        if not source.is_player:
            source.reply("§c只有玩家才能使用此命令")
            return
            
        player = source.player
        title_id = title_manager.get_current_title(player)
        title_display = title_manager.titles.get(title_id, {}).get('display', '')
        source.reply(f"§6当前称号: §r{title_display} §8(§7{title_id}§8)")
    
    # 注册命令树
    server.register_command(
        Literal('!!title').
        then(Literal('list').runs(list_titles)).
        then(Literal('current').runs(current_title)).
        then(
            Literal('use').
            then(Text('title_id').runs(use_title))
        ).
        then(
            Literal('grant').
            then(
                Text('player').
                then(Text('title_id').runs(grant_title))
            )
        ).
        then(
            Literal('revoke').
            then(
                Text('player').
                then(Text('title_id').runs(revoke_title))
            )
        )
    )

def on_user_info(server: PluginServerInterface, info: Info):
    """处理聊天消息"""
    if info.is_user and info.content.startswith('<') and '>' in info.content:
        try:
            # 解析聊天消息
            parts = info.content[1:].split('>', 1)
            if len(parts) == 2:
                player_name, message = parts
                
                # 格式化聊天消息
                formatted_message = title_manager.format_chat_message(player_name, message)
                
                # 取消原消息并发送新消息
                info.cancel()
                server.say(formatted_message)
                
        except Exception as e:
            server.logger.debug(f"处理聊天消息时出错: {e}")

def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    """玩家加入时处理"""
    title_manager.ensure_player(player)
    # 延迟一下再更新显示，确保玩家完全进入
    server.schedule_task(2, lambda: title_manager.update_player_display(player))

@new_thread('TitleUpdater')
def start_update_task(server: PluginServerInterface):
    """启动定时更新任务"""
    interval = title_manager.config.get("update_interval", 10)
    while True:
        time.sleep(interval)
        try:
            for player in server.get_online_players():
                title_manager.update_player_display(player)
        except Exception as e:
            server.logger.debug(f"定时更新玩家显示时出错: {e}")

def on_unload(server: PluginServerInterface):
    """插件卸载时保存数据"""
    title_manager.save_players()