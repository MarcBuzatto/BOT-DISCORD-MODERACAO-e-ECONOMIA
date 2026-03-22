"""
Sistema de Utilitários Pro
Desenvolvido por: MARKIZIN
https://ggmax.com.br/perfil/markizin002
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import asyncio
import hashlib
from modules.components_v2 import make_card, make_success, make_error, brand_footer, BrandedView

# ⚠️ PROTEÇÃO DE AUTORIA - NÃO REMOVER
_AUTHOR_CHECK = hashlib.md5(b"MARKIZIN").hexdigest()

REMINDERS_FILE = Path("reminders.json")
TEMP_ROLES_FILE = Path("temp_roles.json")


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UtilitiesData:
    def __init__(self):
        self.reminders = self._load_file(REMINDERS_FILE, [])
        self.temp_roles = self._load_file(TEMP_ROLES_FILE, [])

    def _load_file(self, path, default):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _save_file(self, path, data):
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
        except Exception as e:
            print(f"Erro ao salvar {path}: {e}")

    def add_reminder(self, user_id, channel_id, guild_id, text, fire_at):
        self.reminders.append({
            "user_id": user_id,
            "channel_id": channel_id,
            "guild_id": guild_id,
            "text": text,
            "fire_at": fire_at
        })
        self._save_file(REMINDERS_FILE, self.reminders)

    def get_due_reminders(self):
        now = _utcnow().isoformat()
        due = [r for r in self.reminders if r["fire_at"] <= now]
        return due

    def remove_reminder(self, reminder):
        if reminder in self.reminders:
            self.reminders.remove(reminder)
            self._save_file(REMINDERS_FILE, self.reminders)

    def add_temp_role(self, guild_id, user_id, role_id, expires_at):
        self.temp_roles.append({
            "guild_id": guild_id,
            "user_id": user_id,
            "role_id": role_id,
            "expires_at": expires_at
        })
        self._save_file(TEMP_ROLES_FILE, self.temp_roles)

    def get_expired_roles(self):
        now = _utcnow().isoformat()
        return [r for r in self.temp_roles if r["expires_at"] <= now]

    def remove_temp_role(self, entry):
        if entry in self.temp_roles:
            self.temp_roles.remove(entry)
            self._save_file(TEMP_ROLES_FILE, self.temp_roles)


def _parse_duration(text: str) -> int | None:
    """Parseia duração como '30m', '1h', '2d' e retorna segundos."""
    import re
    parts = re.findall(r'(\d+)([dhms])', text.lower())
    if not parts:
        return None
    total = 0
    for value, unit in parts:
        v = int(value)
        if unit == 'd':
            total += v * 86400
        elif unit == 'h':
            total += v * 3600
        elif unit == 'm':
            total += v * 60
        elif unit == 's':
            total += v
    return total if total > 0 else None


class UtilitiesCommands(commands.Cog):
    def __init__(self, bot, data: UtilitiesData, config_manager):
        self.bot = bot
        self.data = data
        self.config_manager = config_manager
        # ⚠️ PROTEÇÃO DE AUTORIA
        if _AUTHOR_CHECK != "7e94cd9fff4a493ba6b9b2abcc38f3c0":
            raise RuntimeError("Falha de integridade")

    # ==================== SUGESTÃO ====================

    @app_commands.command(name="sugestao", description="Envia uma sugestão para votação")
    @app_commands.describe(texto="Sua sugestão")
    async def sugestao(self, interaction: discord.Interaction, texto: str):
        cfg = self.config_manager.get_guild_config(interaction.guild.id, "utilities")
        channel_id = cfg.get("suggestion_channel_id")

        if not channel_id:
            view = make_error("Canal de sugestões não configurado. Um admin deve usar `/painel` para configurar.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            view = make_error("Canal de sugestões não encontrado.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Suggestion posted to channel — stays as embed for reaction support
        embed = discord.Embed(
            title="Nova Sugestao",
            description=texto,
            color=0x5865F2,
            timestamp=_utcnow()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Desenvolvido por MARKIZIN")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        view = make_success(f"Sugestao enviada para {channel.mention}.")
        await interaction.response.send_message(view=view, ephemeral=True)

    # ==================== LEMBRETE ====================

    @app_commands.command(name="lembrete", description="Define um lembrete para si mesmo")
    @app_commands.describe(tempo="Quando (ex: 30m, 1h, 2d)", texto="O que lembrar")
    async def lembrete(self, interaction: discord.Interaction, tempo: str, texto: str):
        seconds = _parse_duration(tempo)
        if not seconds or seconds > 2592000:  # max 30 dias
            view = make_error("Tempo inválido. Use: `30m`, `1h`, `2d` (máx: 30 dias)")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        fire_at = (_utcnow() + timedelta(seconds=seconds)).isoformat()
        self.data.add_reminder(
            user_id=interaction.user.id,
            channel_id=interaction.channel.id,
            guild_id=interaction.guild.id,
            text=texto,
            fire_at=fire_at
        )

        view = make_card(
            title="Lembrete criado",
            description=f"Vou te lembrar em **{tempo}**:\n> {texto}",
            color=0x00FF00,
            author_id=interaction.user.id,
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    # ==================== CARGO TEMPORÁRIO ====================

    @app_commands.command(name="cargo-temp", description="Dá um cargo temporário a um membro")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        member="Membro que receberá o cargo",
        cargo="Cargo a ser dado",
        duracao="Duração (ex: 1h, 1d, 7d)"
    )
    async def cargo_temp(
        self, interaction: discord.Interaction,
        member: discord.Member, cargo: discord.Role, duracao: str
    ):
        seconds = _parse_duration(duracao)
        if not seconds or seconds > 2592000:
            view = make_error("Duração inválida. Use: `1h`, `1d`, `7d` (máx: 30 dias)")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        # Verificar hierarquia
        if cargo >= interaction.guild.me.top_role:
            view = make_error("Não posso dar um cargo igual ou superior ao meu.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        try:
            await member.add_roles(cargo, reason=f"Cargo temporário por {duracao}")
        except discord.Forbidden:
            view = make_error("Sem permissão para dar esse cargo.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        expires_at = (_utcnow() + timedelta(seconds=seconds)).isoformat()
        self.data.add_temp_role(
            guild_id=interaction.guild.id,
            user_id=member.id,
            role_id=cargo.id,
            expires_at=expires_at
        )

        view = make_card(
            title="Cargo Temporario",
            description=f"{member.mention} recebeu {cargo.mention} por **{duracao}**",
            color=0xFFD700,
        )
        await interaction.response.send_message(view=view)

    # ==================== ENQUETE ====================

    @app_commands.command(name="enquete", description="Cria uma enquete com até 10 opções")
    @app_commands.describe(
        pergunta="A pergunta da enquete",
        opcoes="Opções separadas por | (ex: Sim | Não | Talvez)"
    )
    async def enquete(self, interaction: discord.Interaction, pergunta: str, opcoes: str):
        options = [o.strip() for o in opcoes.split("|") if o.strip()]
        if len(options) < 2:
            view = make_error("Mínimo 2 opções. Separe com |")
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        if len(options) > 10:
            view = make_error("Máximo 10 opções.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        lines = []
        for i, opt in enumerate(options):
            lines.append(f"{number_emojis[i]} {opt}")

        # Enquete posted to channel — stays as embed for reaction support
        embed = discord.Embed(
            title=pergunta,
            description="\n\n".join(lines),
            color=0x5865F2,
            timestamp=_utcnow()
        )
        embed.set_author(name=f"Enquete de {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Desenvolvido por MARKIZIN")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        for i in range(len(options)):
            try:
                await msg.add_reaction(number_emojis[i])
            except Exception:
                pass

    # ==================== SERVERINFO ====================

    @app_commands.command(name="serverinfo", description="Informações detalhadas do servidor")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        roles = len(guild.roles) - 1  # -1 para @everyone
        emojis = len(guild.emojis)
        boosts = guild.premium_subscription_count or 0
        boost_level = guild.premium_tier

        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots

        view = make_card(
            title=guild.name,
            description=f"**ID:** {guild.id}",
            color=0x5865F2,
            fields=[
                ("Dono", f"{guild.owner.mention}" if guild.owner else "N/A"),
                ("Criado em", f"<t:{int(guild.created_at.timestamp())}:D>"),
                ("Membros", f"Total: **{guild.member_count}** | Humanos: {humans} | Bots: {bots}"),
                ("Canais", f"Texto: {text_channels} | Voz: {voice_channels} | Categorias: {categories}"),
                ("Cargos", f"{roles} cargos"),
                ("Boosts", f"Nivel {boost_level} ({boosts} boosts)"),
                ("Emojis", f"{emojis} emojis"),
            ],
            thumbnail_url=guild.icon.url if guild.icon else None,
            author_id=interaction.user.id,
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    # ==================== USERINFO ====================

    @app_commands.command(name="userinfo", description="Informações de um membro")
    @app_commands.describe(member="Membro (opcional)")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user

        roles = [r.mention for r in target.roles if not r.is_default()]
        roles_text = ", ".join(roles[:10]) if roles else "Nenhum"
        if len(roles) > 10:
            roles_text += f" ... +{len(roles) - 10}"

        fields = [
            ("Nome", f"{target} ({target.id})"),
            ("Conta criada", f"<t:{int(target.created_at.timestamp())}:R>"),
            ("Entrou no servidor", f"<t:{int(target.joined_at.timestamp())}:R>" if target.joined_at else "N/A"),
            ("Cargo mais alto", target.top_role.mention if not target.top_role.is_default() else "Nenhum"),
            (f"Cargos ({len(roles)})", roles_text),
        ]

        if target.bot:
            fields.append(("Bot", "Este membro e um bot"))

        view = make_card(
            title=target.display_name,
            description=f"Informacoes do membro",
            color=target.color if target.color.value else 0x5865F2,
            fields=fields,
            thumbnail_url=target.display_avatar.url,
            author_id=interaction.user.id,
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    # ==================== STARBOARD ====================

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        cfg = self.config_manager.get_guild_config(guild.id, "utilities")
        starboard_channel_id = cfg.get("starboard_channel_id")
        star_threshold = cfg.get("starboard_threshold", 3)
        star_emoji = cfg.get("starboard_emoji", "⭐")

        if not starboard_channel_id:
            return

        if str(payload.emoji) != star_emoji:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        # Não contabilizar reações no próprio starboard
        if channel.id == starboard_channel_id:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        # Contar reações da estrela
        star_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == star_emoji:
                star_count = reaction.count
                break

        if star_count < star_threshold:
            return

        starboard = guild.get_channel(starboard_channel_id)
        if not starboard:
            return

        # Verificar se já foi postado no starboard
        posted_key = f"starboard_posted"
        posted = cfg.get(posted_key, [])
        if message.id in posted:
            return

        # Postar no starboard (channel message — stays as embed)
        content_preview = message.content[:200] if message.content else ""
        embed = discord.Embed(
            title=f"{star_count} estrelas",
            description=f"{content_preview}\n\n[Ir para mensagem]({message.jump_url})",
            color=0xFFD700,
            timestamp=message.created_at
        )
        embed.set_footer(text="Desenvolvido por MARKIZIN")
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        try:
            await starboard.send(embed=embed)
            posted.append(message.id)
            self.config_manager.update_guild_config(guild.id, "utilities", {posted_key: posted})
        except Exception:
            pass


async def setup(bot: commands.Bot, config_manager):
    data = UtilitiesData()
    cog = UtilitiesCommands(bot, data, config_manager)
    await bot.add_cog(cog)

    # Task loop para lembretes e cargos temporários
    @tasks.loop(seconds=30)
    async def check_reminders_and_roles():
        # Lembretes
        due = data.get_due_reminders()
        for r in due:
            try:
                guild = bot.get_guild(r["guild_id"])
                if guild:
                    channel = guild.get_channel(r["channel_id"])
                    if channel:
                        user = guild.get_member(r["user_id"])
                        if user:
                            embed = discord.Embed(
                                title="Lembrete",
                                description=f"{user.mention}\n> {r['text']}",
                                color=0xFFD700
                            )
                            embed.set_footer(text="Desenvolvido por MARKIZIN")
                            await channel.send(content=user.mention, embed=embed)
            except Exception:
                pass
            data.remove_reminder(r)

        # Cargos temporários
        expired = data.get_expired_roles()
        for e in expired:
            try:
                guild = bot.get_guild(e["guild_id"])
                if guild:
                    member = guild.get_member(e["user_id"])
                    role = guild.get_role(e["role_id"])
                    if member and role and role in member.roles:
                        await member.remove_roles(role, reason="Cargo temporário expirado")
            except Exception:
                pass
            data.remove_temp_role(e)

    @check_reminders_and_roles.before_loop
    async def before_check():
        await bot.wait_until_ready()

    check_reminders_and_roles.start()
    print("   [OK] Sistema de Utilitarios carregado")
    return data
