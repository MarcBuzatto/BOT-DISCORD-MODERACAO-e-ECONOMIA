"""\nPainel de Formatação Global de Embeds\nDesenvolvido por: MARKIZIN\n"""
import discord
from discord.ui import Button
from .panel_system import BasePanel, ImageURLModal, EditTextModal, ColorPickerModal
from typing import Any, Dict

class EmbedsPanel(BasePanel):
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, "embed_style")
        self._build_buttons()

    def _build_buttons(self):
        # Row 0: Personalização visual
        self.add_item(ManualEmbedsButton(self))
        self.add_item(EditFooterButton(self))
        self.add_item(EditColorButton(self))
        
        # Row 1: Elementos visuais
        self.add_item(EditThumbnailButton(self))
        self.add_item(EditAuthorButton(self))
        self.add_item(ToggleTimestampButton(self))
        
        # Row 2: Navegação e controles
        self.add_item(BackEmbedsButton(self))
        self.add_item(CloseEmbedsButton(self))
        self.add_item(DeleteEmbedsButton(self))

    def create_embed(self) -> discord.Embed:
        cfg = self.get_config()
        embed = discord.Embed(
            title="🖌️ Painel de Estilo Global de Embeds",
            description=(
                "**Como funciona:** Personalize o visual de todos os embeds do bot.\n\n"
                "**Configurações Atuais:**\n"
                f"🎨 Cor padrão: `{hex(cfg.get('default_color', 0x5865F2))}`\n"
                f"🦶 Footer: `{cfg.get('footer_text') or 'Nenhum'}`\n"
                f"⏱️ Timestamp: {'✅' if cfg.get('use_timestamp') else '❌'}\n"
                f"🖼️ Thumbnail: {'✅' if cfg.get('thumbnail_url') else '❌'}\n"
                f"👤 Author: {'✅' if cfg.get('author_name') else '❌'}"
            ),
            color=cfg.get('default_color', 0x5865F2)
        )
        if cfg.get('thumbnail_url'):
            embed.set_thumbnail(url=cfg['thumbnail_url'])
        if cfg.get('author_name'):
            author_icon = cfg.get('author_icon')
            if author_icon:
                embed.set_author(name=cfg['author_name'], icon_url=author_icon)
            else:
                embed.set_author(name=cfg['author_name'])
        embed.set_footer(text=cfg.get('footer_text') or 'Sem footer configurado')
        embed = self.config_manager.apply_style(self.guild_id, embed)
        return embed

class EditFooterButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Footer", style=discord.ButtonStyle.secondary, emoji="🦶", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        fields = {
            'footer_text': {
                'label': 'Texto do Footer',
                'placeholder': 'Ex: Meu Bot Premium',
                'default': self.panel.get_config().get('footer_text') or '',
                'required': True,
                'max_length': 128
            },
            'footer_icon': {
                'label': 'URL do Ícone (opcional)',
                'placeholder': 'https://...png',
                'default': self.panel.get_config().get('footer_icon') or '',
                'required': False,
                'max_length': 256
            }
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config({
                'footer_text': data['footer_text'] or None,
                'footer_icon': data['footer_icon'] or None
            })
            await self.panel.send_success(inter, 'Footer atualizado.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Editar Footer', fields, _submit))

class EditColorButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Cor", style=discord.ButtonStyle.secondary, emoji="🎨", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        async def _submit(inter: discord.Interaction, color_value: int):
            self.panel.update_config({'default_color': color_value})
            await self.panel.send_success(inter, 'Cor padrão atualizada.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(ColorPickerModal(_submit))

class EditThumbnailButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Thumbnail", style=discord.ButtonStyle.secondary, emoji="🖼️", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        async def _submit(inter: discord.Interaction, url: str, field_type: str):
            self.panel.update_config({'thumbnail_url': url})
            await self.panel.send_success(inter, 'Thumbnail global definida.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(ImageURLModal(_submit, field_type='thumbnail'))

class EditAuthorButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Author", style=discord.ButtonStyle.secondary, emoji="👤", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        fields = {
            'author_name': {
                'label': 'Nome do Author',
                'placeholder': 'Ex: Sistema Global',
                'default': self.panel.get_config().get('author_name') or '',
                'required': False,
                'max_length': 64
            },
            'author_icon': {
                'label': 'URL do Ícone',
                'placeholder': 'https://...png',
                'default': self.panel.get_config().get('author_icon') or '',
                'required': False,
                'max_length': 256
            }
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config({
                'author_name': data['author_name'] or None,
                'author_icon': data['author_icon'] or None
            })
            await self.panel.send_success(inter, 'Autor global atualizado.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Editar Author Global', fields, _submit))

class ToggleTimestampButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Timestamp", style=discord.ButtonStyle.secondary, emoji="⏱️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('use_timestamp', True)
        self.panel.update_config({'use_timestamp': new_state})
        await self.panel.send_success(interaction, f"Timestamp automático {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)

class CloseEmbedsButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Fechar", style=discord.ButtonStyle.secondary, emoji="❌", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        embed = discord.Embed(description="✅ Painel de estilo fechado.", color=0x00FF00)
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()

class DeleteEmbedsButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Apagar", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Painel apagado com sucesso!", ephemeral=True)
        await interaction.message.delete()
        self.panel.stop()

class BackEmbedsButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Voltar", style=discord.ButtonStyle.primary, emoji="🔙", row=2)
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

class ManualEmbedsButton(Button):
    def __init__(self, panel: EmbedsPanel):
        super().__init__(label="Manual", style=discord.ButtonStyle.success, emoji="📖", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Manual de Estilo Global de Embeds",
            description=(
                "**Guia para personalizar visual de todos os embeds do bot.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x3498DB,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="🦶 Footer Personalizado",
            value=(
                "Define o texto que aparece no rodapé de todos os embeds.\n\n"
                "**Exemplos:**\n"
                "• `🎉 Servidor {guild}`\n"
                "• `🛡️ Desenvolvido por [Seu Nome]`\n"
                "• `👍 Obrigado por usar nosso bot!`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎨 Cor Padrão",
            value=(
                "Escolha a cor principal dos embeds.\n\n"
                "**Formatos aceitos:**\n"
                "• Hexadecimal: `#FF0000` (vermelho)\n"
                "• Decimal: `16711680` (vermelho)\n\n"
                "**Cores sugeridas:**\n"
                "🔵 Azul: `#3498DB` | 🟢 Verde: `#2ECC71`\n"
                "🔴 Vermelho: `#E74C3C` | 🟡 Amarelo: `#F1C40F`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🖼️ Thumbnail Global",
            value=(
                "Imagem pequena que aparece no canto superior direito.\n\n"
                "**Uso recomendado:**\n"
                "• Logo do servidor\n"
                "• Ícone do bot\n"
                "• Mascote da comunidade\n\n"
                "⚠️ Insira URL válida (https://...)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👤 Author Customizado",
            value=(
                "Nome e ícone que aparecem no topo do embed.\n\n"
                "**Ideal para:**\n"
                "• Nome do servidor\n"
                "• Título da equipe\n"
                "• Branding personalizado"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Timestamp Automático",
            value=(
                "Ativa data/hora automática no rodapé dos embeds.\n\n"
                "✅ **Ativado**: Mostra quando a mensagem foi enviada\n"
                "❌ **Desativado**: Sem timestamp"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Dica: Essas configurações afetam TODOS os embeds do bot!")
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)
