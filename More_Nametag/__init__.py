from mcdreforged.api.all import *
from mcdreforged.api.types import Info
import json
import os
import re

# 插件的元数据
METADATA = {
    'id': 'advanced_title_plugin',
    'version': '2.0.0',
    'name': 'AdvancedTitlePlugin',
    'description': '支持渐变和多颜色的高级MCDR称号插件',
    'author': 'YourName',
    'link': '',
    'dependencies': {
        'mcdreforged': '>=2.0.0'
    }
}

class AdvancedTitleData:
    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.data_path = os.path.join(self.server.get_data_folder(), 'player_data.json')
        self.config_path = os.path.join(self.server.get_data_folder(), 'titles.json')
        self.player_data = {}
        self.title_config = {}

        if not os.path.exists(self.server.get_data_folder()):
            os.makedirs(self.server.get_data_folder())
        self.load_data()
        self.load_config()

    def load_data(self):
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.player_data = json.load(f)
            else:
                self.player_data = {}
                self.save_data()
        except Exception as e:
            self.server.logger.error(f"加载玩家数据失败: {e}")
            self.player_data = {}

    def save_data(self):
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.player_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存玩家数据失败: {e}")

    def load_config(self):
        # 默认配置包含各种高级效果示例
        default_config = {
            "default": {
                "name": "<gradient:gray:dark_gray>[新手]</gradient>",
                "permission": "adv_title.title.default",
                "description": "默认称号"
            },
            "vip": {
                "name": "<gradient:gold:yellow>✨ VIP玩家 ✨</gradient>",
                "permission": "adv_title.title.vip",
                "description": "VIP会员专属称号"
            },
            "rainbow": {
                "name": "<gradient:red:gold:yellow:green:aqua:blue:dark_purple>⚡ 彩虹战士 ⚡</gradient>",
                "permission": "adv_title.title.rainbow",
                "description": "七彩渐变效果"
            },
            "fire": {
                "name": "<gradient:red:orange:yellow>🔥 火焰使者 🔥</gradient>",
                "permission": "adv_title.title.fire",
                "description": "火焰渐变效果"
            },
            "ocean": {
                "name": "<gradient:dark_aqua:aqua:blue>🌊 海洋守护者 🌊</gradient>",
                "permission": "adv_title.title.ocean",
                "description": "海洋渐变效果"
            },
            "custom_template": {
                "name": "<gradient:#COLOR1#:#COLOR2#:#COLOR3#>你的文本</gradient>",
                "permission": "adv_title.title.custom",
                "description": "自定义渐变模板",
                "template": True
            }
        }
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.title_config = json.load(f)
            else:
                self.title_config = default_config
                self.save_config()
        except Exception as e:
            self.server.logger.error(f"加载称号配置失败: {e}")
            self.title_config = default_config

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.title_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存称号配置失败: {e}")

    def get_player_titles(self, player):
        return self.player_data.get(player, {}).get('titles', [])

    def get_current_title(self, player):
        return self.player_data.get(player, {}).get('current', None)

    def grant_title(self, player, title_id):
        if player not in self.player_data:
            self.player_data[player] = {'titles': [], 'current': None}
        if title_id not in self.player_data[player]['titles']:
            self.player_data[player]['titles'].append(title_id)
            self.save_data()
            return True
        return False

    def revoke_title(self, player, title_id):
        if player in self.player_data and title_id in self.player_data[player]['titles']:
            self.player_data[player]['titles'].remove(title_id)
            if self.get_current_title(player) == title_id:
                self.player_data[player]['current'] = None
            self.save_data()
            return True
        return False

    def set_current_title(self, player, title_id):
        if player in self.player_data and title_id in self.player_data[player]['titles']:
            self.player_data[player]['current'] = title_id
            self.save_data()
            return True
        return False

    def create_custom_title(self, title_id, display_text, colors):
        """
        创建自定义渐变称号
        colors: 颜色列表，如 ['red', 'gold', 'yellow'] 或 ['#FF0000', '#00FF00']
        """
        if len(colors) < 2:
            colors = ['gray', 'white']  # 默认颜色
        
        gradient_colors = ":".join(colors)
        custom_title = f"<gradient:{gradient_colors}>{display_text}</gradient>"
        
        # 添加到配置
        self.title_config[title_id] = {
            "name": custom_title,
            "permission": f"adv_title.title.{title_id}",
            "description": f"自定义称号: {display_text}",
            "custom": True
        }
        self.save_config()
        return custom_title

def on_load(server: PluginServerInterface, old):
    global title_data
    title_data = AdvancedTitleData(server)
    server.register_help_message('!!title', '显示高级称号系统帮助')
    build_command(server)

def build_command(server: PluginServerInterface):
    # 构建更强大的命令树
    server.register_command(
        Literal('!!title').\
        then(
            Literal('list').runs(lambda src: list_titles(src))
        ).\
        then(
            Literal('current').runs(lambda src: show_current_title(src))
        ).\
        then(
            Literal('use').\
            then(
                Text('title_id').runs(lambda src, ctx: use_title(src, ctx))
            )
        ).\
        then(
            Literal('preview').\
            then(
                Text('title_id').runs(lambda src, ctx: preview_title(src, ctx))
            )
        ).\
        then(
            Literal('create').\
            requires(lambda src: src.has_permission(3)).\
            then(
                Text('title_id').\
                then(
                    GreedyText('display_text').runs(lambda src, ctx: create_custom_title_cmd(src, ctx))
                )
            )
        ).\
        then(
            Literal('grant').\
            requires(lambda src: src.has_permission(3)).\
            then(
                Text('player').\
                then(
                    Text('title_id').runs(lambda src, ctx: grant_title_cmd(src, ctx))
                )
            )
        ).\
        then(
            Literal('revoke').\
            requires(lambda src: src.has_permission(3)).\
            then(
                Text('player').\
                then(
                    Text('title_id').runs(lambda src, ctx: revoke_title_cmd(src, ctx))
                )
            )
        )
    )

def create_custom_title_cmd(source: CommandSource, context: dict):
    """创建自定义渐变称号 - 完整版本"""
    title_id = context['title_id']
    full_text = context.get('display_text', '')

    # 解析参数：文本和颜色
    parts = full_text.split()
    if not parts:
        display_text = '称号'
        colors = ['red', 'gold', 'yellow']
    else:
        display_text = parts[0]
        colors = parts[1:] if len(parts) > 1 else ['red', 'gold', 'yellow']

    # 创建自定义称号
    created_title = title_data.create_custom_title(title_id, display_text, colors)

    source.reply('§a✅ 自定义称号创建成功！§r')
    source.reply(f'§7称号ID: §e{title_id}§r')
    source.reply('§7显示文本: §e{}§r'.format(display_text))
    source.reply('§7使用颜色: §e{}§r'.format(' → '.join(colors)))
    source.reply('§7效果预览:§r')
    source.reply(RText(created_title))
    source.reply('§7使用 §e!!title grant <玩家> {} §7来授予这个称号§r'.format(title_id))

def list_titles(source: CommandSource):
    if not source.is_player:
        source.reply('只有玩家才能使用这个命令。')
        return

    player = source.player
    titles = title_data.get_player_titles(player)
    if not titles:
        source.reply('你还没有任何称号！使用 !!title create 创建或请管理员授予。')
        return

    reply_text = '§6=== 你拥有的称号 ===§r\n'
    for title_id in titles:
        title_info = title_data.title_config.get(title_id, {})
        display_name = title_info.get('name', title_id)
        description = title_info.get('description', '')
        current = " §a✓ (当前佩戴)§r" if title_data.get_current_title(player) == title_id else ""
        
        # 使用MiniMessage发送带格式的称号名称
        source.reply(f"§7ID: §e{title_id}§r")
        source.reply(RText(display_name))  # 这里会渲染MiniMessage格式
        if description:
            source.reply(f"§7描述: §f{description}§r")
        source.reply(f"§7状态: {'§a已佩戴' if current else '§7未佩戴'}§r")
        source.reply('§8----------------§r')

def show_current_title(source: CommandSource):
    if not source.is_player:
        source.reply('只有玩家才能使用这个命令。')
        return

    player = source.player
    current_title_id = title_data.get_current_title(player)
    if current_title_id:
        title_info = title_data.title_config.get(current_title_id, {})
        display_name = title_info.get('name', current_title_id)
        source.reply('§6当前佩戴的称号:§r')
        source.reply(RText(display_name))  # 渲染MiniMessage格式
        source.reply(f'§7ID: {current_title_id}§r')
    else:
        source.reply('你当前没有佩戴任何称号。')

def preview_title(source: CommandSource, context: dict):
    """预览称号效果"""
    title_id = context['title_id']
    title_info = title_data.title_config.get(title_id, {})
    
    if not title_info:
        source.reply(f'§c错误: 称号 §e{title_id}§c 不存在。§r')
        return
    
    display_name = title_info.get('name', title_id)
    source.reply('§6称号预览:§r')
    source.reply(RText(display_name))
    source.reply(f'§7在聊天中显示: §r{RText(display_name + " " + source.name)}')

def use_title(source: CommandSource, context: dict):
    if not source.is_player:
        source.reply('只有玩家才能使用这个命令。')
        return

    player = source.player
    title_id = context['title_id']

    if title_id not in title_data.get_player_titles(player):
        source.reply(f'§c错误: 你没有称号 §e{title_id}§c。§r')
        return

    title_info = title_data.title_config.get(title_id, {})
    permission_node = title_info.get('permission')
    
    if permission_node and not source.has_permission(permission_node):
        source.reply(f'§c错误: 你没有权限使用称号 §e{title_id}§c。§r')
        return

    if title_data.set_current_title(player, title_id):
        display_name = title_info.get('name', title_id)
        source.reply('§a已成功切换称号至:§r')
        source.reply(RText(display_name))
    else:
        source.reply('§c切换称号失败！§r')

def create_custom_title_cmd(source: CommandSource, context: dict):
    """创建自定义渐变称号"""
    title_id = context['title_id']
    display_text = context['display_text']
    colors_text = context.get('colors', 'red gold yellow')
    
    # 解析颜色参数
    colors = colors_text.split()
    if len(colors) < 2:
        colors = ['red', 'gold', 'yellow']  # 默认彩虹色
    
    # 创建自定义称号
    created_title = title_data.create_custom_title(title_id, display_text, colors)
    
    source.reply('§a✅ 自定义称号创建成功！§r')
    source.reply(f'§7称号ID: §e{title_id}§r')
    source.reply('§7效果预览:§r')
    source.reply(RText(created_title))
    source.reply('§7使用 §e!!title grant <玩家> {} §7来授予这个称号§r'.format(title_id))

def grant_title_cmd(source: CommandSource, context: dict):
    player = context['player']
    title_id = context['title_id']

    if title_id not in title_data.title_config:
        source.reply(f'§c错误: 称号 §e{title_id}§c 不存在。§r')
        return

    if title_data.grant_title(player, title_id):
        title_info = title_data.title_config.get(title_id, {})
        display_name = title_info.get('name', title_id)
        source.reply(f'§a已成功授予玩家 §e{player}§a 称号:§r')
        source.reply(RText(display_name))
    else:
        source.reply(f'§c玩家 §e{player}§c 已经拥有称号 §e{title_id}§c。§r')

def revoke_title_cmd(source: CommandSource, context: dict):
    player = context['player']
    title_id = context['title_id']

    if title_data.revoke_title(player, title_id):
        source.reply(f'§a已成功收回玩家 §e{player}§a 的称号 §e{title_id}§a。§r')
    else:
        source.reply(f'§c玩家 §e{player}§c 并不拥有称号 §e{title_id}§c。§r')

# 监听聊天事件，使用MiniMessage渲染称号
@new_thread('AdvancedTitleChat')
def on_user_info(server: PluginServerInterface, info: Info):
    if info.is_user and info.content.startswith('<') and '>' in info.content:
        try:
            player_name, message = info.content[1:].split('>', 1)
            current_title_id = title_data.get_current_title(player_name)
            
            if current_title_id:
                title_info = title_data.title_config.get(current_title_id, {})
                title_display = title_info.get('name', current_title_id)
                
                # 使用MiniMessage格式构建聊天信息
                formatted_message = RTextList(
                    RText(title_display),  # 渲染渐变称号
                    " ",
                    RText(player_name),
                    RText(message)
                )
                
                info.cancel()
                server.say(formatted_message)
                
        except Exception as e:
            server.logger.error(f"处理聊天信息时出错: {e}")

# 添加玩家加入时授予默认称号
def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    # 如果玩家没有数据，授予默认称号
    if player not in title_data.player_data:
        title_data.grant_title(player, 'default')
        server.tell(player, '§a欢迎！你已获得默认称号，使用 §e!!title list §a查看！§r')