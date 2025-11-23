"""
Painéis de Configuração - Boas-vindas
Desenvolvido por: MARKIZIN
"""

import discord
from discord.ui import Button
from .panel_system import BasePanel, EditTextModal, ColorPickerModal, ImageURLModal, ChannelSelect, RoleSelect
from typing import Dict, Any


class WelcomePanel(BasePanel):
    """Painel de configuração de boas-vindas."""
    
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, "welcome")
        self._build_buttons()
    
    def _build_buttons(self):
        """Constrói os botões do painel."""
        # Row 0: Ações principais
        self.add_item(ManualWelcomeButton(self))
        self.add_item(ToggleButton(self))
        self.add_item(PreviewButton(self))
        self.add_item(TestButton(self))
        
        # Row 1: Personalização visual
        self.add_item(EditTextsButton(self))
        self.add_item(EditColorButton(self))
        self.add_item(SetImageButton(self))
        self.add_item(SetThumbnailButton(self))
        
        # Row 2: Configurações estruturais
        self.add_item(SetChannelButton(self))
        self.add_item(SetRoleButton(self))
        
        # Row 3: Recursos extras
        self.add_item(RandomMessagesButton(self))
        self.add_item(DMToggleButton(self))
        self.add_item(RestoreRolesToggleButton(self))
        
        # Row 4: Navegação e controles
        self.add_item(BackWelcomeButton(self))
        self.add_item(CloseButton(self))
    
    def create_embed(self) -> discord.Embed:
        """Cria o embed do painel."""
        config = self.get_config()
        
        embed = discord.Embed(
            title="👋 Painel de Boas-vindas",
            description=(
                "**Como funciona:** Envia mensagem automática quando alguém entra no servidor.\n\n"
                "**Passo 1:** Configure o canal onde a mensagem será enviada\n"
                "**Passo 2:** Personalize o texto (use {user} para mencionar, {server} para nome do servidor)\n"
                "**Passo 3:** Ative o sistema\n\n"
                "**Status:** " + ("🟢 Ativado" if config.get('enabled') else "🔴 Desativado (configure o canal primeiro)")
            ),
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        
        # Campo: Canal
        channel_text = f"<#{config['channel_id']}>" if config.get('channel_id') else "❌ Não configurado"
        embed.add_field(
            name="📢 Canal de Boas-vindas",
            value=channel_text,
            inline=True
        )
        
        # Campo: Cargo
        role_text = f"<@&{config['role_id']}>" if config.get('role_id') else "❌ Não configurado"
        embed.add_field(
            name="🎭 Cargo Automático",
            value=role_text,
            inline=True
        )
        
        # Campo: Cor
        color_hex = f"#{config.get('color', 0x00FF00):06X}"
        embed.add_field(
            name="🎨 Cor da Embed",
            value=color_hex,
            inline=True
        )
        
        # Preview dos textos
        embed.add_field(
            name="📝 Título Atual",
            value=f"```{config.get('title', 'Não definido')[:50]}```",
            inline=False
        )
        
        embed.add_field(
            name="📄 Descrição Atual",
            value=f"```{config.get('description', 'Não definido')[:100]}...```",
            inline=False
        )
        
        embed.set_footer(
            text="💡 Use {user} para mencionar | {server} para nome | Clique em Preview para testar"
        )
        
        extras = []
        if config.get('random_messages'):
            extras.append(f"Frases aleatórias: {len(config.get('random_messages'))}")
        extras.append(f"DM: {'✅' if config.get('dm_enabled') else '❌'}")
        extras.append(f"Restore Cargos: {'✅' if config.get('restore_roles') else '❌'}")
        extras.append(f"Contador: {'✅' if config.get('member_counter') else '❌'}")
        if config.get('leave_message'):
            extras.append('Leave: ✅')
        embed.add_field(name="🔧 Extras", value=" | ".join(extras), inline=False)

        embed = self.config_manager.apply_style(self.guild_id, embed)
        return embed


# ==================== BOTÕES DO PAINEL ====================

class ToggleButton(Button):
    """Botão para ativar/desativar o sistema."""
    
    def __init__(self, panel: WelcomePanel):
        config = panel.get_config()
        enabled = config.get('enabled', False)
        super().__init__(
            label="Desativar" if enabled else "Ativar",
            style=discord.ButtonStyle.success if not enabled else discord.ButtonStyle.danger,
            emoji="🔴" if enabled else "🟢",
            row=0
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        config = self.panel.get_config()
        new_state = not config.get('enabled', False)
        
        if new_state and not config.get('channel_id'):
            await self.panel.send_error(interaction, "Configure um canal antes de ativar!")
            return
        
        self.panel.update_config({'enabled': new_state})
        await self.panel.send_success(
            interaction,
            f"Sistema de boas-vindas {'ativado' if new_state else 'desativado'}!"
        )
        await self.panel.refresh(interaction)


class PreviewButton(Button):
    """Botão para visualizar a mensagem."""
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Preview",
            style=discord.ButtonStyle.secondary,
            emoji="👁️",
            row=0
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        config = self.panel.get_config()
        
        # Criar embed de preview
        preview = discord.Embed(
            title=config.get('title', '').format(user=interaction.user.mention, server=interaction.guild.name),
            description=config.get('description', '').format(user=interaction.user.mention, server=interaction.guild.name),
            color=config.get('color', 0x00FF00),
            timestamp=discord.utils.utcnow()
        )
        
        if config.get('footer'):
            preview.set_footer(text=config['footer'])
        
        if config.get('image_url'):
            preview.set_image(url=config['image_url'])
        
        if config.get('thumbnail_url'):
            preview.set_thumbnail(url=config['thumbnail_url'])
        
        await interaction.response.send_message(
            content="👁️ **Preview da mensagem de boas-vindas:**",
            embed=preview,
            ephemeral=True
        )


class TestButton(Button):
    """Botão para enviar teste no canal."""
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Testar",
            style=discord.ButtonStyle.primary,
            emoji="🧪",
            row=0
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        config = self.panel.get_config()
        
        if not config.get('channel_id'):
            await self.panel.send_error(interaction, "Configure um canal primeiro!")
            return
        
        channel = interaction.guild.get_channel(config['channel_id'])
        if not channel:
            await self.panel.send_error(interaction, "Canal não encontrado!")
            return
        
        # Criar embed de teste
        test_embed = discord.Embed(
            title=config.get('title', '').format(user=interaction.user.mention, server=interaction.guild.name),
            description=config.get('description', '').format(user=interaction.user.mention, server=interaction.guild.name),
            color=config.get('color', 0x00FF00),
            timestamp=discord.utils.utcnow()
        )
        
        if config.get('footer'):
            test_embed.set_footer(text=config['footer'])
        
        if config.get('image_url'):
            test_embed.set_image(url=config['image_url'])
        
        if config.get('thumbnail_url'):
            test_embed.set_thumbnail(url=config['thumbnail_url'])
        
        try:
            await channel.send(embed=test_embed)
            await self.panel.send_success(interaction, f"Mensagem de teste enviada em {channel.mention}!")
        except discord.Forbidden:
            await self.panel.send_error(interaction, "Não tenho permissão para enviar mensagens nesse canal!")


class EditTextsButton(Button):
    """Botão para editar todos os textos."""
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Editar Textos",
            style=discord.ButtonStyle.secondary,
            emoji="📝",
            row=1
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        config = self.panel.get_config()
        
        async def save_texts(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config(data)
            await self.panel.send_success(inter, "Textos atualizados com sucesso!")
            await self.panel.refresh(inter)
        
        modal = EditTextModal(
            title="📝 Editar Textos da Boas-vindas",
            fields={
                'title': {
                    'label': 'Título',
                    'default': config.get('title', ''),
                    'max_length': 256,
                    'placeholder': 'Ex: 🎉 Bem-vindo ao {server}!'
                },
                'leave_message': {
                    'label': 'Mensagem de saída ({user},{server})',
                    'default': config.get('leave_message',''),
                    'max_length': 256,
                    'required': False,
                    'placeholder': 'Ex: 👋 {user} saiu do {server}.'
                },
                'description': {
                    'label': 'Descrição',
                    'default': config.get('description', ''),
                    'max_length': 2048,
                    'style': discord.TextStyle.paragraph,
                    'placeholder': 'Olá {user}! Seja bem-vindo...'
                },
                'footer': {
                    'label': 'Rodapé',
                    'default': config.get('footer', ''),
                    'max_length': 256,
                    'required': False,
                    'placeholder': 'Aproveite sua estadia!'
                }
            },
            callback=save_texts
        )
        
        await interaction.response.send_modal(modal)


class EditColorButton(Button):
    """Botão para editar cor."""
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Cor",
            style=discord.ButtonStyle.secondary,
            emoji="🎨",
            row=1
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        async def save_color(inter: discord.Interaction, color: int):
            self.panel.update_config({'color': color})
            await self.panel.send_success(inter, f"Cor atualizada para #{color:06X}!")
            await self.panel.refresh(inter)
        
        modal = ColorPickerModal(callback=save_color)
        await interaction.response.send_modal(modal)


class SetImageButton(Button):
    """Botão para definir imagem principal."""
    def __init__(self, panel: WelcomePanel):
        super().__init__(label="Imagem", style=discord.ButtonStyle.secondary, emoji="🖼️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        async def save_image(inter: discord.Interaction, url: str, field_type: str):
            self.panel.update_config({'image_url': url})
            await self.panel.send_success(inter, "Imagem atualizada!")
            await self.panel.refresh(inter)
        await interaction.response.send_modal(ImageURLModal(callback=save_image, field_type="image"))

class SetThumbnailButton(Button):
    """Botão para definir thumbnail."""
    def __init__(self, panel: WelcomePanel):
        super().__init__(label="Miniatura", style=discord.ButtonStyle.secondary, emoji="🖼️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        async def save_thumb(inter: discord.Interaction, url: str, field_type: str):
            self.panel.update_config({'thumbnail_url': url})
            await self.panel.send_success(inter, "Thumbnail atualizada!")
            await self.panel.refresh(inter)
        await interaction.response.send_modal(ImageURLModal(callback=save_thumb, field_type="thumbnail"))
class BackWelcomeButton(Button):
    """Botão para voltar ao menu principal de painéis."""
    def __init__(self, panel: WelcomePanel):
        super().__init__(label="Voltar", style=discord.ButtonStyle.primary, emoji="🔙", row=4)
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

class ManualWelcomeButton(Button):
    """Botão de manual do painel de boas-vindas."""
    def __init__(self, panel: WelcomePanel):
        super().__init__(label="Manual", style=discord.ButtonStyle.success, emoji="📖", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Manual do Sistema de Boas-Vindas",
            description=(
                "**Guia completo para criar mensagens de boas-vindas profissionais.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x00FF00,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="🚀 Passo 1: Ativar e Testar",
            value=(
                "1️⃣ **Ativar**: Clique no botão verde para ativar o sistema\n"
                "2️⃣ **Preview**: Visualize como ficará a mensagem\n"
                "3️⃣ **Testar**: Envie mensagem de teste para você mesmo\n"
                "4️⃣ **Configurar Canal**: Defina onde enviar boas-vindas"
            ),
            inline=False
        )
        
        embed.add_field(
            name="✏️ Passo 2: Personalizar Textos",
            value=(
                "**Variáveis disponíveis:**\n"
                "`{user}` - Menciona o usuário\n"
                "`{user_name}` - Nome do usuário\n"
                "`{guild}` - Nome do servidor\n"
                "`{member_count}` - Total de membros\n\n"
                "**Exemplo:**\n"
                "```Bem-vindo {user} ao {guild}!\n"
                "Você é o membro #{member_count}!```"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎨 Passo 3: Estilizar Visual",
            value=(
                "🎨 **Cor**: Escolha cor hexadecimal (ex: #FF0000)\n"
                "🖼️ **Imagem**: URL da imagem principal\n"
                "🖼️ **Miniatura**: URL da miniatura (ícone menor)\n"
                "🎭 **Cargo Automático**: Dar cargo ao entrar"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎲 Recursos Extras",
            value=(
                "🔁 **Frases Aleatórias**: Variar mensagens\n"
                "📩 **DM Toggle**: Enviar no privado do membro\n"
                "🔒 **Restore Cargos**: Restaurar cargos de quem sai e volta\n"
                "💼 **Mensagem de Saída**: Aviso quando alguém sai"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Dica: Use Preview antes de ativar! Teste as variáveis para garantir que funcionam.")
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Miniatura",
            style=discord.ButtonStyle.secondary,
            emoji="🎴",
            row=2
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        async def save_thumbnail(inter: discord.Interaction, url: str, field_type: str):
            self.panel.update_config({'thumbnail_url': url})
            await self.panel.send_success(inter, "Miniatura atualizada!")
            await self.panel.refresh(inter)
        
        modal = ImageURLModal(callback=save_thumbnail, field_type="thumbnail")
        await interaction.response.send_modal(modal)


class SetChannelButton(Button):
    """Botão para definir canal."""
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Canal",
            style=discord.ButtonStyle.secondary,
            emoji="📢",
            row=3
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        # Criar view temporária com channel select
        class ChannelSelectView(discord.ui.View):
            def __init__(self, parent_panel):
                super().__init__(timeout=60)
                self.panel = parent_panel
                
                async def on_channel_select(inter, channel):
                    self.panel.update_config({'channel_id': channel.id})
                    await self.panel.send_success(inter, f"Canal configurado: {channel.mention}")
                    await self.panel.refresh(inter)
                
                self.add_item(ChannelSelect(callback=on_channel_select))
        
        view = ChannelSelectView(self.panel)
        await interaction.response.send_message(
            "📢 Selecione o canal de boas-vindas:",
            view=view,
            ephemeral=True
        )


class SetRoleButton(Button):
    """Botão para definir cargo automático."""
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Cargo",
            style=discord.ButtonStyle.secondary,
            emoji="🎭",
            row=3
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        # Criar view temporária com role select
        class RoleSelectView(discord.ui.View):
            def __init__(self, parent_panel):
                super().__init__(timeout=60)
                self.panel = parent_panel
                
                async def on_role_select(inter, role):
                    self.panel.update_config({'role_id': role.id})
                    await self.panel.send_success(inter, f"Cargo configurado: {role.mention}")
                    await self.panel.refresh(inter)
                
                self.add_item(RoleSelect(callback=on_role_select))
        
        view = RoleSelectView(self.panel)
        await interaction.response.send_message(
            "🎭 Selecione o cargo a ser dado automaticamente:",
            view=view,
            ephemeral=True
        )


class CloseButton(Button):
    """Botão para fechar o painel."""
    
    def __init__(self, panel: WelcomePanel):
        super().__init__(
            label="Fechar",
            style=discord.ButtonStyle.secondary,
            emoji="❌",
            row=4
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        
        embed = discord.Embed(
            description="✅ Painel fechado. Todas as configurações foram salvas.",
            color=0x00FF00
        )
        
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()

class RandomMessagesButton(Button):
    def __init__(self, panel: WelcomePanel):
        super().__init__(label="Frases", style=discord.ButtonStyle.secondary, emoji="🔁", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        existing = cfg.get('random_messages', [])
        fields = {}
        for i in range(1, 6):
            fields[f'msg_{i}'] = {
                'label': f'Frase {i}',
                'default': existing[i-1] if i-1 < len(existing) else '',
                'required': False,
                'max_length': 200,
                'placeholder': 'Use {user} {server} variáveis'
            }
        async def _submit(inter: discord.Interaction, data):
            msgs = [v for k,v in data.items() if v.strip()]
            self.panel.update_config({'random_messages': msgs})
            await self.panel.send_success(inter, f"{len(msgs)} frases salvas.")
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Editar Frases Aleatórias', fields, _submit))

class DMToggleButton(Button):
    def __init__(self, panel: WelcomePanel):
        super().__init__(label="DM", style=discord.ButtonStyle.secondary, emoji="📩", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        if not cfg.get('dm_enabled'):
            fields = {
                'dm_message': {
                    'label': 'Mensagem DM',
                    'default': cfg.get('dm_message', ''),
                    'required': True,
                    'max_length': 500,
                    'style': discord.TextStyle.paragraph
                }
            }
            async def _submit(inter, data):
                self.panel.update_config({'dm_enabled': True, 'dm_message': data['dm_message']})
                await self.panel.send_success(inter, 'Mensagem DM configurada e ativada.')
                await self.panel.refresh(inter)
            await interaction.response.send_modal(EditTextModal('Configurar Mensagem DM', fields, _submit))
        else:
            self.panel.update_config({'dm_enabled': False})
            await self.panel.send_success(interaction, 'Envio de DM desativado.')
            await self.panel.refresh(interaction)

class RestoreRolesToggleButton(Button):
    def __init__(self, panel: WelcomePanel):
        super().__init__(label="Restore Cargos", style=discord.ButtonStyle.secondary, emoji="🔒", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('restore_roles', False)
        self.panel.update_config({'restore_roles': new_state})
        await self.panel.send_success(interaction, f"Restore cargos {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)
