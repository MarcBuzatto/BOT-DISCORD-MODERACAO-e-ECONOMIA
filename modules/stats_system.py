"""
Sistema de Estatísticas Avançadas
Desenvolvido por: MARKIZIN
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

class StatsSystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.stats_file = Path("stats.json")
        self.stats = self._load_stats()
    
    def _load_stats(self) -> dict:
        """Carrega estatísticas do arquivo."""
        if not self.stats_file.exists():
            return {}
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_stats(self):
        """Salva estatísticas no arquivo."""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estatísticas: {e}")
    
    def _ensure_guild_stats(self, guild_id: int):
        """Garante que a estrutura de estatísticas existe para o servidor."""
        guild_key = str(guild_id)
        if guild_key not in self.stats:
            self.stats[guild_key] = {
                "commands": {},  # {command_name: count}
                "tickets": {
                    "created": 0,
                    "closed": 0,
                    "avg_close_time": 0,
                    "by_category": {},
                    "by_user": {}
                },
                "economy": {
                    "daily_uses": 0,
                    "transfers": 0,
                    "total_transferred": 0,
                    "shop_purchases": 0
                },
                "moderation": {
                    "bans": 0,
                    "kicks": 0,
                    "mutes": 0,
                    "warns": 0,
                    "by_moderator": {}
                },
                "autorole": {
                    "roles_given": 0,
                    "roles_removed": 0,
                    "by_role": {}
                },
                "activity": {
                    "messages": 0,
                    "reactions": 0,
                    "voice_joins": 0
                },
                "last_reset": datetime.now().isoformat()
            }
    
    def track_command(self, guild_id: int, command_name: str):
        """Rastreia uso de comando."""
        self._ensure_guild_stats(guild_id)
        guild_key = str(guild_id)
        
        if command_name not in self.stats[guild_key]["commands"]:
            self.stats[guild_key]["commands"][command_name] = 0
        
        self.stats[guild_key]["commands"][command_name] += 1
        self._save_stats()
    
    def track_ticket(self, guild_id: int, action: str, category: str = None, user_id: int = None):
        """Rastreia ações de tickets."""
        self._ensure_guild_stats(guild_id)
        guild_key = str(guild_id)
        
        if action == "created":
            self.stats[guild_key]["tickets"]["created"] += 1
            if category:
                if category not in self.stats[guild_key]["tickets"]["by_category"]:
                    self.stats[guild_key]["tickets"]["by_category"][category] = 0
                self.stats[guild_key]["tickets"]["by_category"][category] += 1
            if user_id:
                user_key = str(user_id)
                if user_key not in self.stats[guild_key]["tickets"]["by_user"]:
                    self.stats[guild_key]["tickets"]["by_user"][user_key] = 0
                self.stats[guild_key]["tickets"]["by_user"][user_key] += 1
        elif action == "closed":
            self.stats[guild_key]["tickets"]["closed"] += 1
        
        self._save_stats()
    
    def track_economy(self, guild_id: int, action: str, amount: int = 0):
        """Rastreia ações de economia."""
        self._ensure_guild_stats(guild_id)
        guild_key = str(guild_id)
        
        if action == "daily":
            self.stats[guild_key]["economy"]["daily_uses"] += 1
        elif action == "transfer":
            self.stats[guild_key]["economy"]["transfers"] += 1
            self.stats[guild_key]["economy"]["total_transferred"] += amount
        elif action == "shop":
            self.stats[guild_key]["economy"]["shop_purchases"] += 1
        
        self._save_stats()
    
    def track_moderation(self, guild_id: int, action: str, moderator_id: int = None):
        """Rastreia ações de moderação."""
        self._ensure_guild_stats(guild_id)
        guild_key = str(guild_id)
        
        if action in ["ban", "kick", "mute", "warn"]:
            action_key = f"{action}s"
            self.stats[guild_key]["moderation"][action_key] += 1
            
            if moderator_id:
                mod_key = str(moderator_id)
                if mod_key not in self.stats[guild_key]["moderation"]["by_moderator"]:
                    self.stats[guild_key]["moderation"]["by_moderator"][mod_key] = {
                        "bans": 0, "kicks": 0, "mutes": 0, "warns": 0
                    }
                self.stats[guild_key]["moderation"]["by_moderator"][mod_key][action_key] += 1
        
        self._save_stats()
    
    def track_autorole(self, guild_id: int, action: str, role_id: int = None):
        """Rastreia ações de autorole."""
        self._ensure_guild_stats(guild_id)
        guild_key = str(guild_id)
        
        if action == "given":
            self.stats[guild_key]["autorole"]["roles_given"] += 1
        elif action == "removed":
            self.stats[guild_key]["autorole"]["roles_removed"] += 1
        
        if role_id:
            role_key = str(role_id)
            if role_key not in self.stats[guild_key]["autorole"]["by_role"]:
                self.stats[guild_key]["autorole"]["by_role"][role_key] = {"given": 0, "removed": 0}
            self.stats[guild_key]["autorole"]["by_role"][role_key][action] += 1
        
        self._save_stats()
    
    def get_guild_stats(self, guild_id: int) -> dict:
        """Retorna estatísticas completas do servidor."""
        self._ensure_guild_stats(guild_id)
        return self.stats.get(str(guild_id), {})
    
    def reset_guild_stats(self, guild_id: int):
        """Reseta estatísticas do servidor."""
        guild_key = str(guild_id)
        if guild_key in self.stats:
            del self.stats[guild_key]
        self._ensure_guild_stats(guild_id)
        self._save_stats()

class StatsView(discord.ui.View):
    def __init__(self, guild: discord.Guild, stats_system: StatsSystem):
        super().__init__(timeout=180)
        self.guild = guild
        self.stats_system = stats_system
        self.current_page = "overview"
    
    async def _update_view(self, interaction: discord.Interaction):
        """Atualiza a view com a página atual."""
        stats = self.stats_system.get_guild_stats(self.guild.id)
        
        if self.current_page == "overview":
            embed = self._create_overview_embed(stats)
        elif self.current_page == "commands":
            embed = self._create_commands_embed(stats)
        elif self.current_page == "tickets":
            embed = self._create_tickets_embed(stats)
        elif self.current_page == "economy":
            embed = self._create_economy_embed(stats)
        elif self.current_page == "moderation":
            embed = self._create_moderation_embed(stats)
        elif self.current_page == "autorole":
            embed = self._create_autorole_embed(stats)
        else:
            embed = self._create_overview_embed(stats)
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    def _create_overview_embed(self, stats: dict) -> discord.Embed:
        """Cria embed de visão geral."""
        embed = discord.Embed(
            title="📊 Estatísticas - Visão Geral",
            description=f"Servidor: **{self.guild.name}**",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        # Comandos mais usados
        commands = stats.get("commands", {})
        top_commands = sorted(commands.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_commands:
            cmd_text = "\n".join([f"`{cmd}` - {count}x" for cmd, count in top_commands])
        else:
            cmd_text = "Nenhum comando usado ainda"
        
        embed.add_field(
            name="🔝 Top 5 Comandos",
            value=cmd_text,
            inline=False
        )
        
        # Tickets
        tickets = stats.get("tickets", {})
        embed.add_field(
            name="🎫 Tickets",
            value=f"Criados: {tickets.get('created', 0)}\nFechados: {tickets.get('closed', 0)}",
            inline=True
        )
        
        # Economia
        economy = stats.get("economy", {})
        embed.add_field(
            name="💰 Economia",
            value=f"Daily: {economy.get('daily_uses', 0)}x\nTransferências: {economy.get('transfers', 0)}x",
            inline=True
        )
        
        # Moderação
        moderation = stats.get("moderation", {})
        total_actions = sum([
            moderation.get("bans", 0),
            moderation.get("kicks", 0),
            moderation.get("mutes", 0),
            moderation.get("warns", 0)
        ])
        embed.add_field(
            name="🛡️ Moderação",
            value=f"Total de ações: {total_actions}",
            inline=True
        )
        
        embed.set_footer(text="💡 Use os botões abaixo para ver detalhes de cada categoria")
        
        return embed
    
    def _create_commands_embed(self, stats: dict) -> discord.Embed:
        """Cria embed de estatísticas de comandos."""
        embed = discord.Embed(
            title="📊 Estatísticas - Comandos",
            description="Uso de comandos no servidor",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        commands = stats.get("commands", {})
        if not commands:
            embed.description = "Nenhum comando usado ainda."
            return embed
        
        sorted_commands = sorted(commands.items(), key=lambda x: x[1], reverse=True)
        total = sum(commands.values())
        
        # Top 10 comandos
        top_10 = sorted_commands[:10]
        cmd_list = []
        for i, (cmd, count) in enumerate(top_10, 1):
            percentage = (count / total) * 100
            bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
            cmd_list.append(f"`{i}.` **{cmd}** - {count}x ({percentage:.1f}%)\n{bar}")
        
        embed.add_field(
            name=f"🔝 Top 10 ({total} usos totais)",
            value="\n".join(cmd_list),
            inline=False
        )
        
        return embed
    
    def _create_tickets_embed(self, stats: dict) -> discord.Embed:
        """Cria embed de estatísticas de tickets."""
        embed = discord.Embed(
            title="📊 Estatísticas - Tickets",
            description="Sistema de suporte",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        tickets = stats.get("tickets", {})
        
        created = tickets.get("created", 0)
        closed = tickets.get("closed", 0)
        
        embed.add_field(
            name="📈 Geral",
            value=f"Criados: {created}\nFechados: {closed}\nAbertos: {created - closed}",
            inline=True
        )
        
        # Por categoria
        by_category = tickets.get("by_category", {})
        if by_category:
            cat_text = "\n".join([f"**{cat}**: {count}" for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:5]])
        else:
            cat_text = "Sem dados"
        
        embed.add_field(
            name="📂 Por Categoria (Top 5)",
            value=cat_text,
            inline=True
        )
        
        # Usuários mais ativos
        by_user = tickets.get("by_user", {})
        if by_user:
            top_users = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:5]
            user_text = "\n".join([f"<@{uid}>: {count}" for uid, count in top_users])
        else:
            user_text = "Sem dados"
        
        embed.add_field(
            name="👥 Usuários Mais Ativos",
            value=user_text,
            inline=False
        )
        
        return embed
    
    def _create_economy_embed(self, stats: dict) -> discord.Embed:
        """Cria embed de estatísticas de economia."""
        embed = discord.Embed(
            title="📊 Estatísticas - Economia",
            description="Sistema econômico do servidor",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        economy = stats.get("economy", {})
        
        embed.add_field(
            name="💵 Daily",
            value=f"Usos: {economy.get('daily_uses', 0)}x",
            inline=True
        )
        
        embed.add_field(
            name="💸 Transferências",
            value=f"Quantidade: {economy.get('transfers', 0)}x\nTotal: {economy.get('total_transferred', 0)} créditos",
            inline=True
        )
        
        embed.add_field(
            name="🛒 Loja",
            value=f"Compras: {economy.get('shop_purchases', 0)}x",
            inline=True
        )
        
        return embed
    
    def _create_moderation_embed(self, stats: dict) -> discord.Embed:
        """Cria embed de estatísticas de moderação."""
        embed = discord.Embed(
            title="📊 Estatísticas - Moderação",
            description="Ações de moderação no servidor",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        moderation = stats.get("moderation", {})
        
        embed.add_field(
            name="🔨 Ações",
            value=f"Bans: {moderation.get('bans', 0)}\nKicks: {moderation.get('kicks', 0)}\nMutes: {moderation.get('mutes', 0)}\nWarns: {moderation.get('warns', 0)}",
            inline=True
        )
        
        # Moderadores mais ativos
        by_mod = moderation.get("by_moderator", {})
        if by_mod:
            mod_totals = {mod: sum(actions.values()) for mod, actions in by_mod.items()}
            top_mods = sorted(mod_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            mod_text = "\n".join([f"<@{mid}>: {total} ações" for mid, total in top_mods])
        else:
            mod_text = "Sem dados"
        
        embed.add_field(
            name="👮 Moderadores Ativos",
            value=mod_text,
            inline=False
        )
        
        return embed
    
    def _create_autorole_embed(self, stats: dict) -> discord.Embed:
        """Cria embed de estatísticas de autorole."""
        embed = discord.Embed(
            title="📊 Estatísticas - Autorole",
            description="Sistema de cargos por reação",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        autorole = stats.get("autorole", {})
        
        embed.add_field(
            name="🎭 Geral",
            value=f"Cargos dados: {autorole.get('roles_given', 0)}\nCargos removidos: {autorole.get('roles_removed', 0)}",
            inline=False
        )
        
        # Cargos mais populares
        by_role = autorole.get("by_role", {})
        if by_role:
            role_totals = {role: data.get('given', 0) for role, data in by_role.items()}
            top_roles = sorted(role_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            role_text = "\n".join([f"<@&{rid}>: {count}x" for rid, count in top_roles])
        else:
            role_text = "Sem dados"
        
        embed.add_field(
            name="🏆 Cargos Mais Populares",
            value=role_text,
            inline=False
        )
        
        return embed
    
    @discord.ui.button(label="Visão Geral", style=discord.ButtonStyle.primary, emoji="📊", row=0)
    async def overview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = "overview"
        await self._update_view(interaction)
    
    @discord.ui.button(label="Comandos", style=discord.ButtonStyle.secondary, emoji="⚡", row=0)
    async def commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = "commands"
        await self._update_view(interaction)
    
    @discord.ui.button(label="Tickets", style=discord.ButtonStyle.secondary, emoji="🎫", row=0)
    async def tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = "tickets"
        await self._update_view(interaction)
    
    @discord.ui.button(label="Economia", style=discord.ButtonStyle.secondary, emoji="💰", row=0)
    async def economy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = "economy"
        await self._update_view(interaction)
    
    @discord.ui.button(label="Moderação", style=discord.ButtonStyle.secondary, emoji="🛡️", row=1)
    async def moderation_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = "moderation"
        await self._update_view(interaction)
    
    @discord.ui.button(label="Autorole", style=discord.ButtonStyle.secondary, emoji="🎭", row=1)
    async def autorole_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = "autorole"
        await self._update_view(interaction)
    
    @discord.ui.button(label="Resetar", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stats_system.reset_guild_stats(self.guild.id)
        
        embed = discord.Embed(
            title="✅ Estatísticas Resetadas",
            description="Todas as estatísticas foram reiniciadas.",
            color=0x00FF00
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.secondary, emoji="✖️", row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

class StatsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, stats_system: StatsSystem):
        self.bot = bot
        self.stats_system = stats_system
    
    @app_commands.command(name="stats", description="Mostra estatísticas avançadas do servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def stats_command(self, interaction: discord.Interaction):
        stats = self.stats_system.get_guild_stats(interaction.guild.id)
        
        embed = discord.Embed(
            title="📊 Estatísticas - Visão Geral",
            description=f"Servidor: **{interaction.guild.name}**",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        
        # Comandos mais usados
        commands = stats.get("commands", {})
        top_commands = sorted(commands.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_commands:
            cmd_text = "\n".join([f"`{cmd}` - {count}x" for cmd, count in top_commands])
        else:
            cmd_text = "Nenhum comando usado ainda"
        
        embed.add_field(
            name="🔝 Top 5 Comandos",
            value=cmd_text,
            inline=False
        )
        
        # Tickets
        tickets = stats.get("tickets", {})
        embed.add_field(
            name="🎫 Tickets",
            value=f"Criados: {tickets.get('created', 0)}\nFechados: {tickets.get('closed', 0)}",
            inline=True
        )
        
        # Economia
        economy = stats.get("economy", {})
        embed.add_field(
            name="💰 Economia",
            value=f"Daily: {economy.get('daily_uses', 0)}x\nTransferências: {economy.get('transfers', 0)}x",
            inline=True
        )
        
        # Moderação
        moderation = stats.get("moderation", {})
        total_actions = sum([
            moderation.get("bans", 0),
            moderation.get("kicks", 0),
            moderation.get("mutes", 0),
            moderation.get("warns", 0)
        ])
        embed.add_field(
            name="🛡️ Moderação",
            value=f"Total de ações: {total_actions}",
            inline=True
        )
        
        embed.set_footer(text="💡 Use os botões abaixo para ver detalhes de cada categoria")
        
        view = StatsView(interaction.guild, self.stats_system)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot, config_manager):
    """Configura o sistema de estatísticas."""
    stats_system = StatsSystem(config_manager)
    await bot.add_cog(StatsCommands(bot, stats_system))
    return stats_system
