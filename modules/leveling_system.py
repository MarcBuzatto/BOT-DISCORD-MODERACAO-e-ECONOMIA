"""
Sistema de Níveis/XP
Desenvolvido por: MARKIZIN
https://ggmax.com.br/perfil/markizin002
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
from pathlib import Path
from datetime import datetime, timezone
import random
import hashlib
from modules.components_v2 import make_card, make_success, make_error, brand_footer, BrandedView

# ⚠️ PROTEÇÃO DE AUTORIA - NÃO REMOVER
_AUTHOR_CHECK = hashlib.md5(b"MARKIZIN").hexdigest()

LEVELING_FILE = Path("leveling.json")
_xp_cooldowns = {}


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _xp_for_level(level: int) -> int:
    """XP necessário para atingir um nível."""
    return 5 * (level ** 2) + 50 * level + 100


def _level_from_xp(xp: int) -> int:
    """Calcula o nível a partir do XP total."""
    level = 0
    while xp >= _xp_for_level(level):
        xp -= _xp_for_level(level)
        level += 1
    return level


def _xp_progress(xp: int) -> tuple:
    """Retorna (nível_atual, xp_no_nível, xp_necessário_para_próximo)."""
    level = 0
    remaining = xp
    while remaining >= _xp_for_level(level):
        remaining -= _xp_for_level(level)
        level += 1
    return level, remaining, _xp_for_level(level)


class LevelingSystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.data = self._load()
        self._dirty = False

    def _load(self) -> dict:
        if not LEVELING_FILE.exists():
            return {}
        try:
            return json.loads(LEVELING_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self):
        try:
            tmp = LEVELING_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
            tmp.replace(LEVELING_FILE)
            self._dirty = False
        except Exception as e:
            print(f"Erro ao salvar leveling: {e}")

    def flush(self):
        if self._dirty:
            self._save()

    def _ensure_user(self, guild_id: int, user_id: int) -> dict:
        gk = str(guild_id)
        uk = str(user_id)
        if gk not in self.data:
            self.data[gk] = {}
        if uk not in self.data[gk]:
            self.data[gk][uk] = {"xp": 0, "messages": 0}
        return self.data[gk][uk]

    def add_xp(self, guild_id: int, user_id: int, amount: int) -> tuple:
        """Adiciona XP e retorna (old_level, new_level)."""
        user = self._ensure_user(guild_id, user_id)
        old_level = _level_from_xp(user["xp"])
        user["xp"] += amount
        user["messages"] = user.get("messages", 0) + 1
        new_level = _level_from_xp(user["xp"])
        self._dirty = True
        return old_level, new_level

    def get_user(self, guild_id: int, user_id: int) -> dict:
        return self._ensure_user(guild_id, user_id)

    def get_leaderboard(self, guild_id: int, limit: int = 10) -> list:
        gk = str(guild_id)
        if gk not in self.data:
            return []
        users = [(int(uid), d.get("xp", 0)) for uid, d in self.data[gk].items()]
        users.sort(key=lambda x: x[1], reverse=True)
        return users[:limit]

    def get_rank(self, guild_id: int, user_id: int) -> int:
        gk = str(guild_id)
        if gk not in self.data:
            return 0
        users = sorted(self.data[gk].items(), key=lambda x: x[1].get("xp", 0), reverse=True)
        for i, (uid, _) in enumerate(users, 1):
            if int(uid) == user_id:
                return i
        return 0

    def reset_user(self, guild_id: int, user_id: int):
        gk = str(guild_id)
        uk = str(user_id)
        if gk in self.data and uk in self.data[gk]:
            self.data[gk][uk] = {"xp": 0, "messages": 0}
            self._dirty = True


class LevelingCommands(commands.Cog):
    def __init__(self, bot, leveling: LevelingSystem, config_manager):
        self.bot = bot
        self.leveling = leveling
        self.config_manager = config_manager
        # ⚠️ PROTEÇÃO DE AUTORIA
        if _AUTHOR_CHECK != "7e94cd9fff4a493ba6b9b2abcc38f3c0":
            raise RuntimeError("Falha de integridade")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        cfg = self.config_manager.get_guild_config(message.guild.id, "leveling")
        if not cfg.get("enabled", False):
            return

        # Verificar canais ignorados
        ignored = cfg.get("ignored_channels", [])
        if message.channel.id in ignored:
            return

        # Cooldown de XP (60s por padrão)
        cooldown = cfg.get("xp_cooldown", 60)
        now = _utcnow()
        key = (message.guild.id, message.author.id)
        last = _xp_cooldowns.get(key)
        if last and (now - last).total_seconds() < cooldown:
            return
        _xp_cooldowns[key] = now

        # Adicionar XP
        min_xp = cfg.get("xp_min", 15)
        max_xp = cfg.get("xp_max", 25)
        amount = random.randint(min_xp, max_xp)
        old_level, new_level = self.leveling.add_xp(message.guild.id, message.author.id, amount)

        # Level up! (channel notification — stays as embed)
        if new_level > old_level:
            notify_channel_id = cfg.get("notify_channel_id")
            channel = message.guild.get_channel(notify_channel_id) if notify_channel_id else message.channel

            msg_template = cfg.get("levelup_message", "{user} subiu para o **nivel {level}**")
            text = msg_template.format(user=message.author.mention, level=new_level)

            embed = discord.Embed(
                title="Level Up",
                description=text,
                color=cfg.get("levelup_color", 0xFFD700),
                timestamp=_utcnow()
            )
            embed.set_footer(text="Desenvolvido por MARKIZIN")

            try:
                await channel.send(embed=embed)
            except Exception:
                pass

            # Cargo por nível
            level_roles = cfg.get("level_roles", {})
            role_id = level_roles.get(str(new_level))
            if role_id:
                role = message.guild.get_role(role_id)
                if role:
                    try:
                        await message.author.add_roles(role, reason=f"Atingiu nível {new_level}")
                    except Exception:
                        pass

    @app_commands.command(name="rank", description="Veja seu nível e XP")
    @app_commands.describe(member="Membro para ver (opcional)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = self.leveling.get_user(interaction.guild.id, target.id)
        level, xp_current, xp_needed = _xp_progress(user["xp"])
        rank_pos = self.leveling.get_rank(interaction.guild.id, target.id)

        bar_filled = int((xp_current / xp_needed) * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)

        view = make_card(
            title=f"Perfil de {target.display_name}",
            description=f"`{bar}` {xp_current}/{xp_needed}",
            color=0x5865F2,
            fields=[
                ("Nível", f"**{level}**"),
                ("XP", f"**{user['xp']}** total"),
                ("Ranking", f"#{rank_pos}"),
                ("Progresso", f"`{bar}` {xp_current}/{xp_needed}"),
                ("Mensagens", f"{user.get('messages', 0)}"),
            ],
            thumbnail_url=target.display_avatar.url,
            author_id=interaction.user.id,
        )

        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="leaderboard", description="Top 10 membros com mais XP")
    async def leaderboard(self, interaction: discord.Interaction):
        top = self.leveling.get_leaderboard(interaction.guild.id, 10)
        if not top:
            view = make_error("Nenhum dado de XP ainda.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        lines = []
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for i, (uid, xp) in enumerate(top, 1):
            member = interaction.guild.get_member(uid)
            name = member.display_name if member else f"ID:{uid}"
            level = _level_from_xp(xp)
            medal = medals.get(i, f"**{i}.**")
            lines.append(f"{medal} {name} — Nível **{level}** ({xp:,} XP)")

        view = make_card(
            title="Ranking de Niveis",
            description="\n".join(lines),
            color=0xFFD700,
            author_id=interaction.user.id,
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="setlevel", description="Define o nível de um membro (admin)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(member="Membro", level="Nível desejado")
    async def setlevel(self, interaction: discord.Interaction, member: discord.Member, level: int):
        if level < 0:
            view = make_error("Nível não pode ser negativo.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Calcular XP total para o nível
        xp_total = sum(_xp_for_level(i) for i in range(level))
        user = self.leveling._ensure_user(interaction.guild.id, member.id)
        user["xp"] = xp_total
        self.leveling._dirty = True

        view = make_success(f"{member.mention} agora está no **nível {level}** ({xp_total:,} XP)")
        await interaction.response.send_message(view=view, ephemeral=True)


async def setup(bot: commands.Bot, config_manager):
    leveling = LevelingSystem(config_manager)

    @tasks.loop(seconds=60)
    async def _flush_loop():
        leveling.flush()

    @_flush_loop.before_loop
    async def _before():
        await bot.wait_until_ready()

    _flush_loop.start()
    await bot.add_cog(LevelingCommands(bot, leveling, config_manager))
    print("   [OK] Sistema de Niveis/XP carregado")
    return leveling
