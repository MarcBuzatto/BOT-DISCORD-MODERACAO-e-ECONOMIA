"""
Sistema de Permissões por Cargo
Desenvolvido por: MARKIZIN
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class PermissionSystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def get_panel_permissions(self, guild_id: int, panel_name: str) -> list:
        """Retorna lista de role_ids permitidos para um painel."""
        perms = self.config_manager.get_guild_config(guild_id, "permissions")
        return perms.get(panel_name, [])
    
    def set_panel_permissions(self, guild_id: int, panel_name: str, role_ids: list) -> bool:
        """Define quais cargos podem acessar um painel."""
        try:
            perms = self.config_manager.get_guild_config(guild_id, "permissions")
            perms[panel_name] = role_ids
            self.config_manager.update_guild_config(guild_id, "permissions", perms)
            return True
        except Exception as e:
            print(f"Erro ao configurar permissões: {e}")
            return False
    
    def add_role_permission(self, guild_id: int, panel_name: str, role_id: int) -> bool:
        """Adiciona um cargo à lista de permitidos."""
        try:
            perms = self.config_manager.get_guild_config(guild_id, "permissions")
            if panel_name not in perms:
                perms[panel_name] = []
            if role_id not in perms[panel_name]:
                perms[panel_name].append(role_id)
                self.config_manager.update_guild_config(guild_id, "permissions", perms)
            return True
        except Exception as e:
            print(f"Erro ao adicionar permissão: {e}")
            return False
    
    def remove_role_permission(self, guild_id: int, panel_name: str, role_id: int) -> bool:
        """Remove um cargo da lista de permitidos."""
        try:
            perms = self.config_manager.get_guild_config(guild_id, "permissions")
            if panel_name in perms and role_id in perms[panel_name]:
                perms[panel_name].remove(role_id)
                self.config_manager.update_guild_config(guild_id, "permissions", perms)
            return True
        except Exception as e:
            print(f"Erro ao remover permissão: {e}")
            return False
    
    def check_permission(self, member: discord.Member, panel_name: str) -> bool:
        """Verifica se um membro tem permissão para acessar um painel."""
        # Administradores sempre têm acesso
        if member.guild_permissions.administrator:
            return True
        
        allowed_roles = self.get_panel_permissions(member.guild.id, panel_name)
        
        # Se não há restrições, permite acesso
        if not allowed_roles:
            return member.guild_permissions.administrator
        
        # Verifica se o membro tem algum dos cargos permitidos
        member_role_ids = [role.id for role in member.roles]
        return any(role_id in member_role_ids for role_id in allowed_roles)
    
    def get_all_permissions(self, guild_id: int) -> dict:
        """Retorna todas as permissões configuradas no servidor."""
        return self.config_manager.get_guild_config(guild_id, "permissions")

class PermissionDecorator:
    """Decorator para verificar permissões antes de executar comandos."""
    
    def __init__(self, permission_system: PermissionSystem):
        self.permission_system = permission_system
    
    def require_panel_access(self, panel_name: str):
        """Decorator que verifica acesso ao painel."""
        def decorator(func):
            async def wrapper(interaction: discord.Interaction, *args, **kwargs):
                if not self.permission_system.check_permission(interaction.user, panel_name):
                    await interaction.response.send_message(
                        "❌ Você não tem permissão para acessar este painel.",
                        ephemeral=True
                    )
                    return
                return await func(interaction, *args, **kwargs)
            return wrapper
        return decorator

class PermissionPanel(discord.ui.View):
    def __init__(self, guild: discord.Guild, permission_system: PermissionSystem):
        super().__init__(timeout=180)
        self.guild = guild
        self.permission_system = permission_system
        self.current_panel = None
    
    @discord.ui.select(
        placeholder="Selecione um painel para configurar...",
        options=[
            discord.SelectOption(label="🎫 Tickets", value="tickets", description="Sistema de tickets"),
            discord.SelectOption(label="👋 Boas-vindas", value="welcome", description="Mensagens de boas-vindas"),
            discord.SelectOption(label="💰 Economia", value="economy", description="Sistema de economia"),
            discord.SelectOption(label="🛡️ Moderação", value="moderation", description="Comandos de moderação"),
            discord.SelectOption(label="📋 Logs", value="logs", description="Sistema de logs"),
            discord.SelectOption(label="🎭 Autorole", value="autorole", description="Reaction roles"),
            discord.SelectOption(label="🖌️ Embeds", value="embeds", description="Configuração de embeds"),
            discord.SelectOption(label="🧪 Emojis", value="emojis", description="Gerenciamento de emojis"),
        ],
        row=0
    )
    async def select_panel(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.current_panel = select.values[0]
        await self._show_panel_config(interaction)
    
    async def _show_panel_config(self, interaction: discord.Interaction):
        """Mostra configurações de permissão para o painel selecionado."""
        panel_names = {
            "tickets": "🎫 Tickets",
            "welcome": "👋 Boas-vindas",
            "economy": "💰 Economia",
            "moderation": "🛡️ Moderação",
            "logs": "📋 Logs",
            "autorole": "🎭 Autorole",
            "embeds": "🖌️ Embeds",
            "emojis": "🧪 Emojis"
        }
        
        allowed_roles = self.permission_system.get_panel_permissions(self.guild.id, self.current_panel)
        
        embed = discord.Embed(
            title=f"Permissões: {panel_names.get(self.current_panel, self.current_panel)}",
            description="Configure quais cargos podem acessar este painel.",
            color=0x5865F2
        )
        
        if allowed_roles:
            role_mentions = []
            for role_id in allowed_roles:
                role = self.guild.get_role(role_id)
                if role:
                    role_mentions.append(role.mention)
            
            embed.add_field(
                name="✅ Cargos Permitidos",
                value="\n".join(role_mentions) if role_mentions else "Nenhum cargo configurado",
                inline=False
            )
        else:
            embed.add_field(
                name="⚠️ Sem Restrições",
                value="Apenas administradores podem acessar este painel.\nAdicione cargos para permitir acesso.",
                inline=False
            )
        
        embed.set_footer(text="💡 Use os botões abaixo para gerenciar permissões")
        
        view = PermissionManageView(self.guild, self.permission_system, self.current_panel)
        await interaction.response.edit_message(embed=embed, view=view)

class PermissionManageView(discord.ui.View):
    def __init__(self, guild: discord.Guild, permission_system: PermissionSystem, panel_name: str):
        super().__init__(timeout=180)
        self.guild = guild
        self.permission_system = permission_system
        self.panel_name = panel_name
    
    @discord.ui.button(label="Adicionar Cargo", style=discord.ButtonStyle.success, emoji="➕", row=0)
    async def add_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione os cargos que podem acessar este painel:",
            view=RoleSelectView(self.guild, self.permission_system, self.panel_name, "add"),
            ephemeral=True
        )
    
    @discord.ui.button(label="Remover Cargo", style=discord.ButtonStyle.danger, emoji="➖", row=0)
    async def remove_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        allowed_roles = self.permission_system.get_panel_permissions(self.guild.id, self.panel_name)
        
        if not allowed_roles:
            await interaction.response.send_message(
                "❌ Nenhum cargo configurado para remover.",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            "Selecione os cargos para remover:",
            view=RoleSelectView(self.guild, self.permission_system, self.panel_name, "remove"),
            ephemeral=True
        )
    
    @discord.ui.button(label="Limpar Tudo", style=discord.ButtonStyle.secondary, emoji="🗑️", row=0)
    async def clear_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.permission_system.set_panel_permissions(self.guild.id, self.panel_name, [])
        
        embed = discord.Embed(
            title="✅ Permissões Limpas",
            description=f"Todas as permissões do painel foram removidas.\nApenas administradores podem acessar agora.",
            color=0x00FF00
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Voltar", style=discord.ButtonStyle.secondary, emoji="◀️", row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PermissionPanel(self.guild, self.permission_system)
        
        embed = discord.Embed(
            title="🔐 Gerenciamento de Permissões",
            description=(
                "Configure quais cargos podem acessar cada painel do bot.\n\n"
                "**Como funciona:**\n"
                "• Administradores sempre têm acesso total\n"
                "• Se não houver cargos configurados, apenas admins acessam\n"
                "• Adicione cargos para permitir acesso de usuários específicos\n"
            ),
            color=0x5865F2
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.secondary, emoji="✖️", row=1)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

class RoleSelectView(discord.ui.View):
    def __init__(self, guild: discord.Guild, permission_system: PermissionSystem, panel_name: str, action: str):
        super().__init__(timeout=180)
        self.guild = guild
        self.permission_system = permission_system
        self.panel_name = panel_name
        self.action = action
        
        # Criar select de roles
        if action == "add":
            # Mostrar todos os cargos (exceto @everyone)
            roles = [r for r in guild.roles if r.id != guild.id and not r.managed][:25]
        else:
            # Mostrar apenas cargos já permitidos
            allowed_ids = permission_system.get_panel_permissions(guild.id, panel_name)
            roles = [guild.get_role(rid) for rid in allowed_ids if guild.get_role(rid)][:25]
        
        if not roles:
            return
        
        options = [
            discord.SelectOption(
                label=role.name[:100],
                value=str(role.id),
                description=f"{len([m for m in guild.members if role in m.roles])} membros"
            )
            for role in roles
        ]
        
        self.role_select = discord.ui.Select(
            placeholder="Selecione um ou mais cargos...",
            options=options,
            min_values=1,
            max_values=len(options)
        )
        self.role_select.callback = self._role_callback
        self.add_item(self.role_select)
    
    async def _role_callback(self, interaction: discord.Interaction):
        selected_ids = [int(val) for val in self.role_select.values]
        
        if self.action == "add":
            for role_id in selected_ids:
                self.permission_system.add_role_permission(self.guild.id, self.panel_name, role_id)
            
            roles_str = ", ".join([f"<@&{rid}>" for rid in selected_ids])
            
            embed = discord.Embed(
                title="✅ Cargos Adicionados",
                description=f"Os seguintes cargos agora podem acessar o painel:\n{roles_str}",
                color=0x00FF00
            )
        else:
            for role_id in selected_ids:
                self.permission_system.remove_role_permission(self.guild.id, self.panel_name, role_id)
            
            roles_str = ", ".join([f"<@&{rid}>" for rid in selected_ids])
            
            embed = discord.Embed(
                title="✅ Cargos Removidos",
                description=f"Os seguintes cargos não podem mais acessar o painel:\n{roles_str}",
                color=0x00FF00
            )
        
        await interaction.response.edit_message(embed=embed, view=None)

class PermissionCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, permission_system: PermissionSystem):
        self.bot = bot
        self.permission_system = permission_system
    
    @app_commands.command(name="permissoes", description="Gerencia permissões de acesso aos painéis")
    @app_commands.checks.has_permissions(administrator=True)
    async def permissions_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔐 Gerenciamento de Permissões",
            description=(
                "Configure quais cargos podem acessar cada painel do bot.\n\n"
                "**Como funciona:**\n"
                "• Administradores sempre têm acesso total\n"
                "• Se não houver cargos configurados, apenas admins acessam\n"
                "• Adicione cargos para permitir acesso de usuários específicos\n\n"
                "**Painéis disponíveis:**\n"
                "🎫 Tickets | 👋 Boas-vindas | 💰 Economia\n"
                "🛡️ Moderação | 📋 Logs | 🎭 Autorole\n"
                "🖌️ Embeds | 🧪 Emojis"
            ),
            color=0x5865F2
        )
        
        embed.set_footer(text="💡 Selecione um painel abaixo para configurar")
        
        view = PermissionPanel(interaction.guild, self.permission_system)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot, config_manager):
    """Configura o sistema de permissões."""
    permission_system = PermissionSystem(config_manager)
    await bot.add_cog(PermissionCommands(bot, permission_system))
    return permission_system
