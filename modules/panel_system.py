"""
Sistema de Painéis Interativos - Arquitetura Base
Desenvolvido por: MARKIZIN
"""

import discord
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
from typing import Dict, Any, Optional, Callable
import json
from pathlib import Path
import re
from datetime import datetime, timezone

# Helper para datetime UTC
def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ==================== UTILIDADES ====================

def validate_hex_color(color: str) -> Optional[int]:
    """Valida e converte cor hexadecimal para int."""
    color = color.strip().replace('#', '')
    if re.match(r'^[0-9A-Fa-f]{6}$', color):
        return int(color, 16)
    return None


def validate_url(url: str) -> bool:
    """Valida se é uma URL válida de imagem."""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


# ==================== CONFIG MANAGER ====================

class ConfigManager:
    """Gerenciador central de configurações com persistência."""
    
    def __init__(self, file_path: str = "panel_config.json"):
        self.file_path = Path(file_path)
        self.config: Dict[str, Any] = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Carrega configurações do arquivo."""
        if not self.file_path.exists():
            return self._get_default_config()
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão para todos os módulos."""
        return {
            "welcome": {
                "enabled": False,
                "channel_id": None,
                "title": "🎉 Bem-vindo(a) ao servidor!",
                "description": "Seja bem-vindo(a), {user}! Esperamos que você se divirta aqui.",
                "footer": "Aproveite sua estadia!",
                "color": 0x00FF00,
                "image_url": None,
                "thumbnail_url": None,
                "role_id": None,
                "mention_role": None,
                "random_messages": [],
                "dm_enabled": False,
                "dm_message": "Olá {user}, bem-vindo ao {server}!",
                "restore_roles": False,
                "member_counter": True,
                "leave_enabled": False,
                "leave_channel_id": None,
                "leave_message": "👋 {user} saiu do servidor.",
                "welcome_emoji": "🎉",
                "counter_emoji": "#️⃣"
            },
            "economy": {
                "daily_amount": 100,
                "daily_cooldown": 86400,
                "transfer_enabled": True,
                "saldo_color": 0xFFD700,
                "daily_color": 0x00FF00,
                "shop_enabled": False,
                "shop_items": [],
                "shop_currency_name": "créditos",
                "daily_success_message": "💰 Você coletou {amount} {currency}! Saldo atual: {balance}",
                "daily_emoji": "💰",
                "transfer_success_message": "💸 {sender} transferiu {amount} {currency} para {receiver}.",
                "buy_success_message": "✅ Você comprou **{item}** por {price} {currency}.",
                "insufficient_funds_message": "❌ Saldo insuficiente! Você tem {balance} {currency}.",
                "currency_emoji": "💎"
            },
            "moderation": {
                "log_channel_id": None,
                "kick_message": "👢 {user} foi removido do servidor.\n**Motivo:** {reason}",
                "ban_message": "🚫 {user} foi banido do servidor.\n**Motivo:** {reason}",
                "warn_message": "⚠️ {user} recebeu um aviso.\n**Motivo:** {reason}",
                "kick_color": 0xFF6B00,
                "ban_color": 0xFF0000,
                "warn_color": 0xFFA500,
                "require_confirmation": True,
                "auto_mod": {
                    "enabled": False,
                    "spam_limit": 5,
                    "caps_threshold": 0.7,
                    "blacklist_words": [],
                    "block_links": True,
                    "max_mentions": 5,
                    "action": "delete",  # delete | warn
                    "cooldown_seconds": 5
                },
                "warn_threshold": 3,
                "timeout_default_minutes": 30,
                "quick_reasons": ["Spam", "Desrespeito", "Conteúdo impróprio", "Flood", "Divulgação não autorizada"],
                "timeout_message": "⏳ {user} recebeu timeout por {minutes} min. Motivo: {reason}",
                "dm_on_action": True,
                "kick_dm_message": "Você foi removido de {server}. Motivo: {reason}",
                "ban_dm_message": "Você foi banido de {server}. Motivo: {reason}",
                "warn_dm_message": "Você recebeu um aviso em {server}. Motivo: {reason}",
                "warn_emoji": "⚠️",
                "kick_emoji": "👢",
                "ban_emoji": "🚫"
            },
            "logs": {
                "moderation": {"enabled": False, "channel_id": None},
                "messages": {"enabled": False, "channel_id": None},
                "members": {"enabled": False, "channel_id": None},
                "voice": {"enabled": False, "channel_id": None},
                "server": {"enabled": False, "channel_id": None}
            },
            "autorole": {
                "enabled": False,
                "reaction_roles": []
            },
            "tickets": {
                "enabled": False,
                "panel_channel_id": None,
                "category_id": None,
                "category_ids": [],
                "support_role_ids": [],
                "claim_required": False,
                "feedback_enabled": True,
                "transcript_enabled": True,
                "transcript_format": "html",
                "auto_close_minutes": None,
                "max_open_per_user": 3,
                "ticket_counter": 0,
                "closed_counter": 0,
                "feedback_store": {},
                "panel_title": "🎫 Suporte - Abra um Ticket",
                "panel_description": "Clique no botão abaixo para abrir um ticket de suporte. Use somente se realmente precisar de ajuda.",
                "panel_color": 0x5865F2,
                "panel_button_label": "Abrir Ticket",
                "panel_button_emoji": "🎫",
                "ticket_open_title": "🎫 Ticket Criado",
                "ticket_open_description": "Explique seu problema. Um membro da equipe responderá em breve.",
                "ticket_name_template": "ticket-{counter}",
                "require_initial_form": False,
                "initial_form_subject_label": "Assunto do Ticket",
                "initial_form_description_label": "Descrição Detalhada",
                "enable_priority": False,
                "priorities": ["🔴 Urgente", "🟡 Normal", "🟢 Baixa"],
                "sla_minutes": None,
                "sla_alert_role_ids": [],
                "escalation_minutes": None,
                "escalation_role_ids": []
            },
            "embed_style": {
                "default_color": 0x5865F2,
                "footer_text": "Desenvolvido por MARKIZIN",
                "footer_icon": None,
                "use_timestamp": True,
                "thumbnail_url": None,
                "author_name": None,
                "author_icon": None
            },
            "leveling": {
                "enabled": False,
                "xp_min": 15,
                "xp_max": 25,
                "xp_cooldown": 60,
                "notify_channel_id": None,
                "levelup_message": "🎉 {user} subiu para o **nível {level}**!",
                "levelup_color": 0xFFD700,
                "level_roles": {},
                "ignored_channels": []
            },
            "utilities": {
                "suggestion_channel_id": None,
                "starboard_channel_id": None,
                "starboard_threshold": 3,
                "starboard_emoji": "⭐",
                "starboard_posted": []
            }
        }
    
    def save(self):
        """Salva configurações no arquivo de forma atômica."""
        tmp = self.file_path.with_suffix('.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        tmp.replace(self.file_path)
    
    def get_guild_config(self, guild_id: int, module: str) -> Dict[str, Any]:
        """Retorna configuração de um módulo específico de uma guilda."""
        guild_key = str(guild_id)
        if guild_key not in self.config:
            self.config[guild_key] = self._get_default_config()
            self.save()
        return self.config[guild_key].get(module, {})
    
    def set_guild_config(self, guild_id: int, module: str, key: str, value: Any):
        """Define uma configuração específica."""
        guild_key = str(guild_id)
        if guild_key not in self.config:
            self.config[guild_key] = self._get_default_config()
        if module not in self.config[guild_key]:
            self.config[guild_key][module] = {}
        self.config[guild_key][module][key] = value
        self.save()
    
    def update_guild_config(self, guild_id: int, module: str, data: Dict[str, Any]):
        """Atualiza múltiplas configurações de uma vez."""
        guild_key = str(guild_id)
        if guild_key not in self.config:
            self.config[guild_key] = self._get_default_config()
        if module not in self.config[guild_key]:
            self.config[guild_key][module] = {}
        self.config[guild_key][module].update(data)
        self.save()

    # ======== APLICAÇÃO DE ESTILO GLOBAL ========
    def apply_style(self, guild_id: int, embed: discord.Embed) -> discord.Embed:
        """Aplica estilo global configurado ao embed."""
        style = self.get_guild_config(guild_id, "embed_style")
        if style.get("default_color") and embed.color is None:
            embed.color = style.get("default_color")
        if style.get("use_timestamp") and embed.timestamp is None:
            embed.timestamp = _utcnow()
        if style.get("footer_text") and (not embed.footer or not embed.footer.text):
            footer_icon = style.get("footer_icon")
            if footer_icon:
                embed.set_footer(text=style.get("footer_text"), icon_url=footer_icon)
            else:
                embed.set_footer(text=style.get("footer_text"))
        if style.get("thumbnail_url") and not embed.thumbnail:
            embed.set_thumbnail(url=style.get("thumbnail_url"))
        # Author override
        if style.get("author_name"):
            author_icon = style.get("author_icon")
            if author_icon:
                embed.set_author(name=style.get("author_name"), icon_url=author_icon)
            else:
                embed.set_author(name=style.get("author_name"))
        return embed


# ==================== MODALS ====================

class EditTextModal(Modal):
    """Modal genérico para edição de textos."""
    
    def __init__(self, title: str, fields: Dict[str, Dict[str, Any]], callback: Callable):
        super().__init__(title=title, timeout=300)
        self.callback_func = callback
        self.inputs = {}
        
        for key, config in fields.items():
            text_input = TextInput(
                label=config.get('label', key),
                placeholder=config.get('placeholder', ''),
                default=config.get('default', ''),
                required=config.get('required', True),
                max_length=config.get('max_length', 1024),
                style=config.get('style', discord.TextStyle.short)
            )
            self.add_item(text_input)
            self.inputs[key] = text_input
    
    async def on_submit(self, interaction: discord.Interaction):
        data = {key: inp.value for key, inp in self.inputs.items()}
        await self.callback_func(interaction, data)


class ColorPickerModal(Modal, title="🎨 Escolher Cor"):
    """Modal para seleção de cor hexadecimal."""
    
    color_input = TextInput(
        label="Cor (Hexadecimal)",
        placeholder="#00FF00 ou 00FF00",
        required=True,
        max_length=7
    )
    
    def __init__(self, callback: Callable):
        super().__init__()
        self.callback_func = callback
    
    async def on_submit(self, interaction: discord.Interaction):
        color_value = validate_hex_color(self.color_input.value)
        if color_value is None:
            await interaction.response.send_message(
                "❌ Cor inválida! Use formato hexadecimal (ex: #00FF00 ou 00FF00)",
                ephemeral=True
            )
            return
        await self.callback_func(interaction, color_value)


class ImageURLModal(Modal, title="🖼️ Definir Imagem"):
    """Modal para definir URL de imagem."""
    
    url_input = TextInput(
        label="URL da Imagem",
        placeholder="https://exemplo.com/imagem.png",
        required=True,
        max_length=512,
        style=discord.TextStyle.short
    )
    
    def __init__(self, callback: Callable, field_type: str = "image"):
        super().__init__()
        self.callback_func = callback
        self.field_type = field_type
    
    async def on_submit(self, interaction: discord.Interaction):
        url = self.url_input.value.strip()
        if not validate_url(url):
            await interaction.response.send_message(
                "❌ URL inválida! Use uma URL completa começando com http:// ou https://",
                ephemeral=True
            )
            return
        await self.callback_func(interaction, url, self.field_type)


# ==================== BASE PANEL VIEW ====================

class BasePanel(View):
    """Classe base para todos os painéis de configuração."""
    
    def __init__(self, config_manager: ConfigManager, guild_id: int, author_id: int, module: str):
        super().__init__(timeout=300)
        self.config_manager = config_manager
        self.guild_id = guild_id
        self.author_id = author_id
        self.module = module
        self.message: Optional[discord.Message] = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Verifica se o usuário pode usar o painel."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Somente quem abriu o painel pode usa-lo.",
                ephemeral=True
            )
            return False
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna a configuração do módulo."""
        return self.config_manager.get_guild_config(self.guild_id, self.module)
    
    def update_config(self, data: Dict[str, Any]):
        """Atualiza configuração do módulo."""
        self.config_manager.update_guild_config(self.guild_id, self.module, data)
    
    def create_embed(self) -> discord.Embed:
        """Cria o embed do painel. Deve ser sobrescrito."""
        raise NotImplementedError
    
    async def refresh(self, interaction: discord.Interaction):
        """Atualiza o painel."""
        embed = self.create_embed()
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.InteractionResponded:
            await interaction.followup.edit_message(self.message.id, embed=embed, view=self)
    
    async def send_success(self, interaction: discord.Interaction, message: str):
        """Envia mensagem de sucesso ephemeral."""
        embed = discord.Embed(
            description=f"✅ {message}",
            color=0x00FF00,
            timestamp=_utcnow()
        )
        embed = self.config_manager.apply_style(self.guild_id, embed)
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def send_error(self, interaction: discord.Interaction, message: str):
        """Envia mensagem de erro ephemeral."""
        embed = discord.Embed(
            description=f"❌ {message}",
            color=0xFF0000,
            timestamp=_utcnow()
        )
        embed = self.config_manager.apply_style(self.guild_id, embed)
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def on_timeout(self):
        """Desabilita todos os botões ao expirar."""
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


# ==================== SELECT MENUS ====================

class ChannelSelect(discord.ui.ChannelSelect):
    """Select menu para escolher canal."""
    
    def __init__(self, callback: Callable, placeholder: str = "Selecione um canal"):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]
        )
        self.callback_func = callback
    
    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        await self.callback_func(interaction, channel)


class RoleSelect(discord.ui.RoleSelect):
    """Select menu para escolher cargo."""
    
    def __init__(self, callback: Callable, placeholder: str = "Selecione um cargo"):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1
        )
        self.callback_func = callback
    
    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        await self.callback_func(interaction, role)

