import discord
from discord.ui import Button
from .panel_system import BasePanel, EditTextModal
from typing import Dict, Any

class EmojisPanel(BasePanel):
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, 'emojis')
        self._build_buttons()
    def _build_buttons(self):
        # Row 0: Gerência de emojis
        self.add_item(ManualEmojisButton(self))
        self.add_item(AddOrUpdateEmojiButton(self))
        self.add_item(RemoveEmojiButton(self))
        self.add_item(ListEmojisButton(self))
        
        # Row 1: Navegação e controles
        self.add_item(BackEmojisButton(self))
        self.add_item(CloseEmojisButton(self))
        self.add_item(DeleteEmojisButton(self))
    def create_embed(self) -> discord.Embed:
        cfg = self.get_config()
        em = discord.Embed(
            title='🧪 Painel de Emojis Globais',
            description=(
                '**Como funciona:** Defina emojis personalizados para usar em mensagens do bot.\n'
                '**Configure:** Adicione pares chave-emoji para usar em templates.'
            ),
            color=0x5865F2
        )
        global_emojis = cfg.get('global_emojis', {})
        if global_emojis:
            lines = [f"`{k}` => {v}" for k,v in list(global_emojis.items())[:25]]
            em.add_field(name='Emojis Definidos', value='\n'.join(lines), inline=False)
        else:
            em.add_field(name='Emojis Definidos', value='Nenhum', inline=False)
        em = self.config_manager.apply_style(self.guild_id, em)
        return em

class AddOrUpdateEmojiButton(Button):
    def __init__(self, panel: EmojisPanel):
        super().__init__(label='Adicionar/Atualizar', style=discord.ButtonStyle.success, emoji='➕', row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'key': {'label':'Chave identificadora (ex: money)', 'default':'', 'max_length':30},
            'emoji': {'label':'Emoji (unicode ou <:nome:id>)', 'default':'', 'max_length':60}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            key = data['key'].strip().lower()
            emoji = data['emoji'].strip()
            if not key or not emoji:
                await self.panel.send_error(inter, 'Chave e emoji necessários.')
                return
            ge = cfg.get('global_emojis', {})
            ge[key] = emoji[:60]
            self.panel.update_config({'global_emojis': ge})
            await self.panel.send_success(inter, f'Emoji salvo: {key} -> {emoji}')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Adicionar Emoji Global', fields, _submit))

class RemoveEmojiButton(Button):
    def __init__(self, panel: EmojisPanel):
        super().__init__(label='Remover', style=discord.ButtonStyle.secondary, emoji='🗑️', row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'key': {'label':'Chave a remover', 'default':'', 'max_length':30}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            key = data['key'].strip().lower()
            ge = cfg.get('global_emojis', {})
            if key in ge:
                ge.pop(key)
                self.panel.update_config({'global_emojis': ge})
                await self.panel.send_success(inter, f'Emoji removido: {key}')
            else:
                await self.panel.send_error(inter, 'Chave não encontrada.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Remover Emoji Global', fields, _submit))

class ListEmojisButton(Button):
    def __init__(self, panel: EmojisPanel):
        super().__init__(label='Listar', style=discord.ButtonStyle.secondary, emoji='📄', row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        ge = cfg.get('global_emojis', {})
        if not ge:
            await interaction.response.send_message('Nenhum emoji global definido.', ephemeral=True)
            return
        lines = [f"`{k}` => {v}" for k,v in ge.items()]
        msg = '\n'.join(lines)[:1900]
        await interaction.response.send_message(f'📄 Emojis Globais:\n{msg}', ephemeral=True)

class CloseEmojisButton(Button):
    def __init__(self, panel: EmojisPanel):
        super().__init__(label='Fechar', style=discord.ButtonStyle.secondary, emoji='❌', row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        em = discord.Embed(description='✅ Painel de emojis fechado.', color=0x00FF00)
        em = self.panel.config_manager.apply_style(self.panel.guild_id, em)
        await interaction.response.edit_message(embed=em, view=self.panel)
        self.panel.stop()

class DeleteEmojisButton(Button):
    def __init__(self, panel: EmojisPanel):
        super().__init__(label='Apagar', style=discord.ButtonStyle.danger, emoji='🗑️', row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message('✅ Painel apagado com sucesso!', ephemeral=True)
        await interaction.message.delete()
        self.panel.stop()

class BackEmojisButton(Button):
    def __init__(self, panel: EmojisPanel):
        super().__init__(label='Voltar', style=discord.ButtonStyle.primary, emoji='🔙', row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        from .panel_command import PanelMainView
        embed = discord.Embed(
            title='🎛️ Painel de Controle - Bot Premium',
            description=(
                'Bem-vindo ao **Centro de Configuração Interativo**!\n\n'
                'Selecione abaixo o módulo que deseja configurar.\n'
                'Todas as alterações são salvas automaticamente.\n\n'
                '**Módulos Disponíveis:**\n'
                '👋 **Boas-vindas** - Mensagem automática ao entrar (fácil!)\n'
                '🎫 **Tickets** - Sistema de suporte profissional\n'
                '💰 **Economia** - Créditos virtuais e loja\n'
                '🛡️ **Moderação** - Kick, ban, warn com logs\n'
                '📋 **Logs** - Registre tudo que acontece\n'
                '🎭 **Autorole** - Cargos automáticos\n'
                '😃 **Emojis Globais** - Emojis reutilizáveis\n\n'
                '**🆘 Precisa de ajuda?** Veja `docs/GUIA_RAPIDO.md`\n'
            ),
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text='💡 Dica: Comece pelo módulo Tickets ou Boas-vindas | Desenvolvido por MARKIZIN')
        view = PanelMainView(self.panel.config_manager, interaction.guild.id, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)

class ManualEmojisButton(Button):
    def __init__(self, panel: EmojisPanel):
        super().__init__(label='Manual', style=discord.ButtonStyle.success, emoji='📖', row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title='📖 Manual de Emojis Globais',
            description=(
                '**Guia para configurar emojis personalizados reutilizáveis.**\n\n'
                '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            ),
            color=0xF39C12,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name='➕ Como Adicionar Emojis',
            value=(
                '1️⃣ **Clique em Adicionar/Atualizar**\n'
                '2️⃣ **Defina chave**: Nome identificador (ex: `money`)\n'
                '3️⃣ **Defina emoji**: Emoji Unicode ou customizado\n\n'
                '**Formatos aceitos:**\n'
                '• Unicode: `💰` `⭐` `✅`\n'
                '• Customizado: `<:nome:123456789>`\n'
                '• Animado: `<a:nome:123456789>`'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🎮 Como Usar nos Templates',
            value=(
                'Use `{emoji_chave}` em mensagens customizáveis:\n\n'
                '**Exemplo:**\n'
                '```Você ganhou {emoji_money} 100 créditos!\n'
                'Parabéns {emoji_star}!```\n\n'
                'Se `money` = `💰` e `star` = `⭐`, resulta em:\n'
                '`Você ganhou 💰 100 créditos! Parabéns ⭐!`'
            ),
            inline=False
        )
        
        embed.add_field(
            name='📜 Exemplos de Chaves Comuns',
            value=(
                '`money` = 💰 | `coin` = 🪙\n'
                '`success` = ✅ | `error` = ❌\n'
                '`star` = ⭐ | `fire` = 🔥\n'
                '`ticket` = 🎫 | `warn` = ⚠️\n'
                '`mod` = 🛡️ | `crown` = 👑'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🔄 Atualizar e Remover',
            value=(
                '**Atualizar**: Adicione com mesma chave, novo emoji\n'
                '**Remover**: Clique em Remover e digite a chave\n'
                '**Listar**: Ver todos os emojis configurados'
            ),
            inline=False
        )
        
        embed.set_footer(text='💡 Dica: Use chaves descritivas (ex: money_icon, success_emoji) para não esquecer!')
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)
