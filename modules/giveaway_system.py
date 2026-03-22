"""
Sistema de Sorteios/Giveaways
Desenvolvido por: MARKIZIN
https://ggmax.com.br/perfil/markizin002
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random
import asyncio
import hashlib
from modules.components_v2 import make_card, make_success, make_error, brand_footer, BrandedView

# ⚠️ PROTEÇÃO DE AUTORIA - NÃO REMOVER
_AUTHOR_CHECK = hashlib.md5(b"MARKIZIN").hexdigest()

GIVEAWAY_FILE = Path("giveaways.json")


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class GiveawaySystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.data = self._load()

    def _load(self) -> dict:
        if not GIVEAWAY_FILE.exists():
            return {"giveaways": []}
        try:
            return json.loads(GIVEAWAY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"giveaways": []}

    def _save(self):
        try:
            tmp = GIVEAWAY_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(GIVEAWAY_FILE)
        except Exception as e:
            print(f"Erro ao salvar giveaways: {e}")

    def create(self, guild_id, channel_id, message_id, prize, end_time, winners_count, host_id, requirements=None):
        entry = {
            "guild_id": guild_id,
            "channel_id": channel_id,
            "message_id": message_id,
            "prize": prize,
            "end_time": end_time,
            "winners_count": winners_count,
            "host_id": host_id,
            "participants": [],
            "ended": False,
            "winners": [],
            "requirements": requirements or {}
        }
        self.data["giveaways"].append(entry)
        self._save()
        return entry

    def add_participant(self, message_id, user_id) -> bool:
        for g in self.data["giveaways"]:
            if g["message_id"] == message_id and not g["ended"]:
                if user_id not in g["participants"]:
                    g["participants"].append(user_id)
                    self._save()
                    return True
                return False
        return False

    def remove_participant(self, message_id, user_id):
        for g in self.data["giveaways"]:
            if g["message_id"] == message_id and not g["ended"]:
                if user_id in g["participants"]:
                    g["participants"].remove(user_id)
                    self._save()

    def end_giveaway(self, message_id) -> dict | None:
        for g in self.data["giveaways"]:
            if g["message_id"] == message_id and not g["ended"]:
                g["ended"] = True
                if g["participants"]:
                    count = min(g["winners_count"], len(g["participants"]))
                    g["winners"] = random.sample(g["participants"], count)
                self._save()
                return g
        return None

    def reroll(self, message_id) -> dict | None:
        for g in self.data["giveaways"]:
            if g["message_id"] == message_id and g["ended"]:
                if g["participants"]:
                    count = min(g["winners_count"], len(g["participants"]))
                    g["winners"] = random.sample(g["participants"], count)
                    self._save()
                return g
        return None

    def get_active(self, guild_id) -> list:
        return [g for g in self.data["giveaways"]
                if g["guild_id"] == guild_id and not g["ended"]]

    def get_expired(self) -> list:
        now = _utcnow().isoformat()
        return [g for g in self.data["giveaways"]
                if not g["ended"] and g["end_time"] <= now]


class GiveawayButton(discord.ui.Button):
    def __init__(self, giveaway_system: GiveawaySystem):
        super().__init__(
            label="Participar (0)",
            style=discord.ButtonStyle.success,
            custom_id="giveaway_join_btn"
        )
        self.giveaway_system = giveaway_system

    async def callback(self, interaction: discord.Interaction):
        msg_id = interaction.message.id

        # Encontrar o giveaway
        giveaway = None
        for g in self.giveaway_system.data["giveaways"]:
            if g["message_id"] == msg_id:
                giveaway = g
                break

        if not giveaway or giveaway["ended"]:
            await interaction.response.send_message("Este sorteio ja encerrou.", ephemeral=True)
            return

        # Verificar requisitos
        reqs = giveaway.get("requirements", {})
        if reqs.get("role_id"):
            role = interaction.guild.get_role(reqs["role_id"])
            if role and role not in interaction.user.roles:
                await interaction.response.send_message(
                    f"Voce precisa do cargo {role.mention} para participar.", ephemeral=True
                )
                return

        user_id = interaction.user.id
        if user_id in giveaway["participants"]:
            # Sair do sorteio
            self.giveaway_system.remove_participant(msg_id, user_id)
            count = len(giveaway["participants"])
            self.label = f"Participar ({count})"
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send("Voce saiu do sorteio.", ephemeral=True)
        else:
            # Entrar no sorteio
            self.giveaway_system.add_participant(msg_id, user_id)
            count = len(giveaway["participants"])
            self.label = f"Participar ({count})"
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send("Voce entrou no sorteio. Boa sorte.", ephemeral=True)


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_system: GiveawaySystem):
        super().__init__(timeout=None)
        self.add_item(GiveawayButton(giveaway_system))


class GiveawayCommands(commands.Cog):
    def __init__(self, bot, giveaway_system: GiveawaySystem, config_manager):
        self.bot = bot
        self.gs = giveaway_system
        self.config_manager = config_manager
        # ⚠️ PROTEÇÃO DE AUTORIA
        if _AUTHOR_CHECK != "7e94cd9fff4a493ba6b9b2abcc38f3c0":
            raise RuntimeError("Falha de integridade")

    sorteio_group = app_commands.Group(name="sorteio", description="Comandos de sorteio")

    @sorteio_group.command(name="criar", description="Cria um novo sorteio")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        premio="O que será sorteado",
        duracao="Duração (ex: 1h, 30m, 2d, 1d12h)",
        vencedores="Quantidade de vencedores",
        cargo_requisito="Cargo necessário para participar (opcional)"
    )
    async def criar(
        self, interaction: discord.Interaction,
        premio: str,
        duracao: str,
        vencedores: int = 1,
        cargo_requisito: discord.Role = None
    ):
        # Parsear duração
        total_seconds = 0
        import re
        parts = re.findall(r'(\d+)([dhms])', duracao.lower())
        if not parts:
            view = make_error("Formato de duração inválido. Use: `1h`, `30m`, `2d`, `1d12h`")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        for value, unit in parts:
            v = int(value)
            if unit == 'd':
                total_seconds += v * 86400
            elif unit == 'h':
                total_seconds += v * 3600
            elif unit == 'm':
                total_seconds += v * 60
            elif unit == 's':
                total_seconds += v

        if total_seconds <= 0 or total_seconds > 2592000:  # max 30 dias
            view = make_error("Duração deve ser entre 1 minuto e 30 dias.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if vencedores < 1 or vencedores > 20:
            view = make_error("Vencedores deve ser entre 1 e 20.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        end_time = _utcnow() + timedelta(seconds=total_seconds)

        # Montar card do sorteio
        desc = (
            f"**Prêmio:** {premio}\n\n"
            f"**Vencedores:** {vencedores}\n"
            f"**Encerra:** <t:{int(end_time.replace(tzinfo=timezone.utc).timestamp())}:R>\n"
            f"**Organizado por:** {interaction.user.mention}\n\n"
            f"Clique no botão abaixo para participar!"
        )

        fields = []
        if cargo_requisito:
            fields.append(("Requisito", f"Cargo: {cargo_requisito.mention}"))

        card_view = make_card(
            title="Sorteio",
            description=desc,
            color=0xFF1493,
            fields=fields if fields else None,
            timeout=None,
        )

        reqs = {}
        if cargo_requisito:
            reqs["role_id"] = cargo_requisito.id

        # Adicionar o botão de participar ao card_view
        giveaway_btn = GiveawayButton(self.gs)
        action_row = discord.ui.ActionRow(giveaway_btn)
        card_view.add_item(action_row)

        await interaction.response.send_message(view=card_view)
        msg = await interaction.original_response()

        self.gs.create(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            message_id=msg.id,
            prize=premio,
            end_time=end_time.isoformat(),
            winners_count=vencedores,
            host_id=interaction.user.id,
            requirements=reqs
        )

    @sorteio_group.command(name="reroll", description="Re-sorteia os vencedores de um sorteio encerrado")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(message_id="ID da mensagem do sorteio")
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            mid = int(message_id)
        except ValueError:
            view = make_error("ID inválido.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        result = self.gs.reroll(mid)
        if not result:
            view = make_error("Sorteio não encontrado ou ainda ativo.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if result["winners"]:
            mentions = ", ".join(f"<@{uid}>" for uid in result["winners"])
            view = make_card(
                title="Reroll",
                description=f"**Novo(s) vencedor(es):** {mentions}\n**Prêmio:** {result['prize']}",
                color=0xFF1493,
            )
            await interaction.response.send_message(view=view)
        else:
            view = make_error("Nenhum participante para re-sortear.")
            await interaction.response.send_message(view=view, ephemeral=True)

    @sorteio_group.command(name="listar", description="Lista sorteios ativos")
    async def listar(self, interaction: discord.Interaction):
        active = self.gs.get_active(interaction.guild.id)
        if not active:
            view = make_error("Nenhum sorteio ativo.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        lines = []
        for g in active:
            lines.append(
                f"**{g['prize']}** — {len(g['participants'])} participantes | "
                f"Encerra: `{g['end_time'][:16]}`"
            )

        view = make_card(
            title="Sorteios Ativos",
            description="\n".join(lines),
            color=0xFF1493,
            author_id=interaction.user.id,
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    @sorteio_group.command(name="encerrar", description="Encerra um sorteio manualmente")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(message_id="ID da mensagem do sorteio")
    async def encerrar(self, interaction: discord.Interaction, message_id: str):
        try:
            mid = int(message_id)
        except ValueError:
            view = make_error("ID inválido.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        result = self.gs.end_giveaway(mid)
        if not result:
            view = make_error("Sorteio não encontrado ou já encerrado.")
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await self._announce_winners(interaction.guild, result)
        view = make_success("Sorteio encerrado.")
        await interaction.response.send_message(view=view, ephemeral=True)

    async def _announce_winners(self, guild, giveaway):
        """Announce winners — channel messages stay as embeds for compatibility."""
        channel = guild.get_channel(giveaway["channel_id"])
        if not channel:
            return

        if giveaway["winners"]:
            mentions = ", ".join(f"<@{uid}>" for uid in giveaway["winners"])
            embed = discord.Embed(
                title="Sorteio Encerrado",
                description=f"**Premio:** {giveaway['prize']}\n\n"
                            f"**Vencedor(es):** {mentions}",
                color=0x00FF00,
                timestamp=_utcnow()
            )
            embed.set_footer(text="Desenvolvido por MARKIZIN")
        else:
            embed = discord.Embed(
                title="Sorteio Encerrado",
                description=f"**Premio:** {giveaway['prize']}\n\n"
                            f"Nenhum participante. Sorteio cancelado.",
                color=0xFF0000,
                timestamp=_utcnow()
            )
            embed.set_footer(text="Desenvolvido por MARKIZIN")

        try:
            # Tentar editar mensagem original
            try:
                msg = await channel.fetch_message(giveaway["message_id"])
                await msg.edit(embed=embed, view=None)
            except Exception:
                pass
            # Anunciar vencedores em nova mensagem
            if giveaway["winners"]:
                await channel.send(
                    f"Sorteio encerrado. Parabens {mentions}, voce ganhou **{giveaway['prize']}**."
                )
        except Exception:
            pass


async def setup(bot: commands.Bot, config_manager):
    gs = GiveawaySystem(config_manager)

    # Registrar view persistente
    bot.add_view(GiveawayView(gs))

    cog = GiveawayCommands(bot, gs, config_manager)
    await bot.add_cog(cog)

    # Task loop para verificar sorteios expirados
    @tasks.loop(seconds=30)
    async def check_expired():
        expired = gs.get_expired()
        for g in expired:
            result = gs.end_giveaway(g["message_id"])
            if result:
                guild = bot.get_guild(g["guild_id"])
                if guild:
                    await cog._announce_winners(guild, result)

    @check_expired.before_loop
    async def before_check():
        await bot.wait_until_ready()

    check_expired.start()
    print("   [OK] Sistema de Sorteios carregado")
    return gs
