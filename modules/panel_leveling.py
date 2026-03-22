"""
Painel de Configuração de Níveis/XP
Desenvolvido por: MARKIZIN
"""
import discord
from .panel_system import BasePanel, EditTextModal, ChannelSelect


class LevelingPanel(BasePanel):
    MODULE = "leveling"

    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, self.MODULE)
        self._build_buttons()

    def create_embed(self) -> discord.Embed:
        cfg = self.config_manager.get_guild_config(self.guild_id, self.MODULE)
        status = "Ativado" if cfg.get("enabled") else "Desativado"

        embed = discord.Embed(
            title="Configuracao de Niveis/XP",
            description=f"**Status:** {status}",
            color=0xFFD700
        )

        embed.add_field(
            name="Configuracoes",
            value=(
                f"XP por mensagem: **{cfg.get('xp_min', 15)}-{cfg.get('xp_max', 25)}**\n"
                f"Cooldown: **{cfg.get('xp_cooldown', 60)}s**\n"
                f"Canal de notificação: {'<#' + str(cfg.get('notify_channel_id')) + '>' if cfg.get('notify_channel_id') else 'Canal da mensagem'}\n"
            ),
            inline=False
        )

        level_roles = cfg.get("level_roles", {})
        if level_roles:
            roles_text = "\n".join(f"Nível {lvl}: <@&{rid}>" for lvl, rid in sorted(level_roles.items(), key=lambda x: int(x[0])))
            embed.add_field(name="Cargos por Nivel", value=roles_text, inline=False)
        else:
            embed.add_field(name="Cargos por Nivel", value="Nenhum configurado", inline=False)

        ignored = cfg.get("ignored_channels", [])
        if ignored:
            embed.add_field(name="Canais Ignorados", value=f"{len(ignored)} canais", inline=True)

        embed.set_footer(text="Desenvolvido por MARKIZIN")
        return embed

    def _build_buttons(self):
        cfg = self.config_manager.get_guild_config(self.guild_id, self.MODULE)

        self.add_item(ToggleLevelingButton(cfg.get("enabled", False)))
        self.add_item(SetXPRangeButton())
        self.add_item(SetCooldownButton())
        self.add_item(SetNotifyChannelButton())
        self.add_item(AddLevelRoleButton())
        self.add_item(SetLevelUpMessageButton())

        # Row 2: Back/Close
        self.add_item(BackButton(row=2))
        self.add_item(CloseButton(row=2))


class ToggleLevelingButton(discord.ui.Button):
    def __init__(self, enabled):
        label = "Desativar" if enabled else "Ativar"
        style = discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success
        super().__init__(label=label, style=style, row=0)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        cfg = panel.config_manager.get_guild_config(panel.guild_id, LevelingPanel.MODULE)
        new_val = not cfg.get("enabled", False)
        panel.config_manager.update_guild_config(panel.guild_id, LevelingPanel.MODULE, {"enabled": new_val})
        await panel.refresh(interaction)


class SetXPRangeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="XP por Msg", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        cfg = panel.config_manager.get_guild_config(panel.guild_id, LevelingPanel.MODULE)

        modal = EditTextModal(
            title="XP por Mensagem",
            label="Mínimo-Máximo (ex: 15-25)",
            default=f"{cfg.get('xp_min', 15)}-{cfg.get('xp_max', 25)}",
            max_length=10
        )

        async def on_submit(inter):
            try:
                parts = modal.result.split("-")
                xp_min = int(parts[0].strip())
                xp_max = int(parts[1].strip())
                if xp_min < 1 or xp_max < xp_min:
                    raise ValueError
                panel.config_manager.update_guild_config(panel.guild_id, LevelingPanel.MODULE, {"xp_min": xp_min, "xp_max": xp_max})
                await panel.refresh(inter)
            except (ValueError, IndexError):
                await panel.send_error(inter, "Formato inválido. Use: 15-25")

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


class SetCooldownButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cooldown", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        cfg = panel.config_manager.get_guild_config(panel.guild_id, LevelingPanel.MODULE)

        modal = EditTextModal(
            title="Cooldown de XP (segundos)",
            label="Segundos entre ganhos de XP",
            default=str(cfg.get("xp_cooldown", 60)),
            max_length=5
        )

        async def on_submit(inter):
            try:
                val = int(modal.result)
                if val < 5:
                    raise ValueError
                panel.config_manager.update_guild_config(panel.guild_id, LevelingPanel.MODULE, {"xp_cooldown": val})
                await panel.refresh(inter)
            except ValueError:
                await panel.send_error(inter, "Valor inválido. Mínimo: 5 segundos.")

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


class SetNotifyChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Canal Level-Up", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        select = ChannelSelect(panel, LevelingPanel.MODULE, "notify_channel_id")
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message("Selecione o canal para notificações de level-up:", view=view, ephemeral=True)


class AddLevelRoleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cargo por Nivel", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view

        modal = EditTextModal(
            title="Cargo por Nível",
            label="Nível:ID_do_cargo (ex: 5:123456789)",
            default="",
            max_length=50
        )

        async def on_submit(inter):
            try:
                parts = modal.result.split(":")
                level = str(int(parts[0].strip()))
                role_id = int(parts[1].strip())
                role = inter.guild.get_role(role_id)
                if not role:
                    await panel.send_error(inter, "Cargo não encontrado com esse ID.")
                    return
                cfg = panel.config_manager.get_guild_config(panel.guild_id, LevelingPanel.MODULE)
                level_roles = cfg.get("level_roles", {})
                level_roles[level] = role_id
                panel.config_manager.update_guild_config(panel.guild_id, LevelingPanel.MODULE, {"level_roles": level_roles})
                await panel.refresh(inter)
            except (ValueError, IndexError):
                await panel.send_error(inter, "Formato inválido. Use: NIVEL:ID_CARGO (ex: 5:123456789)")

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


class SetLevelUpMessageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Mensagem Level-Up", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        panel = self.view
        cfg = panel.config_manager.get_guild_config(panel.guild_id, LevelingPanel.MODULE)

        modal = EditTextModal(
            title="Mensagem de Level-Up",
            label="Use {user} e {level}",
            default=cfg.get("levelup_message", "{user} subiu para o **nivel {level}**"),
            max_length=200
        )

        async def on_submit(inter):
            panel.config_manager.update_guild_config(panel.guild_id, LevelingPanel.MODULE, {"levelup_message": modal.result})
            await panel.refresh(inter)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


class BackButton(discord.ui.Button):
    def __init__(self, row=2):
        super().__init__(label="Voltar", style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction):
        from .panel_command import PanelMainView, create_painel_command
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
