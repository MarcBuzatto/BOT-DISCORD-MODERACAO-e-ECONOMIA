"""
Comando Mestre de Painéis
Desenvolvido por: MARKIZIN
"""

import discord
from discord import app_commands
from discord.ui import Select, View
from .panel_welcome import WelcomePanel
from .panel_modules import EconomyPanel, ModerationPanel
from .panel_logs import LogsPanel
from .panel_autorole import AutorolePanel
from .panel_tickets import TicketsPanel
from .panel_system import ConfigManager


class PanelSelectMenu(Select):
    """Select menu para escolher o painel."""
    
    def __init__(self, config_manager: ConfigManager, guild_id: int, author_id: int):
        self.config_manager = config_manager
        self.guild_id = guild_id
        self.author_id = author_id
        
        options = [
            discord.SelectOption(
                label="Boas-vindas",
                description="Configure mensagens de boas-vindas",
                emoji="👋",
                value="welcome"
            ),
            discord.SelectOption(
                label="Economia",
                description="Configure o sistema de economia",
                emoji="💰",
                value="economy"
            ),
            discord.SelectOption(
                label="Moderação",
                description="Configure ações de moderação",
                emoji="🛡️",
                value="moderation"
            ),
            discord.SelectOption(
                label="Logs",
                description="Configure canais de registro",
                emoji="📋",
                value="logs"
            ),
            discord.SelectOption(
                label="Autorole",
                description="Configure cargos automáticos",
                emoji="🎭",
                value="autorole"
            ),
            discord.SelectOption(
                label="Embeds",
                description="Formato e estilo global dos embeds",
                emoji="🖌️",
                value="embeds"
            ),
            discord.SelectOption(
                label="Tickets",
                description="Sistema avançado de suporte",
                emoji="🎫",
                value="tickets"
            ),
            discord.SelectOption(
                label="Emojis Globais",
                description="Configuração de emojis reutilizáveis",
                emoji="😃",
                value="emojis"
            ),
            discord.SelectOption(
                label="Níveis/XP",
                description="Sistema de XP, níveis e cargos por nível",
                emoji="🏆",
                value="leveling"
            ),
            discord.SelectOption(
                label="Utilitários",
                description="Sugestões, starboard e configurações extras",
                emoji="🔧",
                value="utilities"
            )
        ]
        
        super().__init__(
            placeholder="Escolha um modulo para configurar",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        module = self.values[0]
        
        # Criar o painel apropriado
        if module == "welcome":
            panel = WelcomePanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "economy":
            panel = EconomyPanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "moderation":
            panel = ModerationPanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "logs":
            panel = LogsPanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "autorole":
            panel = AutorolePanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "embeds":
            from .panel_embeds import EmbedsPanel
            panel = EmbedsPanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "tickets":
            panel = TicketsPanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "emojis":
            from .panel_emojis import EmojisPanel
            panel = EmojisPanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "leveling":
            from .panel_leveling import LevelingPanel
            panel = LevelingPanel(self.config_manager, self.guild_id, self.author_id)
        elif module == "utilities":
            from .panel_utilities import UtilitiesPanel
            panel = UtilitiesPanel(self.config_manager, self.guild_id, self.author_id)
        else:
            await interaction.response.send_message(
                "Este modulo ainda nao esta disponivel.",
                ephemeral=True
            )
            return
        
        embed = panel.create_embed()
        await interaction.response.send_message(embed=embed, view=panel, ephemeral=True)
        panel.message = await interaction.original_response()


class PanelMainView(View):
    """View principal do comando /painel."""
    
    def __init__(self, config_manager: ConfigManager, guild_id: int, author_id: int):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.add_item(PanelSelectMenu(config_manager, guild_id, author_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Somente quem abriu o painel pode interagir.",
                ephemeral=True
            )
            return False
        return True


def create_painel_command(config_manager: ConfigManager) -> app_commands.Command:
    """Cria o comando /painel."""
    
    @app_commands.command(name="painel", description="Painel de configuracao completo do bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_command(interaction: discord.Interaction):
        """Abre o painel de configuração interativo."""
        
        embed = discord.Embed(
            title="Painel de Controle",
            description=(
                "Selecione abaixo o modulo que deseja configurar.\n"
                "Todas as alteracoes sao salvas automaticamente.\n\n"
                "**Modulos disponiveis:**\n"
                "Boas-vindas, Tickets, Economia, Moderacao,\n"
                "Logs, Autorole, Embeds, Emojis, Niveis/XP, Utilitarios\n\n"
                "**Outros comandos:**\n"
                "`/sorteio` `/trabalhar` `/roubar` `/apostar`\n"
                "`/rank` `/leaderboard` `/sugestao` `/enquete`\n"
                "`/lembrete` `/cargo-temp` `/serverinfo` `/userinfo`\n"
            ),
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(
            text="Desenvolvido por MARKIZIN"
        )
        
        view = PanelMainView(config_manager, interaction.guild.id, interaction.user.id)
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )
    
    return painel_command
