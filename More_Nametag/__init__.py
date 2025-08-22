from mcdreforged.api.all import *
import json
import os

class TitleManager:
    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.data_folder = server.get_data_folder()
        self.player_data_path = os.path.join(self.data_folder, 'player_data.json')
        self.load_data()

    def load_data(self):
        try:
            if os.path.exists(self.player_data_path):
                with open(self.player_data_path, 'r', encoding='utf-8') as f:
                    self.player_data = json.load(f)
            else:
                self.player_data = {}
        except Exception as e:
            self.server.logger.error(f"加载玩家数据失败: {e}")
            self.player_data = {}

    def save_data(self):
        try:
            with open(self.player_data_path, 'w', encoding='utf-8') as f:
                json.dump(self.player_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.server.logger.error(f"保存玩家数据失败: {e}")

    def grant_title(self, player: str, title_id: str, display_text: str) -> bool:
        if player not in self.player_data:
            self.player_data[player] = {"titles": {}, "current": None}

        if title_id not in self.player_data[player]["titles"]:
            self.player_data[player]["titles"][title_id] = display_text
            self.save_data()
            return True
        return False

    def revoke_title(self, player: str, title_id: str) -> bool:
        if player in self.player_data and title_id in self.player_data[player]["titles"]:
            del self.player_data[player]["titles"][title_id]
            if self.player_data[player]["current"] == title_id:
                self.player_data[player]["current"] = None
            self.save_data()
            return True
        return False

    def set_current_title(self, player: str, title_id: str) -> bool:
        if player in self.player_data and title_id in self.player_data[player]["titles"]:
            self.player_data[player]["current"] = title_id
            self.save_data()
            self.update_display(player)
            return True
        return False

    def remove_current_title(self, player: str) -> bool:
        if player in self.player_data:
            self.player_data[player]["current"] = None
            self.save_data()
            self.update_display(player)
            return True
        return False

    def update_display(self, player: str):
        current = self.player_data.get(player, {}).get("current")
        if current:
            display_text = self.player_data[player]["titles"][current]
            display_name = f"{display_text} {player}"
        else:
            display_name = player

        self.server.execute(f"team modify nametag_{player} prefix \"\"")
        self.server.execute(f"team modify nametag_{player} suffix \"\"")
        self.server.execute(f"team join nametag_{player} {player}")
        self.server.execute(f"team modify nametag_{player} displayName \"{display_name}\"")
        self.server.execute(f"team modify nametag_{player} prefix \"{display_name} \"")

title_manager = None

def on_load(server: PluginServerInterface, old):
    global title_manager
    title_manager = TitleManager(server)

    server.register_help_message('!!title', '称号系统 - 使用!!title help查看帮助')
    build_commands(server)

    server.register_event_listener('mcdreforged.api.events.PlayerJoinedEvent', on_player_joined)

def on_player_joined(server: PluginServerInterface, player: str):
    if player in title_manager.player_data:
        title_manager.update_display(player)

def build_commands(server: PluginServerInterface):
    def admin_check(src: CommandSource):
        return src.has_permission(3) if src.is_player else True

    server.register_command(
        Literal('!!title').runs(show_help).then(
            Literal('list').runs(list_titles)
        ).then(
            Literal('use').then(
                Text('title_id').runs(use_title)
            )
        ).then(
            Literal('remove').runs(remove_title)
        ).then(
            Literal('grant').requires(admin_check).then(
                Text('player').then(
                    Text('title_id').then(
                        GreedyText('display_text').runs(grant_title)
                    )
                )
            )
        ).then(
            Literal('revoke').requires(admin_check).then(
                Text('player').then(
                    Text('title_id').runs(revoke_title)
                )
            )
        )
    )

def show_help(src: CommandSource):
    help_msg = [
        "§6===== 称号系统帮助 =====",
        "§a!!title§r - 显示当前称号",
        "§a!!title list§r - 列出所有称号",
        "§a!!title use <称号ID>§r - 使用称号",
        "§a!!title remove§r - 移除当前称号",
        "§6管理员命令:",
        "§b!!title grant <玩家> <称号ID> <显示文本>§r - 直接授予称号",
        "§b!!title revoke <玩家> <称号ID>§r - 收回称号"
    ]
    src.reply("\n".join(help_msg))

def list_titles(src: CommandSource):
    player = src.player
    if player not in title_manager.player_data or not title_manager.player_data[player]["titles"]:
        src.reply("§c你还没有任何称号")
        return

    src.reply("§a你的称号列表:")
    for title_id, display in title_manager.player_data[player]["titles"].items():
        src.reply(f"  §e{title_id}§r: {display}")

def use_title(src: CommandSource, ctx):
    player = src.player
    title_id = ctx['title_id']
    if title_manager.set_current_title(player, title_id):
        display = title_manager.player_data[player]["titles"][title_id]
        src.reply(f"§a已切换称号为: {display}")
    else:
        src.reply("§c切换失败，没有这个称号")

def remove_title(src: CommandSource):
    player = src.player
    if title_manager.remove_current_title(player):
        src.reply("§a已移除当前称号")
    else:
        src.reply("§c你当前没有佩戴称号")

def grant_title(src: CommandSource, ctx):
    player = ctx['player']
    title_id = ctx['title_id']
    display_text = ctx['display_text']

    if title_manager.grant_title(player, title_id, display_text):
        src.reply(f"§a已授予玩家 {player} 称号: {display_text}")
    else:
        src.reply(f"§c玩家已拥有该称号ID")

def revoke_title(src: CommandSource, ctx):
    player = ctx['player']
    title_id = ctx['title_id']

    if title_manager.revoke_title(player, title_id):
        src.reply(f"§a已收回玩家 {player} 的称号 {title_id}")
    else:
        src.reply(f"§c玩家没有这个称号")