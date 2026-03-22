import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
import asyncio
from pathlib import Path
import webbrowser
import hashlib
import sys
from datetime import datetime, timezone, timedelta
from discord.ext import tasks

# Importar sistema de painéis
from modules.panel_system import ConfigManager
from modules.panel_command import create_painel_command
from modules.panel_autorole import AutorolePanel  # usado apenas para tipagem/eventos
from modules.components_v2 import make_card, make_success, make_error, make_info, brand_footer, BrandedView
import random

# Instanciar gerenciador de configuração de painéis
panel_config = ConfigManager()

# Helper para aplicar estilo global de embeds + watermark autoral
def _style_embed(guild: discord.Guild | None, embed: discord.Embed) -> discord.Embed:
    if guild is None:
        # Mesmo sem guild, aplica watermark
        embed.set_footer(text="🔗 Desenvolvido por MARKIZIN", icon_url="https://ggmax.com.br/favicon.ico")
        return embed
    embed = panel_config.apply_style(guild.id, embed)
    # ⚠️ PROTEÇÃO: Watermark obrigatório em todos os embeds
    # Remover esta linha causará falha na verificação de integridade
    embed.set_footer(text="🔗 Desenvolvido por MARKIZIN", icon_url="https://ggmax.com.br/favicon.ico")
    return embed

# Helper para datetime UTC (utcnow() está deprecated no Python 3.12+)
def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ==================== PROTEÇÃO DE AUTORIA AVANÇADA ====================
# ⚠️ ATENÇÃO: REMOVER OU MODIFICAR QUALQUER PARTE DESTE CÓDIGO CAUSARÁ MAU FUNCIONAMENTO
# Sistema de proteção multicamadas - Desenvolvido por: MARKIZIN
# Perfil: https://ggmax.com.br/perfil/markizin002
# Versão da Proteção: 2.0

import base64
import time
from threading import Thread

# Dados do autor (ofuscados em base64)
_AUTOR_DATA = {
    'n': base64.b64decode('TUFSS0laSU4=').decode(),
    'p': base64.b64decode('aHR0cHM6Ly9nZ21heC5jb20uYnIvcGVyZmlsL21hcmtpemluMDAy').decode(),
    'h1': 'f1ab60a5648f42c23a9878934831bc79',
    'h2': '7528982429bbcb369d6f93f049426797',  # hash secundário
    'v': '2.0',
    't': 'BOT DISCORD - MODERAÇÃO + ECONOMIA'
}

def _calc_hash(data: str, salt: str = '') -> str:
    """Calcula hash com salt opcional."""
    return hashlib.md5((data + salt).encode()).hexdigest()

def _verificar_integridade_autor():
    """Verificação de integridade multicamadas do sistema de autoria."""
    try:
        # Verificação primária
        hash1 = _calc_hash(f"{_AUTOR_DATA['n']}{_AUTOR_DATA['p']}")
        if hash1 != _AUTOR_DATA['h1']:
            raise ValueError("Falha na verificação primária")
        
        # Verificação secundária (com salt)
        hash2 = _calc_hash(_AUTOR_DATA['t'], _AUTOR_DATA['v'])
        if hash2 != _AUTOR_DATA['h2']:
            raise ValueError("Falha na verificação secundária")
        
        # Verificação de estrutura
        required_keys = {'n', 'p', 'h1', 'h2', 'v', 't'}
        if not required_keys.issubset(_AUTOR_DATA.keys()):
            raise ValueError("Estrutura de dados comprometida")
        
        return True
    except Exception as e:
        print(f"\n{'='*70}")
        print("  ERRO CRITICO DE SEGURANCA")
        print("="*70)
        print("  Sistema de protecao de autoria comprometido")
        print(f"  Detalhes: {str(e)}")
        print("  O bot sera encerrado imediatamente")
        print("="*70)
        print("\n  Para suporte, contate: https://ggmax.com.br/perfil/markizin002")
        print("="*70 + "\n")
        time.sleep(3)
        sys.exit(1)

def _exibir_creditos_autor():
    """Exibe os créditos do autor com verificação de integridade."""
    if not _verificar_integridade_autor():
        sys.exit(1)
    
    print("\n" + "="*70)
    print(f"  {_AUTOR_DATA['t']}")
    print("="*70)
    print(f"  Desenvolvido por: {_AUTOR_DATA['n']}")
    print(f"  Perfil: {_AUTOR_DATA['p']}")
    print(f"  Protecao: v{_AUTOR_DATA['v']} (Multicamadas)")
    print("="*70)
    print("  Este bot possui protecao avancada de autoria")
    print("  Modificacoes nao autorizadas sao detectadas automaticamente")
    print("  Violacoes resultam em encerramento imediato do sistema")
    print("="*70 + "\n")

    try:
        print("  Abrindo perfil do desenvolvedor...")
        webbrowser.open(_AUTOR_DATA['p'])
        print("  Perfil aberto com sucesso!\n")
    except Exception:
        print("  Nao foi possivel abrir o navegador\n")
    
    return True

def _monitorar_integridade():
    """Monitor em background que verifica integridade periodicamente."""
    while True:
        time.sleep(1800)  # Verifica a cada 30 minutos
        if not _verificar_integridade_autor():
            break

# Verificação inicial de autoria
if not _exibir_creditos_autor():
    sys.exit(1)

# Iniciar monitor de integridade em background
_monitor_thread = Thread(target=_monitorar_integridade, daemon=True)
_monitor_thread.start()

# Variável global para watermark
_WATERMARK_ENABLED = True

# Setup do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ==================== PERSISTÊNCIA ====================

# Persistência de economia (JSON + lock)
ECONOMY_FILE = Path("economia.json")
economia_lock = asyncio.Lock()

def load_economia():
    """Carrega o arquivo de economia e retorna um dict com chaves int -> saldo."""
    if not ECONOMY_FILE.exists():
        return {}
    try:
        text = ECONOMY_FILE.read_text(encoding="utf-8")
        data = json.loads(text)
        return {int(k): v for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        return {}

def _save_economia_sync(dados):
    """Salva dados em disco de forma atômica (sync)."""
    serializable = {str(k): v for k, v in dados.items()}
    tmp = ECONOMY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(serializable, ensure_ascii=False), encoding="utf-8")
    tmp.replace(ECONOMY_FILE)

async def save_economia(dados):
    """Wrapper assíncrono que delega escrita para executor."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_economia_sync, dados)

economia = load_economia()

# ==================== INVENTÁRIO (LOJA) ====================
INVENTORY_FILE = Path('inventory.json')
inventory_lock = asyncio.Lock()

def load_inventory():
    if not INVENTORY_FILE.exists():
        return {}
    try:
        data = json.loads(INVENTORY_FILE.read_text(encoding='utf-8'))
        return {str(k): v for k,v in data.items()}
    except Exception:
        return {}

def _save_inventory_sync(inv):
    tmp = INVENTORY_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(inv, ensure_ascii=False), encoding='utf-8')
    tmp.replace(INVENTORY_FILE)

async def save_inventory(inv):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_inventory_sync, inv)

inventory = load_inventory()

# Persistência de configuração (JSON)
CONFIG_FILE = Path("config.json")

def load_config():
    """Carrega arquivo de configuração."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        text = CONFIG_FILE.read_text(encoding="utf-8")
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}

def _save_config_sync(dados):
    """Salva configuração em disco de forma atômica (sync)."""
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CONFIG_FILE)

async def save_config(dados):
    """Wrapper assíncrono que delega escrita para executor."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_config_sync, dados)

config = load_config()

# ==================== COMPONENTES (VIEWS E MODALS) ====================

class AuthorOnlyView(discord.ui.View):
    def __init__(self, author_id: int, timeout: float | None = 60):
        super().__init__(timeout=timeout)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            try:
                await interaction.response.send_message(
                    "Somente quem solicitou pode usar estes botoes.", ephemeral=True
                )
            except Exception:
                pass
            return False
        return True


class TransferModal(discord.ui.Modal, title="Transferir creditos"):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

        self.destino = discord.ui.TextInput(
            label="Usuário destino (menção ou ID)", placeholder="@membro ou 1234567890", required=True, max_length=64
        )
        self.quantia = discord.ui.TextInput(
            label="Quantidade", placeholder="Ex: 100", required=True, max_length=12
        )
        self.add_item(self.destino)
        self.add_item(self.quantia)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Use no servidor.", ephemeral=True)
            return

        # Resolver destino por menção ou ID
        raw = str(self.destino.value).strip()
        user_id = None
        try:
            if raw.startswith("<@") and raw.endswith(">"):
                raw = raw.replace("<@!", "").replace("<@", "").replace(">", "")
            user_id = int(raw)
        except Exception:
            pass

        membro_destino = None
        if user_id:
            try:
                membro_destino = interaction.guild.get_member(user_id) or await interaction.guild.fetch_member(user_id)
            except Exception:
                pass
        
        if not membro_destino:
            await interaction.response.send_message("Usuario destino invalido.", ephemeral=True)
            return

        # Quantia
        try:
            quantia = int(str(self.quantia.value).strip())
        except Exception:
            await interaction.response.send_message("Quantia invalida.", ephemeral=True)
            return

        sender_id = self.author.id
        receiver_id = membro_destino.id

        if quantia <= 0:
            await interaction.response.send_message("Quantia deve ser maior que 0.", ephemeral=True)
            return
        if receiver_id == sender_id:
            await interaction.response.send_message("Voce nao pode transferir para si mesmo.", ephemeral=True)
            return

        async with economia_lock:
            if sender_id not in economia:
                economia[sender_id] = 0
            if receiver_id not in economia:
                economia[receiver_id] = 0

            if economia[sender_id] < quantia:
                await interaction.response.send_message("Saldo insuficiente.", ephemeral=True)
                return

            economia[sender_id] -= quantia
            economia[receiver_id] += quantia
            await save_economia(economia)

        view = make_card(
            title="Transferencia realizada",
            description=f"{interaction.user.mention} transferiu {quantia} créditos para {membro_destino.mention}",
            color=discord.Color.gold(),
            fields=[("Saldo atual", str(economia.get(sender_id, 0)))],
            author_id=interaction.user.id,
        )
        try:
            await interaction.response.send_message(view=view, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(view=view, ephemeral=True)


class EconomyView(AuthorOnlyView):
    def __init__(self, author_id: int):
        super().__init__(author_id, timeout=60)

    @discord.ui.button(label="Transferir", style=discord.ButtonStyle.primary)
    async def btn_transferir(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TransferModal(author=interaction.user)
        try:
            await interaction.response.send_modal(modal)
        except Exception:
            await interaction.response.send_message("Nao foi possivel abrir o formulario.", ephemeral=True)

    @discord.ui.button(label="Daily", style=discord.ButtonStyle.success)
    async def btn_daily(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use o comando `/daily` para coletar sua recompensa diária.", ephemeral=True)

    @discord.ui.button(label="Ajuda", style=discord.ButtonStyle.secondary)
    async def btn_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await send_help_ephemeral(interaction)


class ConfirmActionView(AuthorOnlyView):
    def __init__(self, author_id: int, action_label: str = "Confirmar"):
        super().__init__(author_id, timeout=30)
        self.confirmed = False
        self.action_label = action_label

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Operacao cancelada.", view=self)
        self.stop()

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Confirmado.", view=self)
        self.stop()


async def send_help_ephemeral(interaction: discord.Interaction):
    """Construir uma ajuda compacta para ephemeral."""
    slash_commands = tree.get_commands()

    desc_lines = []
    for cmd in sorted(slash_commands, key=lambda x: x.name):
        desc_lines.append(f"`/{cmd.name}` — {cmd.description or 'Sem descrição'}")

    help_view = make_card(
        title="Comandos disponiveis",
        description="\n".join(desc_lines) or "Nenhum comando disponível.",
        color=discord.Color.blurple(),
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=help_view, ephemeral=True)


# ==================== EVENTOS ====================


# ==================== TASK LOOPS ====================

from discord.ext import tasks

@tasks.loop(minutes=5)
async def auto_close_tickets_task():
    """Fecha tickets inativos automaticamente."""
    for guild in bot.guilds:
        cfg = panel_config.get_guild_config(guild.id, 'tickets')
        if not cfg.get('enabled') or not cfg.get('auto_close_minutes') or not cfg.get('auto_close_enabled', False):
            continue
        threshold_minutes = cfg.get('auto_close_minutes')
        category_ids = cfg.get('category_ids', [])
        if not category_ids and cfg.get('category_id'):
            category_ids = [cfg.get('category_id')]
        for cid in category_ids:
            cat = guild.get_channel(cid)
            if not isinstance(cat, discord.CategoryChannel):
                continue
            for ch in cat.channels:
                if not isinstance(ch, discord.TextChannel):
                    continue
                if not ch.topic or 'user:' not in ch.topic:
                    continue
                try:
                    last_msg = None
                    async for msg in ch.history(limit=1):
                        last_msg = msg
                        break
                    if last_msg:
                        delta = (_utcnow() - last_msg.created_at).total_seconds() / 60
                        if delta >= threshold_minutes:
                            await ch.send('⏰ Ticket fechado automaticamente por inatividade.')
                            await asyncio.sleep(5)
                            await ch.delete(reason='Auto-close por inatividade')
                            closed = cfg.get('closed_counter', 0) + 1
                            panel_config.update_guild_config(guild.id, 'tickets', {'closed_counter': closed})
                except Exception:
                    pass

@tasks.loop(minutes=10)
async def sla_check_task():
    """Verifica tickets em atraso e envia alertas."""
    for guild in bot.guilds:
        cfg = panel_config.get_guild_config(guild.id, 'tickets')
        if not cfg.get('enabled'):
            continue
        if not cfg.get('sla_enabled', True):
            continue
        sla_map = cfg.get('sla_by_priority')
        legacy_sla = cfg.get('sla_minutes')
        if not sla_map and not legacy_sla:
            continue
        alert_roles = cfg.get('sla_alert_role_ids', [])
        escalation_min = None  # escalonamento por prioridade pode ser adicionado depois
        escalation_roles = cfg.get('escalation_role_ids', [])
        category_ids = cfg.get('category_ids', [])
        if not category_ids and cfg.get('category_id'):
            category_ids = [cfg.get('category_id')]
        for cid in category_ids:
            cat = guild.get_channel(cid)
            if not isinstance(cat, discord.CategoryChannel):
                continue
            for ch in cat.channels:
                if not isinstance(ch, discord.TextChannel):
                    continue
                if not ch.topic or 'user:' not in ch.topic:
                    continue
                try:
                    async for msg in ch.history(limit=50):
                        if not msg.author.bot:
                            staff_responded = any(r.id in cfg.get('support_role_ids', []) for r in msg.author.roles) if hasattr(msg.author, 'roles') else False
                            if staff_responded:
                                break
                    else:
                        created_delta = (_utcnow() - ch.created_at).total_seconds() / 60
                        # Detectar prioridade no tópico
                        priority = None
                        if 'priority:' in ch.topic:
                            try:
                                priority = ch.topic.split('priority:')[1].split()[0].upper()
                            except (IndexError, AttributeError):
                                priority = None
                        threshold = None
                        if sla_map and priority:
                            threshold = sla_map.get(priority)
                        elif legacy_sla:
                            threshold = legacy_sla
                        if threshold and created_delta >= threshold and alert_roles:
                            mention = ' '.join([f'<@&{rid}>' for rid in alert_roles])
                            await ch.send(f'🚨 SLA excedido ({priority or "PADRÃO"}) após {int(created_delta)} min! {mention}')
                        if escalation_min and created_delta >= escalation_min and escalation_roles:
                            mention_esc = ' '.join([f'<@&{rid}>' for rid in escalation_roles])
                            await ch.send(f'⚠️ Escalonamento! {mention_esc}')
                except Exception:
                    pass

@bot.event
async def on_ready():
    # Verificação adicional de integridade ao conectar
    _verificar_integridade_autor()
    
    # ⚠️ PROTEÇÃO: Definir status do bot com marca do autor
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="por MARKIZIN | /painel")
    )

    # Carregar sistemas adicionais
    try:
        from modules import backup_system, themes, permissions, import_export, stats_system, antiraid_system, form_system
        from modules import leveling_system, giveaway_system, utilities_system
        from modules.panel_tickets import OpenTicketButton
        from modules.form_system import FormPublicView

        await backup_system.setup(bot, panel_config)
        await themes.setup(bot, panel_config)
        await permissions.setup(bot, panel_config)
        await import_export.setup(bot, panel_config)
        global stats_tracker
        stats_tracker = await stats_system.setup(bot, panel_config)
        await antiraid_system.setup(bot, panel_config)
        form_sys = await form_system.setup(bot, panel_config)
        await leveling_system.setup(bot, panel_config)
        await giveaway_system.setup(bot, panel_config)
        await utilities_system.setup(bot, panel_config)
        
        # Registrar views persistentes (timeout=None) para funcionar após restart
        # OpenTicketView precisa ser recriado para cada guild
        for guild in bot.guilds:
            try:
                # Registrar view do ticket com custom_id
                class OpenTicketView(discord.ui.View):
                    def __init__(self, cm):
                        super().__init__(timeout=None)
                        self.add_item(OpenTicketButton(cm))
                bot.add_view(OpenTicketView(panel_config))
                
                # Registrar views de formulários
                forms = form_sys.get_forms(guild.id)
                for form_id, form_data in forms.items():
                    bot.add_view(FormPublicView(form_sys, guild.id, form_data))
            except Exception as e:
                print(f"  [AVISO] Erro ao registrar views persistentes para {guild.name}: {e}")

        print("  [OK] Todos os 10 sistemas carregados com sucesso!")
        print("       Backup | Temas | Permissoes | Import/Export")
        print("       Estatisticas | Anti-Raid | Formularios")
        print("       Niveis/XP | Sorteios | Utilitarios")
        print("  [OK] Views persistentes registrados")
    except Exception as e:
        print(f"  [AVISO] Erro ao carregar sistemas extras: {e}")
    
    # Sincronizar App Commands (Slash Commands)
    # Registrar comando mestre de painéis (se ainda não registrado)
    try:
        if not any(c.name == "painel" for c in tree.get_commands()):
            tree.add_command(create_painel_command(panel_config))
        synced = await tree.sync()
        print(f"  [OK] Sincronizados {len(synced)} comandos slash (incluindo /painel).")
    except Exception as e:
        print(f"  [ERRO] Erro ao sincronizar comandos: {e}")

    print(f"  [OK] Bot {bot.user} conectado com sucesso!")
    print(f"  Desenvolvido por MARKIZIN - https://ggmax.com.br/perfil/markizin002")
    print(f"  Servidores: {len(bot.guilds)} | Usuarios: {len(set(bot.get_all_members()))}")
    print(f"  Slash Commands: {len(tree.get_commands())}")
    print(f"  Latencia: {round(bot.latency * 1000)}ms")
    print("="*60)

    # Inicializar cache auxiliar para anti-spam
    global _recent_messages
    _recent_messages = {}

    # Iniciar tasks loops
    auto_close_tickets_task.start()
    sla_check_task.start()


# ==================== EVENTOS AUTOROLE / REACTIONS ====================

def _match_emoji(stored: str, payload_emoji) -> bool:
    """Tenta casar o emoji configurado com o do payload.
    stored pode ser unicode (ex: 😀) ou formato custom (<:nome:id> ou :nome:id).
    """
    try:
        if payload_emoji.is_custom_emoji():
            # Formato padrão armazenado deve ser <a:name:id> ou <:name:id>
            expected = f"<{'a' if payload_emoji.animated else ''}:{payload_emoji.name}:{payload_emoji.id}>"
            return stored == expected
        return stored == str(payload_emoji)
    except Exception:
        return False


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.guild_id is None or payload.member is None:
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    autorole_cfg = panel_config.get_guild_config(guild.id, 'autorole')
    if not autorole_cfg.get('enabled'):
        return
    rr_list = autorole_cfg.get('reaction_roles', [])
    if not rr_list:
        return
    for rr in rr_list:
        if rr.get('message_id') == payload.message_id and rr.get('channel_id') == payload.channel_id and _match_emoji(rr.get('emoji', ''), payload.emoji):
            role = guild.get_role(rr.get('role_id'))
            if role is None:
                continue
            member = payload.member
            try:
                if role not in member.roles:
                    await member.add_roles(role, reason='Reaction Role')
                # Se for único, remover outros únicos desse mesmo message
                if rr.get('unique'):
                    for other in rr_list:
                        if other is rr:
                            continue
                        if other.get('unique') and other.get('message_id') == rr.get('message_id'):
                            other_role = guild.get_role(other.get('role_id'))
                            if other_role and other_role in member.roles and other_role != role:
                                await member.remove_roles(other_role, reason='Reaction Role (grupo único)')
            except Exception:
                pass
            break


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.guild_id is None:
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    autorole_cfg = panel_config.get_guild_config(guild.id, 'autorole')
    if not autorole_cfg.get('enabled'):
        return
    rr_list = autorole_cfg.get('reaction_roles', [])
    if not rr_list:
        return
    # Buscar membro (não vem pronto no remove)
    try:
        member = await guild.fetch_member(payload.user_id)
    except Exception:
        return
    for rr in rr_list:
        if rr.get('message_id') == payload.message_id and rr.get('channel_id') == payload.channel_id and _match_emoji(rr.get('emoji', ''), payload.emoji):
            role = guild.get_role(rr.get('role_id'))
            if role and role in member.roles:
                try:
                    await member.remove_roles(role, reason='Reaction Role removido')
                except Exception:
                    pass
            break

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """Remove reações do usuário em mensagens de reaction role se o cargo correspondente foi retirado."""
    if before.guild is None:
        return
    removed_roles = set(before.roles) - set(after.roles)
    if not removed_roles:
        return
    autorole_cfg = panel_config.get_guild_config(before.guild.id, 'autorole')
    if not autorole_cfg.get('enabled'):
        return
    rr_list = autorole_cfg.get('reaction_roles', [])
    if not rr_list:
        return
    # Map role_id -> reaction role entries
    role_map = {}
    for rr in rr_list:
        role_map.setdefault(rr.get('role_id'), []).append(rr)
    targets = []
    for r in removed_roles:
        if r.id in role_map:
            targets.extend(role_map[r.id])
    if not targets:
        return
    for rr in targets:
        channel = before.guild.get_channel(rr.get('channel_id'))
        if not channel:
            continue
        try:
            msg = await channel.fetch_message(rr.get('message_id'))
        except Exception:
            continue
        emoji = rr.get('emoji')
        # Tentar remover a reação específica
        try:
            # Encontrar Reaction object correspondente
            for reaction in msg.reactions:
                # Comparar unicode
                if not reaction.custom and emoji == str(reaction.emoji):
                    await reaction.remove(after)
                    break
                # Custom
                if reaction.custom and isinstance(reaction.emoji, discord.Emoji):
                    expected = f"<{'a' if reaction.emoji.animated else ''}:{reaction.emoji.name}:{reaction.emoji.id}>"
                    if emoji == expected:
                        await reaction.remove(after)
                        break
        except Exception:
            pass

@bot.event
async def on_member_remove(member: discord.Member):
    # Salvar cargos se restore_roles estiver ativo
    try:
        welcome_cfg = panel_config.get_guild_config(member.guild.id, 'welcome')
        if welcome_cfg.get('restore_roles'):
            roles_ids = [r.id for r in member.roles if not r.is_default()]
            restore_map = panel_config.get_guild_config(member.guild.id, 'welcome').get('role_restores', {})
            restore_map[str(member.id)] = roles_ids
            panel_config.update_guild_config(member.guild.id, 'welcome', {'role_restores': restore_map})
    except Exception:
        pass

@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        return
    cfg = panel_config.get_guild_config(member.guild.id, 'welcome')
    if not cfg.get('enabled'):
        return
    channel_id = cfg.get('channel_id')
    channel = member.guild.get_channel(channel_id) if channel_id else None
    if not channel:
        return
    # Escolher mensagem
    title = cfg.get('title', '').format(user=member.mention, server=member.guild.name)
    description = cfg.get('description', '').format(user=member.mention, server=member.guild.name)
    rand_list = cfg.get('random_messages', [])
    if rand_list:
        chosen = random.choice(rand_list)
        description += f"\n\n{chosen.format(user=member.mention, server=member.guild.name)}"
    # Contador
    if cfg.get('member_counter'):
        member_number = member.guild.member_count
        description += f"\nVocê é o membro nº **{member_number}**"
    embed = discord.Embed(title=title, description=description, color=cfg.get('color', 0x00FF00))
    if cfg.get('footer'):
        embed.set_footer(text=cfg.get('footer'))
    if cfg.get('image_url'):
        embed.set_image(url=cfg.get('image_url'))
    if cfg.get('thumbnail_url'):
        embed.set_thumbnail(url=cfg.get('thumbnail_url'))
    embed = panel_config.apply_style(member.guild.id, embed)
    try:
        await channel.send(embed=embed)
    except Exception:
        pass
    # Dar cargo automático
    role_id = cfg.get('role_id')
    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role, reason='Auto welcome role')
            except Exception:
                pass
    # Restaurar cargos
    if cfg.get('restore_roles') and cfg.get('role_restores') and str(member.id) in cfg.get('role_restores'):
        to_restore = []
        for rid in cfg.get('role_restores').get(str(member.id), []):
            r = member.guild.get_role(rid)
            if r:
                to_restore.append(r)
        if to_restore:
            try:
                await member.add_roles(*to_restore, reason='Restore roles on rejoin')
            except Exception:
                pass
    # DM
    if cfg.get('dm_enabled') and not member.bot:
        dm_text = cfg.get('dm_message', '').format(user=member.mention, server=member.guild.name)
        try:
            await member.send(dm_text)
        except Exception:
            pass


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handler global para erros de App Commands (Slash Commands)."""
    embed = None
    
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title="Permissao insuficiente",
            description="Você não tem permissão para executar este comando.",
            color=discord.Color.red()
        )
    elif isinstance(error, app_commands.CommandOnCooldown):
        embed = discord.Embed(
            title="Cooldown ativo",
            description=f"Tente novamente em {round(error.retry_after)}s.",
            color=discord.Color.orange()
        )
    elif isinstance(error, app_commands.MissingRole):
        embed = discord.Embed(
            title="Cargo necessario",
            description="Você não tem o cargo necessário para usar este comando.",
            color=discord.Color.red()
        )
    else:
        # Erro genérico
        print(f"Erro em App Command: {error}")
        embed = discord.Embed(
            title="Erro inesperado",
            description="Ocorreu um erro ao executar o comando.",
            color=discord.Color.dark_red()
        )
        # Log no canal de logs se configurado
        if interaction.guild:
            guild_id = str(interaction.guild.id)
            if guild_id in config and 'log_channel_id' in config[guild_id]:
                log_channel_id = config[guild_id]['log_channel_id']
                log_channel = bot.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="Erro em Slash Command",
                        description=f"Comando: `/{interaction.command.name if interaction.command else 'desconhecido'}`\nErro: {str(error)[:100]}",
                        color=discord.Color.dark_red()
                    )
                    log_embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar)
                    try:
                        await log_channel.send(embed=log_embed)
                    except Exception:
                        pass
    
    try:
        if interaction.response.is_done():
            embed = _style_embed(interaction.guild, embed)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = _style_embed(interaction.guild, embed)
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception:
        pass


# ==================== SLASH COMMANDS ====================

# ========== UTILITÁRIOS ==========

@tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    view = make_card(
        title="Pong",
        description=f"Latência: **{latency}ms**",
        color=0x5865F2,
        fields=[
            ("Servidores", str(len(bot.guilds))),
            ("Uptime", "Online"),
        ],
    )
    await interaction.response.send_message(view=view)


@tree.command(name="bemvindo", description="Envia mensagem de boas-vindas")
async def bemvindo(interaction: discord.Interaction):
    view = make_card(
        title="Bem-vindo ao servidor",
        description="Obrigado por se juntar a nós! Veja nossos canais de regras e diversão.",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(view=view)


@tree.command(name="ajuda", description="Lista todos os comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
    await send_help_ephemeral(interaction)


# ========== ECONOMIA ==========

# Cooldowns para App Commands usam app_commands.checks.cooldown
user_cooldowns = {}

@tree.command(name="daily", description="Ganha créditos diários (100 créditos)")
@app_commands.checks.cooldown(1, 86400, key=lambda i: (i.guild_id, i.user.id))
async def daily(interaction: discord.Interaction):
    econ_cfg = panel_config.get_guild_config(interaction.guild.id, "economy")
    amount = econ_cfg.get("daily_amount", 100)
    emoji = econ_cfg.get("daily_emoji", "💰")
    color = econ_cfg.get("daily_color", 0x00FF00)

    user_id = interaction.user.id
    async with economia_lock:
        if user_id not in economia:
            economia[user_id] = 0
        economia[user_id] += amount
        await save_economia(economia)

    view = make_card(
        title="Daily coletado",
        description=f"Voce ganhou **{amount} creditos**.",
        color=color,
        fields=[
            ("Saldo atual", f"**{economia[user_id]:,}** créditos"),
        ],
        thumbnail_url=interaction.user.display_avatar.url,
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=view)


@tree.command(name="saldo", description="Vê seu saldo de créditos")
async def saldo(interaction: discord.Interaction):
    econ_cfg = panel_config.get_guild_config(interaction.guild.id, "economy")
    color = econ_cfg.get("saldo_color", 0xFFD700)
    user_id = interaction.user.id
    saldo_valor = economia.get(user_id, 0)
    view = make_card(
        title="Seu saldo",
        description=f"Você tem: **{saldo_valor:,} créditos**",
        color=color,
        thumbnail_url=interaction.user.display_avatar.url,
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=view, ephemeral=True)


@tree.command(name="transferir", description="Transfere créditos para outro membro")
@app_commands.describe(member="Membro que receberá os créditos", amount="Quantidade de créditos a transferir")
async def transferir(interaction: discord.Interaction, member: discord.Member, amount: int):
    sender_id = interaction.user.id
    receiver_id = member.id
    econ_cfg = panel_config.get_guild_config(interaction.guild.id, "economy")
    emoji = econ_cfg.get("currency_emoji", "💸")
    msg_template = econ_cfg.get("transfer_success_message", "{emoji} {sender} transferiu {amount} créditos para {receiver}")
    insufficient_msg = econ_cfg.get("insufficient_funds_message", "Saldo insuficiente.")

    if amount <= 0:
        await interaction.response.send_message(view=make_error("Quantia inválida. Use um valor maior que 0."), ephemeral=True)
        return
    if receiver_id == sender_id:
        await interaction.response.send_message(view=make_error("Você não pode transferir para si mesmo."), ephemeral=True)
        return

    async with economia_lock:
        if sender_id not in economia:
            economia[sender_id] = 0
        if receiver_id not in economia:
            economia[receiver_id] = 0

        if economia[sender_id] < amount:
            await interaction.response.send_message(view=make_error(insufficient_msg), ephemeral=True)
            return

        economia[sender_id] -= amount
        economia[receiver_id] += amount
        await save_economia(economia)

    color = econ_cfg.get("saldo_color", 0xFFD700)
    view = make_card(
        title="Transferencia realizada",
        description=msg_template.format(emoji=emoji, sender=interaction.user.mention, amount=amount, receiver=member.mention),
        color=color,
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=view)

@tree.command(name="top", description="Exibe ranking de maiores saldos")
async def top(interaction: discord.Interaction):
    if not economia:
        await interaction.response.send_message(view=make_error("Nenhum dado de economia."), ephemeral=True)
        return
    sorted_users = sorted(economia.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for i, (uid, value) in enumerate(sorted_users, start=1):
        member = interaction.guild.get_member(uid)
        name = member.display_name if member else f"ID:{uid}"
        medal = medals.get(i, f"**{i}.**")
        lines.append(f"{medal} {name} — **{value:,}** créditos")
    view = make_card(
        title="Ranking de saldos",
        description="\n".join(lines),
        color=0xFFD700,
    )
    await interaction.response.send_message(view=view, ephemeral=True)

@tree.command(name="shop", description="Lista itens disponíveis para compra")
async def shop(interaction: discord.Interaction):
    econ_cfg = panel_config.get_guild_config(interaction.guild.id, 'economy')
    if not econ_cfg.get('shop_enabled'):
        await interaction.response.send_message("Loja desativada.", ephemeral=True)
        return
    items = econ_cfg.get('shop_items', [])
    if not items:
        await interaction.response.send_message("Nenhum item na loja.", ephemeral=True)
        return
    lines = [f"{it['name']} — {it['price']} {econ_cfg.get('shop_currency_name','créditos')}" for it in items]
    view = make_card(
        title="Loja",
        description="\n".join(lines),
        color=econ_cfg.get('daily_color', 0x00FF00),
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=view, ephemeral=True)

@tree.command(name="buy", description="Compra um item da loja")
@app_commands.describe(item="Nome do item exatamente como listado")
async def buy(interaction: discord.Interaction, item: str):
    econ_cfg = panel_config.get_guild_config(interaction.guild.id, 'economy')
    if not econ_cfg.get('shop_enabled'):
        await interaction.response.send_message("Loja desativada.", ephemeral=True)
        return
    items = econ_cfg.get('shop_items', [])
    target = None
    for it in items:
        if it['name'].lower() == item.lower():
            target = it
            break
    if not target:
        await interaction.response.send_message("Item não encontrado.", ephemeral=True)
        return
    user_id = interaction.user.id
    insufficient_msg = econ_cfg.get("insufficient_funds_message", "Saldo insuficiente.")
    buy_msg = econ_cfg.get("buy_success_message", "Voce comprou **{item}** por {price} {currency}.")
    currency = econ_cfg.get('shop_currency_name','créditos')
    emoji = econ_cfg.get('currency_emoji', '💳')
    async with economia_lock:
        saldo = economia.get(user_id,0)
        if saldo < target['price']:
            await interaction.response.send_message(insufficient_msg, ephemeral=True)
            return
        economia[user_id] = saldo - target['price']
        await save_economia(economia)
    async with inventory_lock:
        inv_user = inventory.get(str(user_id), [])
        inv_user.append(target['name'])
        inventory[str(user_id)] = inv_user
        await save_inventory(inventory)
    view = make_success(buy_msg.format(item=target['name'], price=target['price'], currency=currency, emoji=emoji), author_id=interaction.user.id)
    await interaction.response.send_message(view=view, ephemeral=True)

@tree.command(name="inventory", description="Mostra seus itens comprados")
async def inventory_cmd(interaction: discord.Interaction):
    inv_user = inventory.get(str(interaction.user.id), [])
    if not inv_user:
        await interaction.response.send_message("Inventário vazio.", ephemeral=True)
        return
    view = make_card(
        title="Inventario",
        description="\n".join([f"• {it}" for it in inv_user]),
        color=discord.Color.blurple(),
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=view, ephemeral=True)


# ========== ECONOMIA AVANÇADA ==========

TRABALHOS = [
    ("👨‍🍳 Cozinheiro", 50, 150),
    ("🚗 Motorista de Uber", 40, 120),
    ("💻 Programador freelancer", 80, 200),
    ("🎨 Designer gráfico", 60, 180),
    ("📦 Entregador", 30, 100),
    ("🎵 DJ de festa", 70, 160),
    ("📸 Fotógrafo", 50, 140),
    ("🏗️ Pedreiro", 60, 130),
    ("🎭 Ator de teatro", 40, 170),
    ("✂️ Barbeiro", 35, 110),
    ("🐕 Passeador de cães", 25, 90),
    ("📚 Professor particular", 55, 150),
    ("🎮 Streamer", 20, 250),
    ("🧹 Faxineiro", 30, 80),
    ("🍕 Pizzaiolo", 45, 120),
]

FRACASSOS_ROUBO = [
    "Voce tropecou e caiu enquanto fugia.",
    "A vitima te viu e chamou a policia.",
    "Seu plano falhou miseravelmente.",
    "Voce confundiu a carteira com um tijolo.",
    "A vitima era um lutador de MMA.",
]


@tree.command(name="trabalhar", description="Trabalha para ganhar créditos")
@app_commands.checks.cooldown(1, 3600, key=lambda i: (i.guild_id, i.user.id))
async def trabalhar(interaction: discord.Interaction):
    econ_cfg = panel_config.get_guild_config(interaction.guild.id, "economy")
    trabalho_nome, ganho_min, ganho_max = random.choice(TRABALHOS)
    ganho = random.randint(ganho_min, ganho_max)

    # Multiplicador por cargo
    salary_roles = econ_cfg.get("salary_roles", {})
    multiplier = 1.0
    for role_id_str, mult in salary_roles.items():
        role = interaction.guild.get_role(int(role_id_str))
        if role and role in interaction.user.roles:
            multiplier = max(multiplier, mult)
    ganho = int(ganho * multiplier)

    async with economia_lock:
        user_id = interaction.user.id
        if user_id not in economia:
            economia[user_id] = 0
        economia[user_id] += ganho
        await save_economia(economia)

    fields = [("Saldo atual", f"{economia.get(interaction.user.id, 0)} créditos")]
    if multiplier > 1:
        fields.insert(0, ("Bonus de cargo", f"Multiplicador: {multiplier}x"))
    view = make_card(
        title=f"{trabalho_nome}",
        description=f"Voce trabalhou como {trabalho_nome.split(' ', 1)[1]} e ganhou **{ganho} creditos**.",
        color=0x00FF00,
        fields=fields,
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=view)


@tree.command(name="roubar", description="Tenta roubar créditos de outro membro")
@app_commands.checks.cooldown(1, 7200, key=lambda i: (i.guild_id, i.user.id))
@app_commands.describe(member="Membro alvo do roubo")
async def roubar(interaction: discord.Interaction, member: discord.Member):
    if member.id == interaction.user.id:
        await interaction.response.send_message("Voce nao pode roubar a si mesmo.", ephemeral=True)
        return
    if member.bot:
        await interaction.response.send_message("Voce nao pode roubar um bot.", ephemeral=True)
        return

    econ_cfg = panel_config.get_guild_config(interaction.guild.id, "economy")
    roubo_chance = econ_cfg.get("rob_success_chance", 40)
    roubo_max_percent = econ_cfg.get("rob_max_percent", 30)
    roubo_penalty_percent = econ_cfg.get("rob_penalty_percent", 20)

    async with economia_lock:
        sender_id = interaction.user.id
        target_id = member.id
        if sender_id not in economia:
            economia[sender_id] = 0
        if target_id not in economia:
            economia[target_id] = 0

        target_saldo = economia[target_id]
        if target_saldo < 50:
            await interaction.response.send_message("Esse membro nao tem creditos suficientes para roubar.", ephemeral=True)
            return

        if economia[sender_id] < 50:
            await interaction.response.send_message("Voce precisa de pelo menos 50 creditos para tentar roubar.", ephemeral=True)
            return

        sucesso = random.randint(1, 100) <= roubo_chance

        if sucesso:
            max_roubo = int(target_saldo * roubo_max_percent / 100)
            roubado = random.randint(1, max(1, max_roubo))
            economia[sender_id] += roubado
            economia[target_id] -= roubado
            await save_economia(economia)

            result_view = make_card(
                title="Roubo bem-sucedido",
                description=f"Voce roubou **{roubado} creditos** de {member.mention}.",
                color=0x00FF00,
                author_id=interaction.user.id,
            )
        else:
            multa = int(economia[sender_id] * roubo_penalty_percent / 100)
            multa = max(multa, 10)
            economia[sender_id] -= multa
            await save_economia(economia)

            motivo = random.choice(FRACASSOS_ROUBO)
            result_view = make_card(
                title="Roubo falhou",
                description=f"{motivo}\nVoce perdeu **{multa} creditos** de multa.",
                color=0xFF0000,
                author_id=interaction.user.id,
            )

    await interaction.response.send_message(view=result_view)


apostar_group = app_commands.Group(name="apostar", description="Comandos de apostas")
tree.add_command(apostar_group)


@apostar_group.command(name="coinflip", description="Aposta cara ou coroa")
@app_commands.describe(valor="Valor da aposta")
async def coinflip(interaction: discord.Interaction, valor: int):
    if valor <= 0:
        await interaction.response.send_message("Valor deve ser maior que 0.", ephemeral=True)
        return

    async with economia_lock:
        user_id = interaction.user.id
        if user_id not in economia:
            economia[user_id] = 0
        if economia[user_id] < valor:
            await interaction.response.send_message("Saldo insuficiente.", ephemeral=True)
            return

        resultado = random.choice(["cara", "coroa"])
        ganhou = random.choice([True, False])

        if ganhou:
            economia[user_id] += valor
            result_view = make_card(
                title=f"{resultado.capitalize()}",
                description=f"Voce ganhou **{valor} creditos**.\nSaldo: {economia[user_id]}",
                color=0x00FF00,
                author_id=interaction.user.id,
            )
        else:
            economia[user_id] -= valor
            result_view = make_card(
                title=f"{resultado.capitalize()}",
                description=f"Voce perdeu **{valor} creditos**.\nSaldo: {economia[user_id]}",
                color=0xFF0000,
                author_id=interaction.user.id,
            )
        await save_economia(economia)

    await interaction.response.send_message(view=result_view)


@apostar_group.command(name="roleta", description="Aposta na roleta (vermelho, preto ou verde)")
@app_commands.describe(valor="Valor da aposta", cor="Cor: vermelho, preto ou verde")
@app_commands.choices(cor=[
    app_commands.Choice(name="🔴 Vermelho (2x)", value="vermelho"),
    app_commands.Choice(name="⚫ Preto (2x)", value="preto"),
    app_commands.Choice(name="🟢 Verde (14x)", value="verde"),
])
async def roleta(interaction: discord.Interaction, valor: int, cor: app_commands.Choice[str]):
    if valor <= 0:
        await interaction.response.send_message("Valor deve ser maior que 0.", ephemeral=True)
        return

    async with economia_lock:
        user_id = interaction.user.id
        if user_id not in economia:
            economia[user_id] = 0
        if economia[user_id] < valor:
            await interaction.response.send_message("Saldo insuficiente.", ephemeral=True)
            return

        # Resultado: 48.6% vermelho, 48.6% preto, 2.7% verde
        roll = random.randint(0, 36)
        if roll == 0:
            resultado = "verde"
            emoji_resultado = "🟢"
        elif roll % 2 == 0:
            resultado = "vermelho"
            emoji_resultado = "🔴"
        else:
            resultado = "preto"
            emoji_resultado = "⚫"

        cor_escolhida = cor.value
        if cor_escolhida == resultado:
            multi = 14 if resultado == "verde" else 2
            ganho = valor * multi
            economia[user_id] += ganho - valor  # já apostou o valor
            result_view = make_card(
                title=f"{emoji_resultado} {resultado.capitalize()}",
                description=f"Voce apostou {cor_escolhida} e ganhou **{ganho} creditos** ({multi}x).\nSaldo: {economia[user_id]}",
                color=0x00FF00,
                author_id=interaction.user.id,
            )
        else:
            economia[user_id] -= valor
            result_view = make_card(
                title=f"{emoji_resultado} {resultado.capitalize()}",
                description=f"Voce apostou {cor_escolhida} mas saiu {resultado}. Perdeu **{valor} creditos**.\nSaldo: {economia[user_id]}",
                color=0xFF0000,
                author_id=interaction.user.id,
            )
        await save_economia(economia)

    await interaction.response.send_message(view=result_view)


# ========== MODERAÇÃO ==========

@tree.command(name="kick", description="Remove um membro do servidor")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.describe(member="Membro a ser removido", reason="Motivo da remoção")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Sem razão fornecida"):
    if not interaction.guild:
        await interaction.response.send_message("Esse comando so pode ser usado em servidores.", ephemeral=True)
        return

    # O autor não pode expulsar alguém com cargo igual/maior (salvo dono)
    if interaction.user != interaction.guild.owner and member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Voce nao pode expulsar alguem com cargo igual/maior que o seu.", ephemeral=True)
        return

    # O bot precisa ter cargo maior que o alvo
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("Nao posso expulsar esse membro (cargo maior/igual ao meu).", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.kick_members:
        await interaction.response.send_message("Nao tenho permissao de expulsar membros neste servidor.", ephemeral=True)
        return

    # Confirmação via botões
    mod_cfg = panel_config.get_guild_config(interaction.guild.id, "moderation")
    quick_reasons = mod_cfg.get('quick_reasons', [])
    emoji = mod_cfg.get('kick_emoji', '👢')
    dm_enabled = mod_cfg.get('dm_on_action', True)
    dm_msg = mod_cfg.get('kick_dm_message', 'Você foi expulso de {server}. Motivo: {reason}')

    # View com motivos rápidos + confirmar
    class KickReasonView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            for qr in quick_reasons[:5]:
                self.add_item(KickReasonButton(qr))
            self.add_item(ProceedKickButton())
        async def interaction_check(self, inter):
            return inter.user.id == interaction.user.id
    class KickReasonButton(discord.ui.Button):
        def __init__(self, motivo):
            super().__init__(label=motivo, style=discord.ButtonStyle.secondary)
            self.motivo = motivo
        async def callback(self, inter):
            nonlocal reason
            reason = self.motivo
            await inter.response.send_message(f"Motivo selecionado: {reason}", ephemeral=True)
    class ProceedKickButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label='Confirmar', style=discord.ButtonStyle.danger, emoji=emoji)
        async def callback(self, inter):
            self.view.stop()
            await inter.response.send_message('Processando expulsão...', ephemeral=True)
    view = KickReasonView()
    prompt_embed = discord.Embed(title='Expulsar membro', description=f'Selecione um motivo rapido ou use o fornecido: {reason}\nMembro: {member.mention}', color=discord.Color.orange())
    prompt_embed = _style_embed(interaction.guild, prompt_embed)
    await interaction.response.send_message(embed=prompt_embed, view=view, ephemeral=True)
    await view.wait()
    if any(isinstance(i, ProceedKickButton) for i in view.children) and not view.is_finished():
        return

    mod_cfg = panel_config.get_guild_config(interaction.guild.id, "moderation")
    color = mod_cfg.get("kick_color", 0xFF6B00)
    template = mod_cfg.get("kick_message", f"{emoji} {{user}} foi removido do servidor.\n**Motivo:** {{reason}}")
    
    # Validar hierarquia de cargos
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.followup.send(view=make_error("Não posso expulsar esse membro - ele tem cargo igual ou superior ao meu."), ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.followup.send(view=make_error("Você não pode expulsar esse membro - ele tem cargo igual ou superior ao seu."), ephemeral=True)
        return

    try:
        await member.kick(reason=reason)
        if dm_enabled and not member.bot:
            try:
                await member.send(dm_msg.format(server=interaction.guild.name, reason=reason))
            except Exception:
                pass
    except discord.Forbidden:
        await interaction.followup.send(view=make_error("Não tenho permissão para remover esse membro."), ephemeral=True)
    except discord.HTTPException:
        await interaction.followup.send(view=make_error("Falha ao tentar remover o membro. Tente novamente."), ephemeral=True)
    else:
        rendered = template.format(user=member.mention, reason=reason)
        kick_view = make_card(
            title="Membro removido",
            description=rendered,
            color=color,
            author_id=interaction.user.id,
        )
        await interaction.followup.send(view=kick_view, ephemeral=True)

        # Enviar log para o canal de logs (se configurado)
        guild_id = str(interaction.guild.id)
        if guild_id in config and 'log_channel_id' in config[guild_id]:
            log_channel_id = config[guild_id]['log_channel_id']
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="Membro removido (Kick)",
                    color=discord.Color.orange()
                )
                log_embed = _style_embed(interaction.guild, log_embed)
                log_embed.add_field(name="Usuário", value=f"{member} ({member.id})", inline=False)
                log_embed.add_field(name="Moderador", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Motivo", value=reason, inline=False)
                try:
                    await log_channel.send(embed=log_embed)
                except Exception:
                    pass

@tree.command(name="ban", description="Bane um membro do servidor")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(member="Membro a ser banido", reason="Motivo do banimento")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Sem razão fornecida"):
    if not interaction.guild:
        await interaction.response.send_message("Esse comando so pode ser usado em servidores.", ephemeral=True)
        return

    if interaction.user != interaction.guild.owner and member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Voce nao pode banir alguem com cargo igual/maior que o seu.", ephemeral=True)
        return

    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message("Nao posso banir esse membro (cargo maior/igual ao meu).", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("Nao tenho permissao de banir membros neste servidor.", ephemeral=True)
        return

    # Confirmação via botões
    mod_cfg = panel_config.get_guild_config(interaction.guild.id, "moderation")
    quick_reasons = mod_cfg.get('quick_reasons', [])
    emoji = mod_cfg.get('ban_emoji', '🚫')
    dm_enabled = mod_cfg.get('dm_on_action', True)
    dm_msg = mod_cfg.get('ban_dm_message', 'Você foi banido de {server}. Motivo: {reason}')

    class BanReasonView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            for qr in quick_reasons[:5]:
                self.add_item(BanReasonButton(qr))
            self.add_item(ProceedBanButton())
        async def interaction_check(self, inter):
            return inter.user.id == interaction.user.id
    class BanReasonButton(discord.ui.Button):
        def __init__(self, motivo):
            super().__init__(label=motivo, style=discord.ButtonStyle.secondary)
            self.motivo = motivo
        async def callback(self, inter):
            nonlocal reason
            reason = self.motivo
            await inter.response.send_message(f"Motivo selecionado: {reason}", ephemeral=True)
    class ProceedBanButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label='Confirmar', style=discord.ButtonStyle.danger, emoji=emoji)
        async def callback(self, inter):
            self.view.stop()
            await inter.response.send_message('Processando banimento...', ephemeral=True)
    view = BanReasonView()
    prompt_embed = discord.Embed(title='Banir membro', description=f'Selecione um motivo rapido ou use o fornecido: {reason}\nMembro: {member.mention}', color=discord.Color.orange())
    prompt_embed = _style_embed(interaction.guild, prompt_embed)
    await interaction.response.send_message(embed=prompt_embed, view=view, ephemeral=True)
    await view.wait()
    if any(isinstance(i, ProceedBanButton) for i in view.children) and not view.is_finished():
        return

    mod_cfg = panel_config.get_guild_config(interaction.guild.id, "moderation")
    color = mod_cfg.get("ban_color", 0xFF0000)
    template = mod_cfg.get("ban_message", f"{emoji} {{user}} foi banido do servidor.\n**Motivo:** {{reason}}")
    
    # Validar hierarquia de cargos
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.followup.send(view=make_error("Não posso banir esse membro - ele tem cargo igual ou superior ao meu."), ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.followup.send(view=make_error("Você não pode banir esse membro - ele tem cargo igual ou superior ao seu."), ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
        if dm_enabled and not member.bot:
            try:
                await member.send(dm_msg.format(server=interaction.guild.name, reason=reason))
            except Exception:
                pass
    except discord.Forbidden:
        await interaction.followup.send(view=make_error("Não tenho permissão para banir esse membro."), ephemeral=True)
    except discord.HTTPException:
        await interaction.followup.send(view=make_error("Falha ao tentar banir o membro. Tente novamente."), ephemeral=True)
    else:
        rendered = template.format(user=member.mention, reason=reason)
        ban_view = make_card(
            title="Membro banido",
            description=rendered,
            color=color,
            author_id=interaction.user.id,
        )
        await interaction.followup.send(view=ban_view, ephemeral=True)

        # Enviar log para o canal de logs (se configurado)
        guild_id = str(interaction.guild.id)
        if guild_id in config and 'log_channel_id' in config[guild_id]:
            log_channel_id = config[guild_id]['log_channel_id']
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="Membro banido",
                    color=discord.Color.red()
                )
                log_embed = _style_embed(interaction.guild, log_embed)
                log_embed.add_field(name="Usuário", value=f"{member} ({member.id})", inline=False)
                log_embed.add_field(name="Moderador", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Motivo", value=reason, inline=False)
                try:
                    await log_channel.send(embed=log_embed)
                except Exception:
                    pass

@tree.command(name="warn", description="Avisa um membro")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(member="Membro a ser avisado", reason="Motivo do aviso")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Sem razão"):
    mod_cfg = panel_config.get_guild_config(interaction.guild.id, "moderation")
    quick_reasons = mod_cfg.get('quick_reasons', [])
    if not reason or reason == 'Sem razão':
        # permitir escolha rápida
        class WarnReasonView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=45)
                for qr in quick_reasons[:5]:
                    self.add_item(WarnReasonButton(qr))
            async def interaction_check(self, inter):
                return inter.user.id == interaction.user.id
        class WarnReasonButton(discord.ui.Button):
            def __init__(self, motivo):
                super().__init__(label=motivo, style=discord.ButtonStyle.secondary)
                self.motivo = motivo
            async def callback(self, inter):
                nonlocal reason
                reason = self.motivo
                await inter.response.send_message(f"Motivo selecionado: {reason}", ephemeral=True)
                self.view.stop()
        view = WarnReasonView()
        prompt = discord.Embed(title='Selecionar motivo', description='Escolha um motivo rapido para o aviso.', color=0xFFA500)
        prompt = _style_embed(interaction.guild, prompt)
        await interaction.response.send_message(embed=prompt, view=view, ephemeral=True)
        await view.wait()
        if reason == 'Sem razão':
            reason = 'Aviso aplicado'
    emoji = mod_cfg.get('warn_emoji', '⚠️')
    dm_enabled = mod_cfg.get('dm_on_action', True)
    dm_msg = mod_cfg.get('warn_dm_message', 'Você recebeu um aviso em {server}: {reason}')
    color = mod_cfg.get("warn_color", 0xFFA500)
    template = mod_cfg.get("warn_message", f"{emoji} {{user}} recebeu um aviso.\n**Motivo:** {{reason}}")
    rendered = template.format(user=member.mention, reason=reason)
    warn_view = make_card(
        title="Aviso aplicado",
        description=rendered,
        color=color,
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=warn_view, ephemeral=True)
    if dm_enabled and not member.bot:
        try:
            await member.send(dm_msg.format(server=interaction.guild.name, reason=reason))
        except discord.Forbidden:
            await interaction.followup.send("Aviso aplicado, mas nao foi possivel enviar DM ao usuario.", ephemeral=True)
    # Persistir warn e verificar threshold
    warns_cfg = panel_config.get_guild_config(interaction.guild.id, 'moderation')
    threshold = warns_cfg.get('warn_threshold', 3)
    warn_store = warns_cfg.get('warn_store', {})
    user_key = str(member.id)
    current = warn_store.get(user_key, 0) + 1
    warn_store[user_key] = current
    panel_config.update_guild_config(interaction.guild.id, 'moderation', {'warn_store': warn_store})
    if current >= threshold:
        # Auto ação: ban
        try:
            await member.ban(reason=f"Acumulou {current} avisos")
            auto_view = make_card(
                title="Auto-Ban",
                description=f"{member.mention} banido automaticamente após {current} avisos.",
                color=0xFF0000,
            )
            await interaction.followup.send(view=auto_view, ephemeral=True)
        except Exception:
            pass

@tree.command(name="timeout", description="Aplica timeout em um membro (usa default se não informado)")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(member="Membro para timeout", minutos="Duração em minutos (deixe 0 para usar padrão)", motivo="Motivo")
async def timeout(interaction: discord.Interaction, member: discord.Member, minutos: int = 0, motivo: str = "Sem motivo"):
    mod_cfg = panel_config.get_guild_config(interaction.guild.id, 'moderation')
    default_minutes = mod_cfg.get('timeout_default_minutes', 10)
    real_minutes = minutos if minutos and minutos > 0 else default_minutes
    if real_minutes <= 0:
        await interaction.response.send_message("Duracao invalida.", ephemeral=True)
        return
    until = _utcnow() + datetime.timedelta(minutes=real_minutes)
    try:
        await member.edit(timed_out_until=until, reason=motivo)
        msg_template = mod_cfg.get('timeout_message', '⏳ {user} recebeu timeout por {minutes} min. Motivo: {reason}')
        rendered = msg_template.format(user=member.mention, minutes=real_minutes, reason=motivo)
        t_color = mod_cfg.get('warn_color', 0xFFA500)
        t_view = make_card(
            title="Timeout aplicado",
            description=rendered,
            color=t_color,
            author_id=interaction.user.id,
        )
        await interaction.response.send_message(view=t_view, ephemeral=True)
    except Exception:
        await interaction.response.send_message("Falha ao aplicar timeout.", ephemeral=True)

@tree.command(name="metricas", description="Mostra métricas básicas do bot no servidor")
async def metricas(interaction: discord.Interaction):
    tickets_cfg = panel_config.get_guild_config(interaction.guild.id, 'tickets')
    mod_cfg = panel_config.get_guild_config(interaction.guild.id, 'moderation')
    econ_cfg = panel_config.get_guild_config(interaction.guild.id, 'economy')
    warn_store = mod_cfg.get('warn_store', {})
    feedback_store = tickets_cfg.get('feedback_store', {})
    avg_feedback = 0
    if feedback_store:
        avg_feedback = sum(feedback_store.values())/len(feedback_store)
    total_credits = sum(economia.values()) if economia else 0
    metricas_view = make_card(
        title="Metricas do servidor",
        description="Use /stats para estatisticas detalhadas",
        color=discord.Color.purple(),
        fields=[
            ("Tickets", f"Criados: {tickets_cfg.get('ticket_counter',0)}\nFechados: {tickets_cfg.get('closed_counter',0)}"),
            ("Warns", f"Total warns registrados: {sum(warn_store.values())}"),
            ("Economia", f"Usuários: {len(economia)}\nCréditos totais: {total_credits}"),
            ("Feedback Médio", f"{avg_feedback:.2f}" if feedback_store else "Sem dados"),
        ],
        author_id=interaction.user.id,
    )
    await interaction.response.send_message(view=metricas_view, ephemeral=True)


# ========== CONFIGURAÇÃO ==========

@tree.command(name="setlog", description="Define o canal de logs de moderação para este servidor")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(canal="Canal de texto para receber os logs")
async def setlog(interaction: discord.Interaction, canal: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]['log_channel_id'] = canal.id
    await save_config(config)
    
    view = make_success(f"Logs de moderação serão enviados para {canal.mention}", author_id=interaction.user.id)
    await interaction.response.send_message(view=view, ephemeral=True)


# ==================== AUTO-MOD EVENTO ====================

_recent_messages = {}

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    mod_cfg = panel_config.get_guild_config(message.guild.id, 'moderation')
    am = mod_cfg.get('auto_mod', {})
    if not am.get('enabled'):
        await bot.process_commands(message)
        return
    try:
        now = asyncio.get_event_loop().time()
        user_key = (message.guild.id, message.author.id)
        window = am.get('cooldown_seconds',5)
        spam_limit = am.get('spam_limit',5)
        lst = _recent_messages.get(user_key, [])
        lst = [t for t in lst if now - t <= window]
        lst.append(now)
        _recent_messages[user_key] = lst
        violations = []
        if len(lst) > spam_limit:
            violations.append('spam')
        content = message.content or ''
        letters = [c for c in content if c.isalpha()]
        caps_ratio = (sum(1 for c in letters if c.isupper())/len(letters)) if letters else 0
        if caps_ratio >= am.get('caps_threshold',0.7) and len(letters) >= 10:
            violations.append('caps')
        if am.get('block_links', True) and ('http://' in content.lower() or 'https://' in content.lower()):
            violations.append('links')
        if content.count('@') >= am.get('max_mentions',5):
            violations.append('mentions')
        for bad in am.get('blacklist_words', []):
            if bad.lower() in content.lower():
                violations.append('blacklist')
                break
        if violations:
            action = am.get('action','delete')
            try:
                if action == 'delete':
                    await message.delete()
                elif action == 'warn':
                    await message.reply(f"Sua mensagem violou regras ({', '.join(set(violations))}).", delete_after=10)
            except Exception:
                pass
            # Log opcional
            log_channel_id = mod_cfg.get('log_channel_id')
            if log_channel_id:
                log_ch = message.guild.get_channel(log_channel_id)
                if log_ch:
                    log_embed = discord.Embed(title='Auto-Mod', description=f"Autor: {message.author.mention}\nViolações: {', '.join(set(violations))}", color=discord.Color.red(), timestamp=_utcnow())
                    log_embed = _style_embed(message.guild, log_embed)
                    try: await log_ch.send(embed=log_embed)
                    except Exception: pass
    except Exception:
        pass
    await bot.process_commands(message)


# ==================== EXECUTAR ====================

def _setup_interativo():
    """Setup interativo quando o .env não existe ou token está vazio."""
    print("\n" + "="*60)
    print("  CONFIGURACAO INICIAL DO BOT")
    print("="*60)
    print("\nO arquivo .env nao foi encontrado ou o token esta vazio.")
    print("\nPara obter o token do bot:")
    print("  1. Acesse: https://discord.com/developers/applications")
    print("  2. Clique no seu bot > Bot > Reset Token")
    print("  3. Copie o token gerado")
    print("\n  NUNCA compartilhe seu token com ninguem!\n")

    token = input("Cole o token do bot aqui: ").strip()
    if not token:
        print("\n  [ERRO] Token nao pode estar vazio. Tente novamente.")
        sys.exit(1)

    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"DISCORD_TOKEN={token}\n")

    print("\n  [OK] Token salvo com sucesso no arquivo .env!")
    print("   Iniciando o bot...\n")
    return token

# Verificar token antes de rodar
if not TOKEN or TOKEN == "SEU_TOKEN_AQUI":
    TOKEN = _setup_interativo()
    # Recarregar
    load_dotenv(override=True)
    TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN or TOKEN == "SEU_TOKEN_AQUI":
    print("\n  [ERRO] Token do bot nao configurado!")
    print("   Execute 'instalar.bat' ou edite o arquivo .env")
    print("   Coloque seu token na variável DISCORD_TOKEN\n")
    sys.exit(1)

try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("\n" + "="*60)
    print("  [ERRO] Token invalido!")
    print("="*60)
    print("\nO token que você colocou no .env está incorreto ou expirou.")
    print("\nPara corrigir:")
    print("  1. Acesse: https://discord.com/developers/applications")
    print("  2. Clique no seu bot > Bot > Reset Token")
    print("  3. Copie o novo token")
    print("  4. Edite o arquivo .env e cole o token")
    print("  5. Ou delete o .env e execute 'instalar.bat' novamente")
    print("="*60 + "\n")
    sys.exit(1)
except Exception as e:
    print(f"\n  [ERRO] Erro ao iniciar o bot: {e}")
    print("   Verifique sua conexão com a internet e tente novamente.\n")
    sys.exit(1)

