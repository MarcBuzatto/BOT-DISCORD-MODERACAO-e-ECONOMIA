"""
Sistema Anti-Raid
Desenvolvido por: MARKIZIN
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict

class AntiRaidSystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.join_tracker = defaultdict(list)  # {guild_id: [(user_id, timestamp), ...]}
    
    def get_config(self, guild_id: int) -> dict:
        """Retorna configurações anti-raid do servidor."""
        return self.config_manager.get_guild_config(guild_id, "antiraid")
    
    def update_config(self, guild_id: int, config: dict):
        """Atualiza configurações anti-raid."""
        self.config_manager.update_guild_config(guild_id, "antiraid", config)
    
    def track_join(self, guild_id: int, user_id: int) -> dict:
        """
        Rastreia entrada de usuário e detecta possível raid.
        Retorna dict com: is_raid (bool), join_rate (int), action (str)
        """
        config = self.get_config(guild_id)
        
        if not config.get("enabled", False):
            return {"is_raid": False, "join_rate": 0, "action": None}
        
        now = datetime.now()
        threshold_seconds = config.get("threshold_seconds", 10)
        max_joins = config.get("max_joins", 5)
        
        # Limpar entradas antigas
        cutoff = now - timedelta(seconds=threshold_seconds)
        self.join_tracker[guild_id] = [
            (uid, ts) for uid, ts in self.join_tracker[guild_id]
            if ts > cutoff
        ]
        
        # Adicionar nova entrada
        self.join_tracker[guild_id].append((user_id, now))
        
        # Verificar se excedeu limite
        join_rate = len(self.join_tracker[guild_id])
        is_raid = join_rate >= max_joins
        
        return {
            "is_raid": is_raid,
            "join_rate": join_rate,
            "action": config.get("action", "alert") if is_raid else None,
            "threshold": max_joins,
            "window": threshold_seconds
        }
    
    def clear_join_tracker(self, guild_id: int):
        """Limpa o rastreamento de entradas."""
        self.join_tracker[guild_id] = []

class AntiRaidPanel(discord.ui.View):
    def __init__(self, guild: discord.Guild, antiraid_system: AntiRaidSystem):
        super().__init__(timeout=180)
        self.guild = guild
        self.antiraid_system = antiraid_system
    
    @discord.ui.button(label="Manual", style=discord.ButtonStyle.primary, emoji="📖", row=0)
    async def manual_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📖 Manual: Sistema Anti-Raid",
            description="Proteção automática contra raids de bots e trolls",
            color=0x5865F2
        )
        
        embed.add_field(
            name="🎯 O que é um Raid?",
            value=(
                "Raid é quando múltiplos usuários/bots entram no servidor rapidamente "
                "com intenções maliciosas (spam, trollagem, etc)."
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Como Configurar",
            value=(
                "1. **Ative** o sistema com o botão Toggle\n"
                "2. **Configure** o limite de entradas (ex: 5 pessoas)\n"
                "3. **Defina** o tempo de janela (ex: 10 segundos)\n"
                "4. **Escolha** a ação automática:\n"
                "   • **Alerta**: Apenas notifica moderadores\n"
                "   • **Verificação**: Adiciona cargo de verificação\n"
                "   • **Kick**: Expulsa novos membros automaticamente\n"
                "   • **Ban**: Bane novos membros automaticamente"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔔 Canal de Alertas",
            value="Configure um canal para receber notificações quando raids forem detectadas.",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Atenção",
            value=(
                "• Use **Kick/Ban** com cautela - pode afetar usuários legítimos\n"
                "• Recomendado: Comece com **Alerta** e ajuste conforme necessário\n"
                "• Cargo de verificação: Membros novos ficam restritos até verificação manual"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Teste as configurações em horários de baixo movimento")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Toggle", style=discord.ButtonStyle.success, emoji="🔄", row=0)
    async def toggle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.antiraid_system.get_config(self.guild.id)
        config["enabled"] = not config.get("enabled", False)
        self.antiraid_system.update_config(self.guild.id, config)
        
        status = "✅ Ativado" if config["enabled"] else "❌ Desativado"
        
        embed = discord.Embed(
            title=f"Sistema Anti-Raid {status}",
            description=f"O sistema está agora **{'ativado' if config['enabled'] else 'desativado'}**.",
            color=0x00FF00 if config["enabled"] else 0xFF0000
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Limites", style=discord.ButtonStyle.secondary, emoji="⚙️", row=0)
    async def limits_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LimitsModal(self.antiraid_system, self.guild.id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Ação", style=discord.ButtonStyle.secondary, emoji="⚡", row=0)
    async def action_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ActionSelectView(self.antiraid_system, self.guild.id)
        
        embed = discord.Embed(
            title="⚡ Escolher Ação Automática",
            description="Selecione o que fazer quando um raid for detectado:",
            color=0x5865F2
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Canal de Alertas", style=discord.ButtonStyle.secondary, emoji="🔔", row=1)
    async def alert_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View(timeout=180)
        
        select = discord.ui.ChannelSelect(
            placeholder="Selecione o canal de alertas...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )
        
        async def select_callback(interaction: discord.Interaction):
            channel = select.values[0]
            config = self.antiraid_system.get_config(self.guild.id)
            config["alert_channel_id"] = channel.id
            self.antiraid_system.update_config(self.guild.id, config)
            
            embed = discord.Embed(
                title="✅ Canal de Alertas Configurado",
                description=f"Alertas de raid serão enviados para {channel.mention}",
                color=0x00FF00
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        select.callback = select_callback
        view.add_item(select)
        
        await interaction.response.send_message("Selecione o canal:", view=view, ephemeral=True)
    
    @discord.ui.button(label="Status", style=discord.ButtonStyle.primary, emoji="ℹ️", row=1)
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.antiraid_system.get_config(self.guild.id)
        
        embed = discord.Embed(
            title="📊 Status do Anti-Raid",
            color=0x00FF00 if config.get("enabled") else 0xFF0000
        )
        
        embed.add_field(
            name="Status",
            value="✅ Ativado" if config.get("enabled") else "❌ Desativado",
            inline=True
        )
        
        embed.add_field(
            name="Limites",
            value=f"{config.get('max_joins', 5)} entradas em {config.get('threshold_seconds', 10)}s",
            inline=True
        )
        
        actions = {
            "alert": "🔔 Apenas Alertar",
            "verification": "✋ Verificação",
            "kick": "👢 Kick Automático",
            "ban": "🔨 Ban Automático"
        }
        
        embed.add_field(
            name="Ação",
            value=actions.get(config.get("action", "alert"), "Não configurado"),
            inline=True
        )
        
        alert_channel = self.guild.get_channel(config.get("alert_channel_id"))
        embed.add_field(
            name="Canal de Alertas",
            value=alert_channel.mention if alert_channel else "Não configurado",
            inline=False
        )
        
        if config.get("action") == "verification":
            verification_role = self.guild.get_role(config.get("verification_role_id"))
            embed.add_field(
                name="Cargo de Verificação",
                value=verification_role.mention if verification_role else "Não configurado",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Limpar Rastreamento", style=discord.ButtonStyle.danger, emoji="🧹", row=1)
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.antiraid_system.clear_join_tracker(self.guild.id)
        
        embed = discord.Embed(
            title="✅ Rastreamento Limpo",
            description="O histórico de entradas foi resetado.",
            color=0x00FF00
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Voltar", style=discord.ButtonStyle.secondary, emoji="◀️", row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.secondary, emoji="✖️", row=2)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

class LimitsModal(discord.ui.Modal, title="⚙️ Configurar Limites"):
    def __init__(self, antiraid_system: AntiRaidSystem, guild_id: int):
        super().__init__()
        self.antiraid_system = antiraid_system
        self.guild_id = guild_id
        
        config = antiraid_system.get_config(guild_id)
        
        self.max_joins = discord.ui.TextInput(
            label="Máximo de Entradas",
            placeholder="Ex: 5",
            default=str(config.get("max_joins", 5)),
            min_length=1,
            max_length=3
        )
        self.add_item(self.max_joins)
        
        self.threshold_seconds = discord.ui.TextInput(
            label="Janela de Tempo (segundos)",
            placeholder="Ex: 10",
            default=str(config.get("threshold_seconds", 10)),
            min_length=1,
            max_length=3
        )
        self.add_item(self.threshold_seconds)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_joins = int(self.max_joins.value)
            threshold_seconds = int(self.threshold_seconds.value)
            
            if max_joins < 1 or threshold_seconds < 1:
                raise ValueError("Valores devem ser maiores que 0")
            
            config = self.antiraid_system.get_config(self.guild_id)
            config["max_joins"] = max_joins
            config["threshold_seconds"] = threshold_seconds
            self.antiraid_system.update_config(self.guild_id, config)
            
            embed = discord.Embed(
                title="✅ Limites Configurados",
                description=f"Detecção de raid: **{max_joins}** entradas em **{threshold_seconds}** segundos",
                color=0x00FF00
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message(
                "❌ Valores inválidos! Use apenas números inteiros positivos.",
                ephemeral=True
            )

class ActionSelectView(discord.ui.View):
    def __init__(self, antiraid_system: AntiRaidSystem, guild_id: int):
        super().__init__(timeout=180)
        self.antiraid_system = antiraid_system
        self.guild_id = guild_id
        
        options = [
            discord.SelectOption(
                label="Apenas Alertar",
                value="alert",
                description="Notifica moderadores mas não toma ação",
                emoji="🔔"
            ),
            discord.SelectOption(
                label="Modo Verificação",
                value="verification",
                description="Adiciona cargo de verificação aos novos membros",
                emoji="✋"
            ),
            discord.SelectOption(
                label="Kick Automático",
                value="kick",
                description="Expulsa novos membros automaticamente",
                emoji="👢"
            ),
            discord.SelectOption(
                label="Ban Automático",
                value="ban",
                description="Bane novos membros automaticamente",
                emoji="🔨"
            )
        ]
        
        self.action_select = discord.ui.Select(
            placeholder="Selecione a ação...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.action_select.callback = self._select_callback
        self.add_item(self.action_select)
    
    async def _select_callback(self, interaction: discord.Interaction):
        action = self.action_select.values[0]
        
        config = self.antiraid_system.get_config(self.guild_id)
        config["action"] = action
        self.antiraid_system.update_config(self.guild_id, config)
        
        action_names = {
            "alert": "🔔 Apenas Alertar",
            "verification": "✋ Modo Verificação",
            "kick": "👢 Kick Automático",
            "ban": "🔨 Ban Automático"
        }
        
        embed = discord.Embed(
            title="✅ Ação Configurada",
            description=f"Ação selecionada: **{action_names[action]}**",
            color=0x00FF00
        )
        
        if action == "verification":
            embed.add_field(
                name="⚠️ Próximo Passo",
                value="Configure um cargo de verificação com `/antiraid`",
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=None)

class AntiRaidCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, antiraid_system: AntiRaidSystem):
        self.bot = bot
        self.antiraid_system = antiraid_system
    
    @app_commands.command(name="antiraid", description="Gerencia sistema anti-raid")
    @app_commands.checks.has_permissions(administrator=True)
    async def antiraid_command(self, interaction: discord.Interaction):
        config = self.antiraid_system.get_config(interaction.guild.id)
        
        embed = discord.Embed(
            title="🛡️ Sistema Anti-Raid",
            description="Proteção automática contra raids de bots e trolls",
            color=0x5865F2
        )
        
        status = "✅ Ativado" if config.get("enabled") else "❌ Desativado"
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(
            name="Limites",
            value=f"{config.get('max_joins', 5)} entradas / {config.get('threshold_seconds', 10)}s",
            inline=True
        )
        
        actions = {
            "alert": "🔔 Alertar",
            "verification": "✋ Verificação",
            "kick": "👢 Kick",
            "ban": "🔨 Ban"
        }
        embed.add_field(
            name="Ação",
            value=actions.get(config.get("action", "alert")),
            inline=True
        )
        
        embed.set_footer(text="💡 Use os botões abaixo para configurar")
        
        view = AntiRaidPanel(interaction.guild, self.antiraid_system)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Detecta e responde a possíveis raids."""
        result = self.antiraid_system.track_join(member.guild.id, member.id)
        
        if not result["is_raid"]:
            return
        
        config = self.antiraid_system.get_config(member.guild.id)
        action = config.get("action", "alert")
        
        # Enviar alerta
        alert_channel_id = config.get("alert_channel_id")
        if alert_channel_id:
            channel = member.guild.get_channel(alert_channel_id)
            if channel:
                embed = discord.Embed(
                    title="🚨 RAID DETECTADA!",
                    description=f"**{result['join_rate']}** usuários entraram em **{result['window']}** segundos (limite: {result['threshold']})",
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="Último Membro",
                    value=f"{member.mention} ({member.id})",
                    inline=False
                )
                
                embed.add_field(
                    name="Ação Tomada",
                    value={
                        "alert": "🔔 Alerta enviado",
                        "verification": "✋ Cargo de verificação aplicado",
                        "kick": "👢 Membros expulsos",
                        "ban": "🔨 Membros banidos"
                    }.get(action, "Nenhuma"),
                    inline=False
                )
                
                try:
                    await channel.send(embed=embed)
                except:
                    pass
        
        # Executar ação
        try:
            if action == "verification":
                verification_role_id = config.get("verification_role_id")
                if verification_role_id:
                    role = member.guild.get_role(verification_role_id)
                    if role:
                        await member.add_roles(role, reason="Anti-Raid: Verificação necessária")
            
            elif action == "kick":
                await member.kick(reason="Anti-Raid: Entrada suspeita detectada")
            
            elif action == "ban":
                await member.ban(reason="Anti-Raid: Entrada suspeita detectada", delete_message_days=0)
        
        except discord.Forbidden:
            pass  # Bot não tem permissões
        except Exception as e:
            print(f"Erro ao executar ação anti-raid: {e}")

async def setup(bot: commands.Bot, config_manager):
    """Configura o sistema anti-raid."""
    antiraid_system = AntiRaidSystem(config_manager)
    await bot.add_cog(AntiRaidCommands(bot, antiraid_system))
    return antiraid_system
