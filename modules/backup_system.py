"""
Sistema de Backup Automático
Desenvolvido por: MARKIZIN
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import zipfile
import shutil

class BackupSystem:
    def __init__(self, bot: commands.Bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, guild_id: int) -> str:
        """Cria um backup completo das configurações do servidor."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{guild_id}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        # Coletar todas as configurações
        backup_data = {
            "version": "1.0",
            "timestamp": timestamp,
            "guild_id": guild_id,
            "configs": {}
        }
        
        # Módulos para fazer backup
        modules = ["tickets", "welcome", "economy", "moderation", "logs", "autorole", "embeds", "emojis"]
        
        for module in modules:
            try:
                config = self.config_manager.get_guild_config(guild_id, module)
                backup_data["configs"][module] = config
            except:
                backup_data["configs"][module] = {}
        
        # Salvar backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        return str(backup_path)
    
    def restore_backup(self, guild_id: int, backup_file: str) -> bool:
        """Restaura configurações de um arquivo de backup."""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validar backup
            if backup_data.get("version") != "1.0":
                return False
            
            # Restaurar cada módulo
            for module, config in backup_data.get("configs", {}).items():
                if config:
                    self.config_manager.update_guild_config(guild_id, module, config)
            
            return True
        except Exception as e:
            print(f"Erro ao restaurar backup: {e}")
            return False
    
    def list_backups(self, guild_id: int) -> list:
        """Lista todos os backups disponíveis para um servidor."""
        backups = []
        for file in self.backup_dir.glob(f"backup_{guild_id}_*.json"):
            backups.append({
                "name": file.name,
                "path": str(file),
                "size": file.stat().st_size,
                "created": datetime.fromtimestamp(file.stat().st_ctime)
            })
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def cleanup_old_backups(self, guild_id: int, keep_last: int = 10):
        """Remove backups antigos, mantendo apenas os mais recentes."""
        backups = self.list_backups(guild_id)
        if len(backups) > keep_last:
            for backup in backups[keep_last:]:
                try:
                    os.remove(backup["path"])
                except:
                    pass

class BackupCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, backup_system: BackupSystem):
        self.bot = bot
        self.backup_system = backup_system
        self.auto_backup.start()
    
    def cog_unload(self):
        self.auto_backup.cancel()
    
    @tasks.loop(hours=24)
    async def auto_backup(self):
        """Backup automático a cada 24 horas."""
        for guild in self.bot.guilds:
            try:
                self.backup_system.create_backup(guild.id)
                self.backup_system.cleanup_old_backups(guild.id, keep_last=10)
                print(f"✅ Backup automático criado para {guild.name}")
            except Exception as e:
                print(f"❌ Erro no backup automático de {guild.name}: {e}")
    
    @auto_backup.before_loop
    async def before_auto_backup(self):
        await self.bot.wait_until_ready()
    
    @app_commands.command(name="backup", description="Cria backup das configurações do servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            backup_path = self.backup_system.create_backup(interaction.guild.id)
            
            embed = discord.Embed(
                title="✅ Backup Criado com Sucesso!",
                description=(
                    f"**Arquivo:** `{Path(backup_path).name}`\n"
                    f"**Data:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n\n"
                    "**Módulos incluídos:**\n"
                    "🎫 Tickets | 👋 Boas-vindas | 💰 Economia\n"
                    "🛡️ Moderação | 📋 Logs | 🎭 Autorole\n"
                    "🖌️ Embeds | 🧪 Emojis\n\n"
                    "Use `/restore` para restaurar este backup."
                ),
                color=0x00FF00,
                timestamp=datetime.now()
            )
            
            # Listar backups existentes
            backups = self.backup_system.list_backups(interaction.guild.id)
            if backups:
                backup_list = "\n".join([
                    f"• `{b['name']}` - {b['created'].strftime('%d/%m/%Y %H:%M')}"
                    for b in backups[:5]
                ])
                embed.add_field(
                    name=f"📦 Últimos Backups ({len(backups)} total)",
                    value=backup_list,
                    inline=False
                )
            
            embed.set_footer(text="💡 Backups automáticos são criados a cada 24h")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Limpar backups antigos
            self.backup_system.cleanup_old_backups(interaction.guild.id, keep_last=10)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro ao criar backup: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="restore", description="Restaura backup das configurações")
    @app_commands.checks.has_permissions(administrator=True)
    async def restore_command(self, interaction: discord.Interaction):
        backups = self.backup_system.list_backups(interaction.guild.id)
        
        if not backups:
            await interaction.response.send_message(
                "❌ Nenhum backup encontrado. Use `/backup` para criar um.",
                ephemeral=True
            )
            return
        
        # Criar view com select de backups
        class BackupSelect(discord.ui.Select):
            def __init__(self, backup_list, backup_system, guild_id):
                self.backup_system = backup_system
                self.guild_id = guild_id
                
                options = [
                    discord.SelectOption(
                        label=b["name"][:100],
                        description=f"Criado em {b['created'].strftime('%d/%m/%Y às %H:%M')}",
                        value=b["path"]
                    )
                    for b in backup_list[:25]
                ]
                
                super().__init__(
                    placeholder="Selecione um backup para restaurar...",
                    options=options,
                    min_values=1,
                    max_values=1
                )
            
            async def callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                backup_path = self.values[0]
                success = self.backup_system.restore_backup(self.guild_id, backup_path)
                
                if success:
                    embed = discord.Embed(
                        title="✅ Backup Restaurado!",
                        description=(
                            f"**Arquivo:** `{Path(backup_path).name}`\n\n"
                            "Todas as configurações foram restauradas com sucesso.\n"
                            "Use `/painel` para verificar as configurações."
                        ),
                        color=0x00FF00,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text="⚠️ Recomendado: Criar novo backup após mudanças importantes")
                else:
                    embed = discord.Embed(
                        title="❌ Erro ao Restaurar",
                        description="Não foi possível restaurar o backup selecionado.",
                        color=0xFF0000
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
        
        class BackupView(discord.ui.View):
            def __init__(self, backup_list, backup_system, guild_id):
                super().__init__(timeout=180)
                self.add_item(BackupSelect(backup_list, backup_system, guild_id))
        
        embed = discord.Embed(
            title="📦 Restaurar Backup",
            description=(
                "Selecione um backup para restaurar:\n\n"
                "⚠️ **ATENÇÃO:** Isso substituirá todas as configurações atuais!"
            ),
            color=0xFFA500
        )
        
        embed.add_field(
            name=f"Backups Disponíveis ({len(backups)})",
            value="\n".join([
                f"• `{b['name']}` - {b['created'].strftime('%d/%m/%Y %H:%M')}"
                for b in backups[:5]
            ]),
            inline=False
        )
        
        view = BackupView(backups, self.backup_system, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot, config_manager):
    """Configura o sistema de backup."""
    backup_system = BackupSystem(bot, config_manager)
    await bot.add_cog(BackupCommands(bot, backup_system))
    return backup_system
