"""
Painel de Logs
Desenvolvido por: MARKIZIN
"""
import discord
from discord.ui import Button
from .panel_system import BasePanel, ChannelSelect
from typing import Dict, Any

LOG_CATEGORIES = [
    ("moderation", "Moderação", "🛡️"),
    ("messages", "Mensagens", "💬"),
    ("members", "Membros", "👥"),
    ("voice", "Voz", "🎙️"),
    ("server", "Servidor", "⚙️"),
]

class LogsPanel(BasePanel):
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, "logs")
        self._build_buttons()

    def _build_buttons(self):
        # Botão manual
        self.add_item(ManualLogsButton(self))
        
        # Botões por categoria: toggle + canal (rows 0-3)
        row_map = {"moderation":0, "messages":1, "members":2, "voice":3, "server":3}
        for key, label, emoji in LOG_CATEGORIES:
            self.add_item(ToggleCategoryButton(self, key, label, emoji, row_map[key]))
            self.add_item(SetCategoryChannelButton(self, key, label, emoji, row_map[key]))
        
        # Row 4: Navegação e controles
        self.add_item(BackLogsButton(self))
        self.add_item(CloseLogsButton(self))
        self.add_item(DeleteLogsButton(self))

    def create_embed(self) -> discord.Embed:
        cfg = self.get_config()
        embed = discord.Embed(
            title="📋 Painel de Logs",
            description="Configure canais e ativação de cada categoria de logs.",
            color=0x2F3136,
            timestamp=discord.utils.utcnow()
        )
        for key, label, emoji in LOG_CATEGORIES:
            cat = cfg.get(key, {})
            enabled = cat.get("enabled", False)
            channel_id = cat.get("channel_id")
            status = "🟢 Ativado" if enabled else "🔴 Desativado"
            channel_txt = f"<#{channel_id}>" if channel_id else "Não definido"
            embed.add_field(
                name=f"{emoji} {label}",
                value=f"Status: {status}\nCanal: {channel_txt}",
                inline=False
            )
        embed.set_footer(text="Escolha ativar e definir um canal para cada categoria.")
        embed = self.config_manager.apply_style(self.guild_id, embed)
        return embed

class ToggleCategoryButton(Button):
    def __init__(self, panel: LogsPanel, key: str, label: str, emoji: str, row: int):
        cfg = panel.get_config().get(key, {})
        enabled = cfg.get("enabled", False)
        super().__init__(
            label=f"{'Desativar' if enabled else 'Ativar'} {label}",
            style=discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success,
            emoji=emoji,
            row=row
        )
        self.panel = panel
        self.key = key
        self.label_txt = label
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config().get(self.key, {})
        new_state = not cfg.get("enabled", False)
        # Necessita de canal antes de ativar
        if new_state and not cfg.get("channel_id"):
            await self.panel.send_error(interaction, f"Defina um canal para {self.label_txt} antes de ativar.")
            return
        # Atualiza
        root = self.panel.get_config()
        root.setdefault(self.key, {})
        root[self.key]['enabled'] = new_state
        self.panel.update_config({self.key: root[self.key]})
        await self.panel.send_success(interaction, f"Logs de {self.label_txt} {'ativados' if new_state else 'desativados'}.")
        await self.panel.refresh(interaction)

class SetCategoryChannelButton(Button):
    def __init__(self, panel: LogsPanel, key: str, label: str, emoji: str, row: int):
        super().__init__(
            label=f"Canal {label}",
            style=discord.ButtonStyle.secondary,
            emoji="📢",
            row=row
        )
        self.panel = panel
        self.key = key
        self.label_txt = label
    async def callback(self, interaction: discord.Interaction):
        panel = self.panel
        key = self.key
        label = self.label_txt
        class ChannelView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                async def on_select(inter, channel):
                    root = panel.get_config()
                    root.setdefault(key, {})
                    root[key]['channel_id'] = channel.id
                    panel.update_config({key: root[key]})
                    await panel.send_success(inter, f"Canal de {label} definido: {channel.mention}")
                    await panel.refresh(inter)
                self.add_item(ChannelSelect(callback=on_select, placeholder=f"Selecione canal de {label}"))
        view = ChannelView()
        await interaction.response.send_message(
            f"📢 Selecione o canal para logs de {label}:",
            view=view,
            ephemeral=True
        )

class CloseLogsButton(Button):
    def __init__(self, panel: LogsPanel):
        super().__init__(label="Fechar", style=discord.ButtonStyle.secondary, emoji="❌", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        embed = discord.Embed(description="✅ Painel de logs fechado.", color=0x00FF00)
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()

class DeleteLogsButton(Button):
    def __init__(self, panel: LogsPanel):
        super().__init__(label="Apagar", style=discord.ButtonStyle.danger, emoji="🗑️", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        if getattr(interaction.message, 'flags', None) and interaction.message.flags.ephemeral:
            for item in self.panel.children:
                item.disabled = True
            embed = discord.Embed(description="✅ Painel fechado (efêmero).", color=0x00FF00)
            embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
            await interaction.response.edit_message(embed=embed, view=self.panel)
            self.panel.stop()
        else:
            await interaction.response.send_message("✅ Painel apagado com sucesso!", ephemeral=True)
            await interaction.message.delete()
            self.panel.stop()

class BackLogsButton(Button):
    def __init__(self, panel: LogsPanel):
        super().__init__(label="Voltar", style=discord.ButtonStyle.primary, emoji="🔙", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        from .panel_command import PanelMainView
        embed = discord.Embed(
            title="🎛️ Painel de Controle - Bot Premium",
            description=(
                "Bem-vindo ao **Centro de Configuração Interativo**!\n\n"
                "Selecione abaixo o módulo que deseja configurar.\n"
                "Todas as alterações são salvas automaticamente.\n\n"
                "**Módulos Disponíveis:**\n"
                "👋 **Boas-vindas** - Mensagem automática ao entrar (fácil!)\n"
                "🎫 **Tickets** - Sistema de suporte profissional\n"
                "💰 **Economia** - Créditos virtuais e loja\n"
                "🛡️ **Moderação** - Kick, ban, warn com logs\n"
                "📋 **Logs** - Registre tudo que acontece\n"
                "🎭 **Autorole** - Cargos automáticos\n"
                "😃 **Emojis Globais** - Emojis reutilizáveis\n\n"
                "**🆘 Precisa de ajuda?** Veja `docs/GUIA_RAPIDO.md`\n"
            ),
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="💡 Dica: Comece pelo módulo Tickets ou Boas-vindas | Desenvolvido por MARKIZIN")
        view = PanelMainView(self.panel.config_manager, interaction.guild.id, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)

class ManualLogsButton(Button):
    def __init__(self, panel: LogsPanel):
        super().__init__(label="Manual", style=discord.ButtonStyle.success, emoji="📖", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Manual do Sistema de Logs",
            description=(
                "**Guia para configurar registro completo de eventos do servidor.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x2F3136,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="📋 Categorias Disponíveis",
            value=(
                "🚫 **Moderação**: Bans, kicks, warns, mutes\n"
                "💬 **Mensagens**: Editadas, deletadas, fixadas\n"
                "👥 **Membros**: Entradas, saídas, atualizações\n"
                "🔊 **Voz**: Entradas/saídas de canais de voz\n"
                "🏛️ **Servidor**: Criação/deleção de canais/cargos"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Como Configurar",
            value=(
                "1️⃣ **Ativar categoria**: Clique no botão toggle da categoria\n"
                "2️⃣ **Definir canal**: Clique no botão de canal da categoria\n"
                "3️⃣ **Selecionar canal**: Escolha onde os logs aparecerão\n\n"
                "💡 **Dica**: Use canais separados para cada categoria"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📈 Exemplos de Uso",
            value=(
                "**#logs-moderação**: Todas as punições\n"
                "**#logs-mensagens**: Mensagens deletadas/editadas\n"
                "**#logs-entradas**: Membros entrando/saindo\n"
                "**#logs-geral**: Tudo em um só canal"
            ),
            inline=False
        )
        
        embed.set_footer(text="🚨 Importante: Canais de logs devem ser privados para staff!")
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)
