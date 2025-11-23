"""
Sistema de Importação e Exportação de Configurações
Desenvolvido por: MARKIZIN
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
from pathlib import Path

class ImportExportSystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
    def export_config(self, guild_id: int, modules: list = None, include_sensitive: bool = False) -> str:
        """Exporta configurações selecionadas para compartilhamento."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"export_{guild_id}_{timestamp}.json"
        export_path = self.export_dir / export_name
        
        # Módulos disponíveis para exportar
        all_modules = ["tickets", "welcome", "economy", "moderation", "logs", "autorole", "embeds", "emojis", "theme"]
        if modules is None:
            modules = all_modules
        
        export_data = {
            "version": "1.0",
            "export_type": "config_share",
            "timestamp": timestamp,
            "modules": {}
        }
        
        for module in modules:
            if module not in all_modules:
                continue
            
            try:
                config = self.config_manager.get_guild_config(guild_id, module)
                
                # Filtrar dados sensíveis se necessário
                if not include_sensitive:
                    config = self._remove_sensitive_data(module, config)
                
                export_data["modules"][module] = config
            except:
                export_data["modules"][module] = {}
        
        # Salvar exportação
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(export_path)
    
    def _remove_sensitive_data(self, module: str, config: dict) -> dict:
        """Remove dados sensíveis das configurações para compartilhamento."""
        sensitive_keys = {
            "tickets": ["ticket_counter", "closed_counter", "feedback_store"],
            "economy": [],  # Economia não tem dados sensíveis de config
            "moderation": ["warn_store"],
            "logs": ["log_channel_id"],  # IDs de canais específicos
            "autorole": ["target_message_id", "target_channel_id"],
            "welcome": ["welcome_channel_id", "goodbye_channel_id", "autorole_id"],
            "embeds": [],
            "emojis": [],
            "theme": []
        }
        
        filtered = config.copy()
        for key in sensitive_keys.get(module, []):
            if key in filtered:
                del filtered[key]
        
        return filtered
    
    def import_config(self, guild_id: int, import_file: str, modules: list = None, merge: bool = True) -> dict:
        """Importa configurações de um arquivo de exportação."""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validar formato
            if import_data.get("version") != "1.0":
                return {"success": False, "error": "Versão incompatível"}
            
            imported = []
            skipped = []
            
            for module, config in import_data.get("modules", {}).items():
                if modules and module not in modules:
                    skipped.append(module)
                    continue
                
                if not config:
                    skipped.append(module)
                    continue
                
                try:
                    if merge:
                        # Mesclar com configurações existentes
                        existing = self.config_manager.get_guild_config(guild_id, module)
                        existing.update(config)
                        self.config_manager.update_guild_config(guild_id, module, existing)
                    else:
                        # Substituir completamente
                        self.config_manager.update_guild_config(guild_id, module, config)
                    
                    imported.append(module)
                except Exception as e:
                    skipped.append(f"{module} (erro: {str(e)})")
            
            return {
                "success": True,
                "imported": imported,
                "skipped": skipped
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class ModuleSelectView(discord.ui.View):
    def __init__(self, action: str):
        super().__init__(timeout=180)
        self.action = action
        self.selected_modules = []
        
        # Select de módulos
        options = [
            discord.SelectOption(label="🎫 Tickets", value="tickets", description="Sistema de tickets"),
            discord.SelectOption(label="👋 Boas-vindas", value="welcome", description="Mensagens de boas-vindas"),
            discord.SelectOption(label="💰 Economia", value="economy", description="Sistema de economia"),
            discord.SelectOption(label="🛡️ Moderação", value="moderation", description="Comandos de moderação"),
            discord.SelectOption(label="📋 Logs", value="logs", description="Sistema de logs"),
            discord.SelectOption(label="🎭 Autorole", value="autorole", description="Reaction roles"),
            discord.SelectOption(label="🖌️ Embeds", value="embeds", description="Estilo de embeds"),
            discord.SelectOption(label="🧪 Emojis", value="emojis", description="Emojis customizados"),
            discord.SelectOption(label="🎨 Tema", value="theme", description="Tema visual"),
        ]
        
        self.module_select = discord.ui.Select(
            placeholder="Selecione os módulos...",
            options=options,
            min_values=1,
            max_values=len(options)
        )
        self.module_select.callback = self._select_callback
        self.add_item(self.module_select)
    
    async def _select_callback(self, interaction: discord.Interaction):
        self.selected_modules = self.module_select.values
        await interaction.response.defer()

class ImportExportCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, import_export_system: ImportExportSystem):
        self.bot = bot
        self.import_export_system = import_export_system
    
    @app_commands.command(name="exportar", description="Exporta configurações para compartilhar")
    @app_commands.checks.has_permissions(administrator=True)
    async def export_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📤 Exportar Configurações",
            description=(
                "Exporte suas configurações para compartilhar com outros servidores!\n\n"
                "**Como funciona:**\n"
                "1. Selecione os módulos que deseja exportar\n"
                "2. Escolha se deseja incluir dados sensíveis\n"
                "3. Receba o arquivo de exportação\n"
                "4. Compartilhe com outros servidores\n\n"
                "⚠️ **Dados sensíveis** incluem: IDs de canais, contadores, registros específicos"
            ),
            color=0x5865F2
        )
        
        view = ExportOptionsView(self.import_export_system, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="importar", description="Importa configurações de outro servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def import_command(self, interaction: discord.Interaction, arquivo: discord.Attachment):
        # Verificar se é um JSON
        if not arquivo.filename.endswith('.json'):
            await interaction.response.send_message(
                "❌ O arquivo deve ser um JSON (.json)",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Baixar arquivo
        import_path = self.import_export_system.export_dir / f"temp_{arquivo.filename}"
        await arquivo.save(import_path)
        
        # Criar view para selecionar módulos
        embed = discord.Embed(
            title="📥 Importar Configurações",
            description=(
                f"**Arquivo:** `{arquivo.filename}`\n\n"
                "Selecione quais módulos deseja importar:\n\n"
                "**Opções:**\n"
                "• **Mesclar:** Mantém configs existentes e adiciona as novas\n"
                "• **Substituir:** Remove tudo e usa apenas o que está no arquivo"
            ),
            color=0x5865F2
        )
        
        view = ImportOptionsView(self.import_export_system, interaction.guild.id, str(import_path))
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class ExportOptionsView(discord.ui.View):
    def __init__(self, import_export_system: ImportExportSystem, guild_id: int):
        super().__init__(timeout=180)
        self.import_export_system = import_export_system
        self.guild_id = guild_id
        self.selected_modules = None
        self.include_sensitive = False
    
    @discord.ui.button(label="Selecionar Módulos", style=discord.ButtonStyle.primary, emoji="📦", row=0)
    async def select_modules(self, interaction: discord.Interaction, button: discord.ui.Button):
        module_view = ModuleSelectView("export")
        
        await interaction.response.send_message(
            "Selecione os módulos para exportar:",
            view=module_view,
            ephemeral=True
        )
        
        await module_view.wait()
        self.selected_modules = module_view.selected_modules
        
        if self.selected_modules:
            await interaction.edit_original_response(
                content=f"✅ Selecionados: {', '.join(self.selected_modules)}"
            )
    
    @discord.ui.button(label="Incluir Dados Sensíveis", style=discord.ButtonStyle.secondary, emoji="🔓", row=0)
    async def toggle_sensitive(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.include_sensitive = not self.include_sensitive
        
        button.emoji = "🔓" if self.include_sensitive else "🔒"
        button.label = "Incluir Dados Sensíveis" if self.include_sensitive else "Ocultar Dados Sensíveis"
        button.style = discord.ButtonStyle.danger if self.include_sensitive else discord.ButtonStyle.secondary
        
        await interaction.response.edit_message(view=self)
    
    @discord.ui.button(label="Exportar Agora", style=discord.ButtonStyle.success, emoji="📤", row=1)
    async def export_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        export_path = self.import_export_system.export_config(
            self.guild_id,
            modules=self.selected_modules,
            include_sensitive=self.include_sensitive
        )
        
        file = discord.File(export_path, filename=Path(export_path).name)
        
        modules_exported = self.selected_modules if self.selected_modules else ["todos os módulos"]
        
        embed = discord.Embed(
            title="✅ Exportação Concluída!",
            description=(
                f"**Módulos exportados:** {', '.join(modules_exported)}\n"
                f"**Dados sensíveis:** {'Incluídos' if self.include_sensitive else 'Removidos'}\n\n"
                "Use `/importar` em outro servidor para aplicar estas configurações!"
            ),
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.set_footer(text="💡 Compartilhe este arquivo com segurança")
        
        await interaction.followup.send(embed=embed, file=file, ephemeral=True)

class ImportOptionsView(discord.ui.View):
    def __init__(self, import_export_system: ImportExportSystem, guild_id: int, import_path: str):
        super().__init__(timeout=180)
        self.import_export_system = import_export_system
        self.guild_id = guild_id
        self.import_path = import_path
        self.selected_modules = None
        self.merge_mode = True
    
    @discord.ui.button(label="Selecionar Módulos", style=discord.ButtonStyle.primary, emoji="📦", row=0)
    async def select_modules(self, interaction: discord.Interaction, button: discord.ui.Button):
        module_view = ModuleSelectView("import")
        
        await interaction.response.send_message(
            "Selecione os módulos para importar:",
            view=module_view,
            ephemeral=True
        )
        
        await module_view.wait()
        self.selected_modules = module_view.selected_modules
        
        if self.selected_modules:
            await interaction.edit_original_response(
                content=f"✅ Selecionados: {', '.join(self.selected_modules)}"
            )
    
    @discord.ui.button(label="Modo: Mesclar", style=discord.ButtonStyle.secondary, emoji="🔀", row=0)
    async def toggle_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.merge_mode = not self.merge_mode
        
        button.label = "Modo: Mesclar" if self.merge_mode else "Modo: Substituir"
        button.emoji = "🔀" if self.merge_mode else "🔄"
        button.style = discord.ButtonStyle.secondary if self.merge_mode else discord.ButtonStyle.danger
        
        await interaction.response.edit_message(view=self)
    
    @discord.ui.button(label="Importar Agora", style=discord.ButtonStyle.success, emoji="📥", row=1)
    async def import_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        result = self.import_export_system.import_config(
            self.guild_id,
            self.import_path,
            modules=self.selected_modules,
            merge=self.merge_mode
        )
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Importação Concluída!",
                description=(
                    f"**Modo:** {'Mesclar' if self.merge_mode else 'Substituir'}\n\n"
                    f"**Importados:** {', '.join(result['imported']) if result['imported'] else 'Nenhum'}\n"
                    f"**Ignorados:** {', '.join(result['skipped']) if result['skipped'] else 'Nenhum'}"
                ),
                color=0x00FF00
            )
        else:
            embed = discord.Embed(
                title="❌ Erro na Importação",
                description=f"**Erro:** {result.get('error', 'Desconhecido')}",
                color=0xFF0000
            )
        
        # Limpar arquivo temporário
        try:
            Path(self.import_path).unlink()
        except:
            pass
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot, config_manager):
    """Configura o sistema de importação/exportação."""
    import_export_system = ImportExportSystem(config_manager)
    await bot.add_cog(ImportExportCommands(bot, import_export_system))
    return import_export_system
