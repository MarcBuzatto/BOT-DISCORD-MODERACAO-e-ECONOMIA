"""
Sistema de Temas Predefinidos
Desenvolvido por: MARKIZIN
"""
import discord
from discord import app_commands
from discord.ext import commands

# Temas predefinidos com cores e estilos
THEMES = {
    "dark": {
        "name": "🌙 Dark",
        "description": "Tema escuro elegante e profissional",
        "colors": {
            "primary": 0x2C2F33,      # Cinza escuro
            "success": 0x43B581,      # Verde Discord
            "error": 0xF04747,        # Vermelho
            "warning": 0xFAA61A,      # Laranja
            "info": 0x7289DA,         # Azul Discord
            "embed": 0x2C2F33,        # Cor padrão embeds
            "daily": 0x43B581,        # Verde para daily
            "balance": 0x7289DA       # Azul para saldo
        },
        "style": "clean"
    },
    "light": {
        "name": "☀️ Light",
        "description": "Tema claro e vibrante",
        "colors": {
            "primary": 0xFFFFFF,      # Branco
            "success": 0x77B255,      # Verde claro
            "error": 0xDD2E44,        # Vermelho claro
            "warning": 0xFFCC4D,      # Amarelo
            "info": 0x55ACEE,         # Azul claro
            "embed": 0x99AAB5,        # Cinza claro
            "daily": 0x77B255,        # Verde claro
            "balance": 0x55ACEE       # Azul claro
        },
        "style": "friendly"
    },
    "neon": {
        "name": "⚡ Neon",
        "description": "Tema neon vibrante e energético",
        "colors": {
            "primary": 0xFF00FF,      # Magenta neon
            "success": 0x00FF00,      # Verde neon
            "error": 0xFF0000,        # Vermelho neon
            "warning": 0xFFFF00,      # Amarelo neon
            "info": 0x00FFFF,         # Ciano neon
            "embed": 0xFF1493,        # Pink neon
            "daily": 0x00FF00,        # Verde neon
            "balance": 0x00FFFF       # Ciano neon
        },
        "style": "vibrant"
    },
    "professional": {
        "name": "💼 Professional",
        "description": "Tema corporativo e sério",
        "colors": {
            "primary": 0x34495E,      # Azul corporativo
            "success": 0x27AE60,      # Verde profissional
            "error": 0xC0392B,        # Vermelho sério
            "warning": 0xE67E22,      # Laranja corporativo
            "info": 0x2980B9,         # Azul informativo
            "embed": 0x34495E,        # Azul corporativo
            "daily": 0x27AE60,        # Verde profissional
            "balance": 0x2980B9       # Azul informativo
        },
        "style": "formal"
    },
    "minimal": {
        "name": "✨ Minimal",
        "description": "Tema minimalista e limpo",
        "colors": {
            "primary": 0x95A5A6,      # Cinza neutro
            "success": 0x2ECC71,      # Verde suave
            "error": 0xE74C3C,        # Vermelho suave
            "warning": 0xF39C12,      # Amarelo suave
            "info": 0x3498DB,         # Azul suave
            "embed": 0xECF0F1,        # Cinza muito claro
            "daily": 0x2ECC71,        # Verde suave
            "balance": 0x3498DB       # Azul suave
        },
        "style": "simple"
    }
}

class ThemeSystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def get_theme(self, theme_name: str) -> dict:
        """Retorna as configurações de um tema."""
        return THEMES.get(theme_name.lower())
    
    def list_themes(self) -> list:
        """Lista todos os temas disponíveis."""
        return [
            {
                "id": theme_id,
                "name": theme["name"],
                "description": theme["description"]
            }
            for theme_id, theme in THEMES.items()
        ]
    
    def apply_theme(self, guild_id: int, theme_name: str) -> bool:
        """Aplica um tema a todas as configurações do servidor."""
        theme = self.get_theme(theme_name)
        if not theme:
            return False
        
        try:
            colors = theme["colors"]
            
            # Aplicar cores ao módulo de boas-vindas
            welcome_config = self.config_manager.get_guild_config(guild_id, "welcome")
            welcome_config["cor_embed"] = colors["embed"]
            self.config_manager.update_guild_config(guild_id, "welcome", welcome_config)
            
            # Aplicar cores ao módulo de economia
            economy_config = self.config_manager.get_guild_config(guild_id, "economy")
            economy_config["cor_saldo"] = colors["balance"]
            economy_config["cor_daily"] = colors["daily"]
            self.config_manager.update_guild_config(guild_id, "economy", economy_config)
            
            # Aplicar cores ao módulo de moderação
            moderation_config = self.config_manager.get_guild_config(guild_id, "moderation")
            moderation_config["cor_ban"] = colors["error"]
            moderation_config["cor_kick"] = colors["warning"]
            moderation_config["cor_mute"] = colors["info"]
            moderation_config["cor_warn"] = colors["warning"]
            self.config_manager.update_guild_config(guild_id, "moderation", moderation_config)
            
            # Aplicar cor ao módulo de embeds
            embeds_config = self.config_manager.get_guild_config(guild_id, "embeds")
            embeds_config["color"] = colors["embed"]
            self.config_manager.update_guild_config(guild_id, "embeds", embeds_config)
            
            # Salvar tema atual
            theme_config = {
                "current_theme": theme_name.lower(),
                "applied_at": discord.utils.utcnow().isoformat()
            }
            self.config_manager.update_guild_config(guild_id, "theme", theme_config)
            
            return True
        except Exception as e:
            print(f"Erro ao aplicar tema: {e}")
            return False
    
    def get_current_theme(self, guild_id: int) -> str:
        """Retorna o tema atual do servidor."""
        try:
            theme_config = self.config_manager.get_guild_config(guild_id, "theme")
            return theme_config.get("current_theme", "dark")
        except:
            return "dark"

class ThemeSelect(discord.ui.Select):
    def __init__(self, theme_system, guild_id):
        self.theme_system = theme_system
        self.guild_id = guild_id
        
        options = []
        for theme_id, theme in THEMES.items():
            options.append(
                discord.SelectOption(
                    label=theme["name"],
                    description=theme["description"],
                    value=theme_id,
                    emoji=theme["name"].split()[0]  # Pega o emoji do nome
                )
            )
        
        super().__init__(
            placeholder="Selecione um tema...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        theme_id = self.values[0]
        theme = THEMES[theme_id]
        
        success = self.theme_system.apply_theme(self.guild_id, theme_id)
        
        if success:
            embed = discord.Embed(
                title=f"{theme['name']} Aplicado!",
                description=(
                    f"**Tema:** {theme['description']}\n\n"
                    "**Módulos atualizados:**\n"
                    "👋 Boas-vindas\n"
                    "💰 Economia\n"
                    "🛡️ Moderação\n"
                    "🖌️ Embeds\n\n"
                    "As cores foram aplicadas automaticamente em todos os módulos!"
                ),
                color=theme["colors"]["primary"],
                timestamp=discord.utils.utcnow()
            )
            
            # Mostrar paleta de cores
            color_preview = ""
            for color_name, color_value in theme["colors"].items():
                color_preview += f"**{color_name.title()}:** `#{color_value:06X}`\n"
            
            embed.add_field(
                name="🎨 Paleta de Cores",
                value=color_preview,
                inline=False
            )
            
            embed.set_footer(text="💡 Use /tema novamente para trocar de tema")
        else:
            embed = discord.Embed(
                title="❌ Erro ao Aplicar Tema",
                description="Não foi possível aplicar o tema selecionado.",
                color=0xFF0000
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class ThemeView(discord.ui.View):
    def __init__(self, theme_system, guild_id):
        super().__init__(timeout=180)
        # Guardar referências diretas para evitar depender da ordem em self.children
        self.theme_system = theme_system
        self.guild_id = guild_id
        self.select = ThemeSelect(theme_system, guild_id)
        self.add_item(self.select)
    
    @discord.ui.button(label="Tema Atual", style=discord.ButtonStyle.secondary, emoji="ℹ️")
    async def current_theme_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Usar atributos armazenados em vez de acessar children[0]
        theme_system = self.theme_system
        guild_id = self.guild_id
        
        current = theme_system.get_current_theme(guild_id)
        theme = THEMES.get(current, THEMES["dark"])
        
        embed = discord.Embed(
            title=f"Tema Atual: {theme['name']}",
            description=theme['description'],
            color=theme["colors"]["primary"]
        )
        
        # Mostrar cores atuais
        color_preview = ""
        for color_name, color_value in theme["colors"].items():
            color_preview += f"**{color_name.title()}:** `#{color_value:06X}`\n"
        
        embed.add_field(
            name="🎨 Cores Aplicadas",
            value=color_preview,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ThemeCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, theme_system: ThemeSystem):
        self.bot = bot
        self.theme_system = theme_system
    
    @app_commands.command(name="tema", description="Gerencia temas visuais do bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def theme_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎨 Sistema de Temas",
            description=(
                "Escolha um tema para aplicar automaticamente em todo o bot!\n\n"
                "**Temas disponíveis:**\n"
            ),
            color=0x5865F2
        )
        
        for theme_id, theme in THEMES.items():
            embed.add_field(
                name=theme["name"],
                value=theme["description"],
                inline=True
            )
        
        current = self.theme_system.get_current_theme(interaction.guild.id)
        current_theme = THEMES.get(current, THEMES["dark"])
        
        embed.set_footer(text=f"Tema atual: {current_theme['name']}")
        
        view = ThemeView(self.theme_system, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot, config_manager):
    """Configura o sistema de temas."""
    theme_system = ThemeSystem(config_manager)
    await bot.add_cog(ThemeCommands(bot, theme_system))
    return theme_system
