from mcdreforged.api.all import *
import json
import os

class TitleManager:
    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.data_folder = server.get_data_folder()
        self.player_data_path = os.path.join(self.data_folder, 'player_data.json')
        self.titles_path = os.path.join(self.data_folder, 'titles.json')

        os.makedirs(self.data_folder, exist_ok=True)
        self.load_data()

    def load_data(self):
        # 加载玩家数据
        try:
            if os.path.exists(self.player_data_path):
                with open(self.player_data_path, 'r', encoding='utf-8') as f:
                    self.player_data = json.load(f)
            else:
                self.player_data = {}
        except Exception as e:
            self.server.logger.error(f"加载玩家数据失败: {e}")
            self.player_data = {}

        # 加载称号配置
        try:
            if os.path.exists(self.titles_path):
                with open(self.titles_path, 'r', encoding='utf-8') as f:
                    self.titles = json.load(f)
            else:
                # 默认称号配置
                self.titles = {
                    "vip": {"display": "§6[VIP]", "permission": "more_nametag.title.vip"},
                    "default": {"display": "§7[玩家]", "permission": "more_nametag.title.default"}
                }
                self.save_titles()
        except Exception as e:
            self.server.logger.error(f"加载称号配置失败: {e}")
            self.titles = {}

    def save_player_data(self):
        try:
            with open(self.player_data_path, 'w', encoding='utf-8') as f:
                json.dump(self.player_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存玩家数据失败: {e}")

    def save_titles(self):
        try:
            with open(self.titles_path, 'w', encoding='utf-8') as f:
                json.dump(self.titles, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存称号配置失败: {e}")

    def grant_title(self, player: str, title_id: str) -> bool:
        if title_id not in self.titles:
            return False

        if player not in self.player_data:
            self.player_data[player] = {"available_titles": [], "current_title": None}

        if title_id not in self.player_data[player]["available_titles"]:
            self.player_data[player]["available_titles"].append(title_id)
            self.save_player_data()
            return True
        return False

    def revoke_title(self, player: str, title_id: str) -> bool:
        if player in self.player_data and title_id in self.player_data[player]["available_titles"]:
            self.player_data[player]["available_titles"].remove(title_id)
            if self.player_data[player]["current_title"] == title_id:
                self.player_data[player]["current_title"] = None
            self.save_player_data()
            return True
        return False

    def set_current_title(self, player: str, title_id: str) -> bool:
        if player in self.player_data and title_id in self.player_data[player]["available_titles"]:
            self.player_data[player]["current_title"] = title_id
            self.save_player_data()
            self.update_player_display(player)
            return True
        return False

    def remove_current_title(self, player: str) -> bool:
        if player in self.player_data:
            self.player_data[player]["current_title"] = None
            self.save_player_data()
            self.update_player_display(player)
            return True
        return False

    def update_player_display(self, player: str):
        current_title = self.player_data.get(player, {}).get("current_title")
        if current_title:
            title_display = self.titles[current_title]["display"]
            display_name = f"{title_display} {player}"
        else:
            display_name = player

        # 更新TAB列表显示
        self.server.execute(f"team modify nametag_{player} prefix \"\"")
        self.server.execute(f"team modify nametag_{player} suffix \"\"")
        self.server.execute(f"team join nametag_{player} {player}")

        # 更新头顶显示
        self.server.execute(f"team modify nametag_{player} displayName \"{display_name}\"")
        self.server.execute(f"team modify nametag_{player} prefix \"{display_name} \"")

title_manager = None

def on_load(server: PluginServerInterface, old):
    global title_manager
    title_manager = TitleManager(server)

    server.register_help_message('!!title', '称号系统 - 使用!!title help查看帮助')
    build_commands(server)

    # 注册事件监听
    server.register_event_listener('mcdreforged.api.events.PlayerJoinedEvent', on_player_joined)
    server.register_event_listener('mcdreforged.api.events.PlayerLeftEvent', on_player_left)

def on_player_joined(server: PluginServerInterface, player: str):
    if player in title_manager.player_data:
        title_manager.update_player_display(player)

def on_player_left(server: PluginServerInterface, player: str):
    pass

def build_commands(server: PluginServerInterface):
    # 主命令
    title_command = Literal('!!title').runs(show_help)

    # 玩家命令
    title_command.then(
        Literal('list').runs(list_titles)
    ).then(
        Literal('use').then(
            Text('title_id').runs(use_title)
        )
    ).then(
        Literal('remove').runs(remove_title)
    ).then(
        Literal('help').runs(show_help)
    )

    # 管理员命令
    admin_node = Literal('grant').then(
        Text('player').then(
            Text('title_id').runs(grant_title)
        )
    ).then(
        Literal('revoke').then(
            Text('player').then(
                Text('title_id').runs(revoke_title)
            )
        )
    ).then(
        Literal('create').then(
            Text('title_id').then(
                Text('display').runs(create_title)
            )
        )
    )

    # 添加权限检查
    title_command.then(
        admin_node.requires(
            lambda src: src.has_permission(3),
            failure_message_getter=lambda: "§c需要管理员权限(3级)才能使用此命令"
        )
    )

    server.register_command(title_command)
def show_help(src: CommandSource):
    help_msg = [
        "§6===== 称号系统帮助 =====",
        "§a!!title§r - 显示当前称号",
        "§a!!title list§r - 列出所有可用称号",
        "§a!!title use <称号ID>§r - 使用指定称号",
        "§a!!title remove§r - 移除当前称号",
        "§6管理员命令:",
        "§b!!title grant <玩家> <称号ID>§r - 授予玩家称号",
        "§b!!title revoke <玩家> <称号ID>§r - 收回玩家称号",
        "§b!!title create <称号ID> <显示文本>§r - 创建新称号"
    ]
    src.reply("\n".join(help_msg))

def list_titles(src: CommandSource):
    player = src.player
    if player not in title_manager.player_data:
        src.reply("§c你还没有任何称号")
        return

    available_titles = title_manager.player_data[player]["available_titles"]
    if not available_titles:
        src.reply("§c你还没有任何称号")
        return

    src.reply("§a你拥有的称号:")
    for title_id in available_titles:
        title_info = title_manager.titles[title_id]
        src.reply(f"  §e{title_id}§r: {title_info['display']}")

def use_title(src: CommandSource, ctx):
    player = src.player
    title_id = ctx['title_id']
    if title_manager.set_current_title(player, title_id):
        src.reply(f"§a已切换称号为: {title_manager.titles[title_id]['display']}")
    else:
        src.reply("§c切换称号失败，你可能没有这个称号")

def remove_title(src: CommandSource):
    player = src.player
    if title_manager.remove_current_title(player):
        src.reply("§a已移除当前称号")
    else:
        src.reply("§c你当前没有佩戴称号")

def grant_title(src: CommandSource, ctx):
    player = ctx['player']
    title_id = ctx['title_id']
    if title_manager.grant_title(player, title_id):
        src.reply(f"§a已授予玩家 {player} 称号 {title_id}")
    else:
        src.reply(f"§c授予称号失败，玩家可能已经拥有该称号")

def revoke_title(src: CommandSource, ctx):
    player = ctx['player']
    title_id = ctx['title_id']
    if title_manager.revoke_title(player, title_id):
        src.reply(f"§a已收回玩家 {player} 的称号 {title_id}")
    else:
        src.reply(f"§c收回称号失败，玩家可能没有该称号")

def create_title(src: CommandSource, ctx):
    title_id = ctx['title_id']
    display = ctx['display']

    if title_id in title_manager.titles:
        src.reply(f"§c称号 {title_id} 已存在")
        return

    title_manager.titles[title_id] = {
        "display": display,
        "permission": f"more_nametag.title.{title_id}"
    }
    title_manager.save_titles()
    src.reply(f"§a已创建新称号 {title_id}: {display}")