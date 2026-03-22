"""
Painel de Configuração de Utilitários
Desenvolvido por: MARKIZIN
"""
import discord
from .panel_system import BasePanel, ChannelSelect, EditTextModal


class UtilitiesPanel(BasePanel):
    MODULE = "utilities"

    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, self.MODULE)
        self._build_buttons()

    def create_embed(self) -> discord.Embed:
        cfg = self.config_manager.get_guild_config(self.guild_id, self.MODULE)

        embed = discord.Embed(
            title="Configuracao de Utilitarios",
            description="Configure sugestões, starboard e mais.",
            color=0x5865F2
        )

        # Sugestões
        sug_ch = cfg.get("suggestion_channel_id")
        embed.add_field(
            name="Sugestoes",
            value=f"Canal: {f'<#{sug_ch}>' if sug_ch else 'Nao configurado'}\nUso: `/sugestao <texto>`",
            inline=True
        )

        # Starboard
        star_ch = cfg.get("starboard_channel_id")
        star_thresh = cfg.get("starboard_threshold", 3)
        star_emoji = cfg.get("starboard_emoji", "⭐")
        embed.add_field(
            name=f"{star_emoji} Starboard",
            value=(
                f"Canal: {f'<#{star_ch}>' if star_ch else 'Nao configurado'}\n"
                f"Mínimo: {star_thresh} reações\n"
                f"Emoji: {star_emoji}"
            ),
            inline=True
        )

        embed.add_field(
            name="Outros Comandos",
            value=(
                "`/lembrete` — Criar lembretes\n"
                "`/cargo-temp` — Cargo temporário\n"
                "`/enquete` — Criar enquetes\n"
                "`/serverinfo` — Info do servidor\n"
                "`/userinfo` — Info de membro"
            ),
            inline=False
        )

        embed.set_footer(text="Desenvolvido por MARKIZIN")
        return embed

    def _build_buttons(self):
        self.add_item(SetSuggestionChannelButton())
        self.add_item(SetStarboardChannelButton())
        self.add_item(SetStarboardThresholdButton())
        self.add_item(SetStarboardEmojiButton())

        # Row 2: Back/Close
        self.add_item(BackButton(row=2))
        self.add_item(CloseButton(row=2))


class SetSuggestionChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Canal Sugestoes", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        select = ChannelSelect(panel, UtilitiesPanel.MODULE, "suggestion_channel_id")
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Selecione o canal de sugestões:", view=view, ephemeral=True)


class SetStarboardChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Canal Starboard", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        select = ChannelSelect(panel, UtilitiesPanel.MODULE, "starboard_channel_id")
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Selecione o canal do Starboard:", view=view, ephemeral=True)


class SetStarboardThresholdButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Minimo Estrelas", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        cfg = panel.config_manager.get_guild_config(panel.guild_id, UtilitiesPanel.MODULE)

        modal = EditTextModal(
            title="Mínimo de Reações para Starboard",
            label="Quantidade mínima de reações",
            default=str(cfg.get("starboard_threshold", 3)),
            max_length=3
        )

        async def on_submit(inter):
            try:
                val = int(modal.result)
                if val < 1 or val > 100:
                    raise ValueError
                panel.config_manager.update_guild_config(panel.guild_id, UtilitiesPanel.MODULE, {"starboard_threshold": val})
                await panel.refresh(inter)
            except ValueError:
                await panel.send_error(inter, "Valor inválido. Use um número entre 1 e 100.")

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


class SetStarboardEmojiButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Emoji Starboard", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        cfg = panel.config_manager.get_guild_config(panel.guild_id, UtilitiesPanel.MODULE)

        modal = EditTextModal(
            title="Emoji do Starboard",
            label="Emoji (ex: ⭐ ou 🌟)",
            default=cfg.get("starboard_emoji", "⭐"),
            max_length=10
        )

        async def on_submit(inter):
            panel.config_manager.update_guild_config(panel.guild_id, UtilitiesPanel.MODULE, {"starboard_emoji": modal.result.strip()})
            await panel.refresh(inter)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


class BackButton(discord.ui.Button):
    def __init__(self, row=2):
        super().__init__(label="Voltar", style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction):
        from .panel_command import PanelMainView
        panel = self.view
        embed = discord.Embed(
            title="Painel de Controle",
            description="Selecione um módulo para configurar.",
            color=0x5865F2
        )
        embed.set_footer(text="Desenvolvido por MARKIZIN")
        view = PanelMainView(panel.config_manager, panel.guild_id, panel.author_id)
        await interaction.response.edit_message(embed=embed, view=view)


class CloseButton(discord.ui.Button):
    def __init__(self, row=2):
        super().__init__(label="Fechar", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(title="Painel fechado", color=0x00FF00),
            view=None
        )
