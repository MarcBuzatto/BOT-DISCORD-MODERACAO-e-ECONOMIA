"""
Painéis de Configuração - Economia e Moderação
Desenvolvido por: MARKIZIN
"""

import discord
from discord.ui import Button, Select
from .panel_system import BasePanel, EditTextModal, ColorPickerModal, ChannelSelect
from typing import Dict, Any

# Certifique-se que ModerationPanel está definido antes do uso


# ==================== PAINEL DE ECONOMIA ====================

class EconomyPanel(BasePanel):
    """Painel de configuração de economia."""
    
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, "economy")
        self._build_buttons()
    
    def _build_buttons(self):
        # Row 0: Configurações de daily
        self.add_item(ManualEconomyButton(self))
        self.add_item(EditDailyAmountButton(self))
        self.add_item(EditDailyCooldownButton(self))
        
        # Row 1: Cores das embeds
        self.add_item(EditSaldoColorButton(self))
        self.add_item(EditDailyColorButton(self))
        
        # Row 2: Recursos funcionais
        self.add_item(ToggleTransferButton(self))
        self.add_item(ManageShopButton(self))
        
        # Row 3: Personalização de mensagens
        self.add_item(CustomizeEconomyMessagesButton(self))
        self.add_item(CustomizeEconomyExtraMessagesButton(self))
        
        # Row 4: Navegação e controles
        self.add_item(BackEconomyButton(self))
        self.add_item(CloseEconomyButton(self))
        self.add_item(DeleteEconomyButton(self))
    
    def create_embed(self) -> discord.Embed:
        config = self.get_config()
        
        embed = discord.Embed(
            title="💰 Painel de Economia",
            description=(
                "**Como funciona:** Sistema de créditos virtuais para seu servidor.\n\n"
                "**Comandos disponíveis:**\n"
                "• `/daily` - Membros ganham créditos diários\n"
                "• `/saldo` - Ver saldo de créditos\n"
                "• `/transferir` - Enviar créditos para outros\n"
                "• `/buy` - Comprar itens da loja (se ativada)\n\n"
                "**Configure:** Valor do daily, cores das mensagens, loja de itens."
            ),
            color=0xFFD700,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="💡 Dica: Personalize as mensagens para deixar o sistema único do seu servidor")
        
        # Daily
        embed.add_field(
            name="💵 Valor do Daily",
            value=f"```{config.get('daily_amount', 100)} créditos```",
            inline=True
        )
        
        cooldown_hours = config.get('daily_cooldown', 86400) / 3600
        embed.add_field(
            name="⏰ Cooldown do Daily",
            value=f"```{cooldown_hours} horas```",
            inline=True
        )
        
        # Transfer
        transfer_status = "🟢 Ativado" if config.get('transfer_enabled', True) else "🔴 Desativado"
        embed.add_field(
            name="💸 Transferências",
            value=transfer_status,
            inline=True
        )
        
        # Cores
        saldo_color = f"#{config.get('saldo_color', 0xFFD700):06X}"
        daily_color = f"#{config.get('daily_color', 0x00FF00):06X}"
        
        embed.add_field(
            name="🎨 Cores",
            value=f"**Saldo:** {saldo_color}\n**Daily:** {daily_color}",
            inline=False
        )

        # Shop
        shop_items = config.get('shop_items', [])
        shop_status = "🟢 Ativado" if config.get('shop_enabled') else "🔴 Desativado"
        items_preview = ", ".join([f"{it['name']}({it['price']})" for it in shop_items[:5]]) or "Nenhum"
        embed.add_field(name="🛍️ Loja", value=f"Status: {shop_status}\nItens: {items_preview}", inline=False)
        
        embed.set_footer(text="💡 Personalize a experiência de economia do seu servidor")
        
        embed = self.config_manager.apply_style(self.guild_id, embed)
        return embed


class EditDailyAmountButton(Button):
    def __init__(self, panel: EconomyPanel):
        super().__init__(label="Valor Daily", style=discord.ButtonStyle.secondary, emoji="💵", row=0)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        class AmountModal(discord.ui.Modal, title="💵 Definir Valor do Daily"):
            amount = discord.ui.TextInput(
                label="Quantidade de Créditos",
                placeholder="Ex: 100",
                required=True,
                max_length=10
            )
            
            def __init__(self, parent_panel):
                super().__init__()
                self.panel = parent_panel
            
            async def on_submit(self, inter: discord.Interaction):
                try:
                    value = int(self.amount.value)
                    if value <= 0:
                        raise ValueError
                    self.panel.update_config({'daily_amount': value})
                    await self.panel.send_success(inter, f"Valor do daily atualizado para {value} créditos!")
                    await self.panel.refresh(inter)
                except ValueError:
                    await self.panel.send_error(inter, "Valor inválido! Use um número positivo.")
        
        await interaction.response.send_modal(AmountModal(self.panel))


class EditDailyCooldownButton(Button):
    def __init__(self, panel: EconomyPanel):
        super().__init__(label="Cooldown Daily", style=discord.ButtonStyle.secondary, emoji="⏰", row=0)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        class CooldownModal(discord.ui.Modal, title="⏰ Definir Cooldown do Daily"):
            hours = discord.ui.TextInput(
                label="Horas de Cooldown",
                placeholder="Ex: 24",
                required=True,
                max_length=5
            )
            
            def __init__(self, parent_panel):
                super().__init__()
                self.panel = parent_panel
            
            async def on_submit(self, inter: discord.Interaction):
                try:
                    value = float(self.hours.value)
                    if value <= 0:
                        raise ValueError
                    seconds = int(value * 3600)
                    self.panel.update_config({'daily_cooldown': seconds})
                    await self.panel.send_success(inter, f"Cooldown atualizado para {value} horas!")
                    await self.panel.refresh(inter)
                except ValueError:
                    await self.panel.send_error(inter, "Valor inválido! Use um número positivo.")
        
        await interaction.response.send_modal(CooldownModal(self.panel))


class EditSaldoColorButton(Button):
    def __init__(self, panel: EconomyPanel):
        super().__init__(label="Cor Saldo", style=discord.ButtonStyle.secondary, emoji="🎨", row=1)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        async def save_color(inter: discord.Interaction, color: int):
            self.panel.update_config({'saldo_color': color})
            await self.panel.send_success(inter, f"Cor do saldo atualizada para #{color:06X}!")
            await self.panel.refresh(inter)
        
        modal = ColorPickerModal(callback=save_color)
        await interaction.response.send_modal(modal)


class EditDailyColorButton(Button):
    def __init__(self, panel: EconomyPanel):
        super().__init__(label="Cor Daily", style=discord.ButtonStyle.secondary, emoji="🎨", row=1)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        async def save_color(inter: discord.Interaction, color: int):
            self.panel.update_config({'daily_color': color})
            await self.panel.send_success(inter, f"Cor do daily atualizada para #{color:06X}!")
            await self.panel.refresh(inter)
        
        modal = ColorPickerModal(callback=save_color)
        await interaction.response.send_modal(modal)


class ToggleTransferButton(Button):
    def __init__(self, panel: EconomyPanel):
        config = panel.get_config()
        enabled = config.get('transfer_enabled', True)
        super().__init__(
            label="Desativar Transferências" if enabled else "Ativar Transferências",
            style=discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success,
            emoji="💸",
            row=2
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        config = self.panel.get_config()
        new_state = not config.get('transfer_enabled', True)
        self.panel.update_config({'transfer_enabled': new_state})
        await self.panel.send_success(
            interaction,
            f"Transferências {'ativadas' if new_state else 'desativadas'}!"
        )
        await self.panel.refresh(interaction)


class ManageShopButton(Button):
        def __init__(self, panel: EconomyPanel):
            super().__init__(label="Loja", style=discord.ButtonStyle.secondary, emoji="🛍️", row=2)
            self.panel = panel
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message("**🛍️ Como funciona a Loja:**\n\n**O que é?** Membros gastam créditos para comprar itens virtuais.\n\n**Como configurar:**\nDigite itens no formato: `nome:preço`\nSepare com ponto e vírgula (`;`)\n\n**Exemplo:**\n```\nVIP Mensal:5000;Cargo Colorido:2000;Destaque no Chat:1000\n```\n\n**Como comprar:** Membros usam `/buy nome_do_item`", ephemeral=True)
            cfg = self.panel.get_config()
            fields = {
                'shop_enabled': {
                    'label': 'Ativar loja? (sim/nao)',
                    'default': 'sim' if cfg.get('shop_enabled') else 'nao',
                    'max_length': 5
                },
                'shop_items': {
                    'label': 'Itens (nome:preco separados por ;)',
                    'default': ';'.join([f"{it['name']}:{it['price']}" for it in cfg.get('shop_items', [])]),
                    'max_length': 1000,
                    'required': False,
                    'style': discord.TextStyle.paragraph,
                    'placeholder': 'VIP:5000;Cargo Colorido:2000;Destaque:1000'
                }
            }
            async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
                enabled = data['shop_enabled'].strip().lower() in ('sim','s','true','1')
                raw_items = data['shop_items'].strip()
                items = []
                if raw_items:
                    for part in raw_items.split(';'):
                        if ':' in part:
                            name, price = part.split(':',1)
                            name = name.strip()[:40]
                            try:
                                val = int(price.strip())
                                if val>0:
                                    items.append({'name': name, 'price': val})
                            except Exception:
                                continue
                self.panel.update_config({'shop_enabled': enabled, 'shop_items': items})
                msg = f"✅ Loja {'ativada' if enabled else 'desativada'} com {len(items)} item(s)."
                if items:
                    msg += f"\n\n**Itens disponíveis:**\n" + '\n'.join([f"• {it['name']} - {it['price']} créditos" for it in items[:5]])
                    msg += "\n\n**Para comprar:** Use `/buy nome_do_item`"
                await self.panel.send_success(inter, msg)
                await self.panel.refresh(inter)
            modal = EditTextModal('Configurar Loja', fields, _submit)
            await interaction.response.send_modal(modal)

class CustomizeEconomyMessagesButton(Button):
    def __init__(self, panel: EconomyPanel):
        super().__init__(label="Mensagens", style=discord.ButtonStyle.secondary, emoji="💬", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'daily_success_message': {'label':'Daily sucesso ({amount},{currency},{balance})', 'default': cfg.get('daily_success_message',''), 'max_length':200},
            'transfer_success_message': {'label':'Transfer ({sender},{receiver},{amount},{currency})', 'default': cfg.get('transfer_success_message',''), 'max_length':200},
            'buy_success_message': {'label':'Compra ({item},{price},{currency})', 'default': cfg.get('buy_success_message',''), 'max_length':200},
            'insufficient_funds_message': {'label':'Saldo insuficiente ({balance},{currency})', 'default': cfg.get('insufficient_funds_message',''), 'max_length':200}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config(data)
            await self.panel.send_success(inter, 'Mensagens atualizadas.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Personalizar Mensagens Economia', fields, _submit))

class CustomizeEconomyExtraMessagesButton(Button):
    def __init__(self, panel: EconomyPanel):
        super().__init__(label="Extras", style=discord.ButtonStyle.secondary, emoji="🧩", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'shop_purchase_error': {'label':'Erro compra ({item})', 'default': cfg.get('shop_purchase_error',''), 'max_length':150},
            'transfer_error_message': {'label':'Erro transferência ({reason})', 'default': cfg.get('transfer_error_message',''), 'max_length':150},
            'currency_emoji': {'label':'Emoji moeda', 'default': cfg.get('currency_emoji','💰'), 'max_length':10},
            'daily_emoji': {'label':'Emoji daily', 'default': cfg.get('daily_emoji','🕒'), 'max_length':10},
            'shop_emoji': {'label':'Emoji loja', 'default': cfg.get('shop_emoji','🛍️'), 'max_length':10}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config(data)
            await self.panel.send_success(inter, 'Mensagens extras economia atualizadas.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Mensagens Extras Economia', fields, _submit))

class CloseEconomyButton(Button):
    def __init__(self, panel):
        super().__init__(label="Fechar", style=discord.ButtonStyle.secondary, emoji="❌", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        embed = discord.Embed(description="✅ Painel de economia fechado.", color=0x00FF00)
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()

class DeleteEconomyButton(Button):
    def __init__(self, panel):
        super().__init__(label="Apagar", style=discord.ButtonStyle.danger, emoji="🗑️", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Painel apagado com sucesso!", ephemeral=True)
        await interaction.message.delete()
        self.panel.stop()

class BackEconomyButton(Button):
    def __init__(self, panel):
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

class ManualEconomyButton(Button):
    def __init__(self, panel):
        super().__init__(label="Manual", style=discord.ButtonStyle.success, emoji="📖", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Manual do Sistema de Economia",
            description=(
                "**Guia completo para configurar sistema de créditos virtuais.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xFFD700,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="💵 Passo 1: Configurar Daily",
            value=(
                "1️⃣ **Valor Daily**: Quantos créditos membros ganham por dia\n"
                "   • Sugestão inicial: 100-500 créditos\n"
                "2️⃣ **Cooldown**: Intervalo entre coletas (em horas)\n"
                "   • Padrão: 24 horas (86400 segundos)\n"
                "   • Pode ser 12h, 6h ou personalizado"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎨 Passo 2: Personalizar Cores",
            value=(
                "**Cor Saldo**: Cor da embed do comando `/saldo`\n"
                "**Cor Daily**: Cor da embed do comando `/daily`\n\n"
                "💡 Use cores hex (#FF0000) ou decimais (16711680)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💸 Passo 3: Transferências",
            value=(
                "**Toggle Transfer**: Permite membros enviarem créditos\n"
                "• Ativado: Membros podem usar `/transferir`\n"
                "• Desativado: Apenas daily e loja funcionam\n\n"
                "⚠️ Recomendado: Desativar se houver problemas de farm"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛍️ Passo 4: Loja de Itens",
            value=(
                "Clique em **Loja** para gerenciar:\n"
                "• Adicionar itens para venda\n"
                "• Definir preços em créditos\n"
                "• Configurar ações ao comprar (dar cargo, enviar msg)\n"
                "• Remover itens esgotados\n\n"
                "Membros usam `/buy <item>` para comprar"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💬 Passo 5: Mensagens Customizadas",
            value=(
                "**Mensagens**: Textos de daily, saldo, transferência\n"
                "**Extras**: Mensagens de erro, sucesso, loja\n\n"
                "Use variáveis: `{user}`, `{amount}`, `{balance}`"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Dica: Comece com valores baixos e ajuste conforme engajamento!")
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CustomizeModerationDMButton(Button):
    def __init__(self, panel):
        super().__init__(label="Mensagens DM", style=discord.ButtonStyle.secondary, emoji="📬", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'dm_on_action': {'label':'Enviar DM? (sim/nao)', 'default': 'sim' if cfg.get('dm_on_action',True) else 'nao', 'max_length':5},
            'kick_dm_message': {'label':'Kick DM ({server},{reason})', 'default': cfg.get('kick_dm_message',''), 'max_length':300},
            'ban_dm_message': {'label':'Ban DM ({server},{reason})', 'default': cfg.get('ban_dm_message',''), 'max_length':300},
            'warn_dm_message': {'label':'Warn DM ({server},{reason})', 'default': cfg.get('warn_dm_message',''), 'max_length':300}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            dm_enabled = data['dm_on_action'].strip().lower() in ('sim','s','true','1')
            self.panel.update_config({
                'dm_on_action': dm_enabled,
                'kick_dm_message': data['kick_dm_message'],
                'ban_dm_message': data['ban_dm_message'],
                'warn_dm_message': data['warn_dm_message']
            })
            await self.panel.send_success(inter, 'Mensagens DM atualizadas.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Personalizar Mensagens DM', fields, _submit))

class CustomizeModerationLogTemplatesButton(Button):
    def __init__(self, panel):
        super().__init__(label="Templates Logs", style=discord.ButtonStyle.secondary, emoji="🧾", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'kick_log_template': {'label':'Log Kick ({user},{moderator},{reason})', 'default': cfg.get('kick_log_template',''), 'max_length':300},
            'ban_log_template': {'label':'Log Ban ({user},{moderator},{reason})', 'default': cfg.get('ban_log_template',''), 'max_length':300},
            'warn_log_template': {'label':'Log Warn ({user},{moderator},{reason})', 'default': cfg.get('warn_log_template',''), 'max_length':300}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config(data)
            await self.panel.send_success(inter, 'Templates de log atualizados.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Templates de Logs', fields, _submit))

class CloseModerationButton(Button):
    def __init__(self, panel):
        super().__init__(label="Fechar", style=discord.ButtonStyle.secondary, emoji="❌", row=4)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        embed = discord.Embed(description="✅ Painel fechado.", color=0x00FF00)
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()

class DeleteModerationButton(Button):
    def __init__(self, panel):
        super().__init__(label="Apagar", style=discord.ButtonStyle.danger, emoji="🗑️", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Painel apagado com sucesso!", ephemeral=True)
        await interaction.message.delete()
        self.panel.stop()

class BackModerationButton(Button):
    def __init__(self, panel):
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

class ManualModerationButton(Button):
    def __init__(self, panel):
        super().__init__(label="Manual", style=discord.ButtonStyle.success, emoji="📖", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Manual do Sistema de Moderação",
            description=(
                "**Guia completo para ferramentas de moderação profissional.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xE74C3C,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="📝 Comandos Disponíveis",
            value=(
                "`/ban` - Banir membro permanente ou temporário\n"
                "`/kick` - Expulsar membro do servidor\n"
                "`/warn` - Advertir membro (acumula histórico)\n"
                "`/mute` - Silenciar membro temporariamente\n"
                "`/unmute` - Remover silenciamento\n"
                "`/history` - Ver histórico de punições"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 Canal de Logs",
            value=(
                "Configure um canal para registrar:\n"
                "• Todas as punições aplicadas\n"
                "• Moderador responsável\n"
                "• Motivo da ação\n"
                "• Data e hora\n\n"
                "⚠️ Essencial para auditoria!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🤖 Auto-Moderação",
            value=(
                "**Ativar Auto-Mod**: Moderação automática\n"
                "• Spam detection\n"
                "• Blacklist de palavras\n"
                "• Links suspeitos\n"
                "• Menções em massa\n\n"
                "**Configurar Params**: Ajustar sensibilidade"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Dica: Configure canal de logs primeiro! Sempre registre ações de moderação.")
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== PAINEL DE MODERAÇÃO ====================

class ModerationPanel(BasePanel):
    """Painel de configuração de moderação."""
    
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, "moderation")
        self._build_buttons()
    
    def _build_buttons(self):
        # Row 0: Personalização básica
        self.add_item(ManualModerationButton(self))
        self.add_item(EditMessagesButton(self))
        self.add_item(EditColorsButton(self))
        
        # Row 1: Configurações de log e automod
        self.add_item(SetLogChannelButton(self))
        self.add_item(ToggleConfirmationButton(self))
        self.add_item(ToggleAutoModButton(self))
        
        # Row 2: Parâmetros de automod
        self.add_item(EditAutoModParamsButton(self))
        self.add_item(EditBlacklistButton(self))
        
        # Row 3: Templates e mensagens avançadas
        self.add_item(CustomizeModerationDMButton(self))
        self.add_item(CustomizeModerationLogTemplatesButton(self))
        self.add_item(CustomizeEconomyExtraMessagesButton(self))
        
        # Row 4: Navegação e controles
        self.add_item(BackModerationButton(self))
        self.add_item(CloseModerationButton(self))
        self.add_item(DeleteModerationButton(self))
    
    def create_embed(self) -> discord.Embed:
        config = self.get_config()
        
        embed = discord.Embed(
            title="🛡️ Painel de Moderação",
            description=(
                "**Como funciona:** Ferramentas para moderar seu servidor.\n\n"
                "**Comandos disponíveis:**\n"
                "• `/kick` - Expulsar membro\n"
                "• `/ban` - Banir membro\n"
                "• `/warn` - Advertir membro\n\n"
                "**Configure:**\n"
                "• Canal de logs para registrar ações\n"
                "• Mensagens DM enviadas aos punidos\n"
                "• Auto-moderação (spam, links, caps)\n"
                "• Cores das mensagens de log"
            ),
            color=0xFF0000,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="💡 Dica: Ative o canal de logs para ter histórico completo das ações")
        
        # Log Channel
        log_text = f"<#{config['log_channel_id']}>" if config.get('log_channel_id') else "❌ Não configurado"
        embed.add_field(name="📋 Canal de Logs", value=log_text, inline=False)
        
        # Confirmação
        confirm_status = "🟢 Ativada" if config.get('require_confirmation', True) else "🔴 Desativada"
        embed.add_field(name="⚠️ Confirmação de Ações", value=confirm_status, inline=True)
        
        # Cores
        kick_color = f"#{config.get('kick_color', 0xFF6B00):06X}"
        ban_color = f"#{config.get('ban_color', 0xFF0000):06X}"
        warn_color = f"#{config.get('warn_color', 0xFFA500):06X}"
        
        embed.add_field(
            name="🎨 Cores das Ações",
            value=f"**Kick:** {kick_color}\n**Ban:** {ban_color}\n**Warn:** {warn_color}",
            inline=False
        )

        # Auto-Mod
        am = config.get('auto_mod', {})
        am_status = '🟢 Ativado' if am.get('enabled') else '🔴 Desativado'
        am_desc = (
            f"Status: {am_status}\nSpam limite: {am.get('spam_limit')} msgs/{am.get('cooldown_seconds')}s\n"
            f"Caps: {int(am.get('caps_threshold')*100)}%\nLinks bloqueados: {'✅' if am.get('block_links') else '❌'}\n"
            f"Menções máximas: {am.get('max_mentions')}\nBlacklist: {len(am.get('blacklist_words', []))} palavras"
        )
        embed.add_field(name='🤖 Auto-Mod', value=am_desc, inline=False)
        
        embed.set_footer(text="💡 Personalize as mensagens e ações de moderação")
        
        embed = self.config_manager.apply_style(self.guild_id, embed)
        return embed


class EditMessagesButton(Button):
    def __init__(self, panel: ModerationPanel):
        super().__init__(label="Editar Mensagens", style=discord.ButtonStyle.secondary, emoji="📝", row=0)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        config = self.panel.get_config()
        
        async def save_messages(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config(data)
            await self.panel.send_success(inter, "Mensagens atualizadas!")
            await self.panel.refresh(inter)
        
        modal = EditTextModal(
            title="📝 Editar Mensagens de Moderação",
            fields={
                'kick_message': {
                    'label': 'Mensagem de Kick',
                    'default': config.get('kick_message', ''),
                    'max_length': 512,
                    'style': discord.TextStyle.paragraph,
                    'placeholder': 'Use {user} e {reason}'
                },
                'ban_message': {
                    'label': 'Mensagem de Ban',
                    'default': config.get('ban_message', ''),
                    'max_length': 512,
                    'style': discord.TextStyle.paragraph
                },
                'warn_message': {
                    'label': 'Mensagem de Warn',
                    'default': config.get('warn_message', ''),
                    'max_length': 512,
                    'style': discord.TextStyle.paragraph
                }
            },
            callback=save_messages
        )
        
        await interaction.response.send_modal(modal)


class EditColorsButton(Button):
    def __init__(self, panel: ModerationPanel):
        super().__init__(label="Editar Cores", style=discord.ButtonStyle.secondary, emoji="🎨", row=0)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        # Select para escolher qual cor editar
        class ColorSelect(Select):
            def __init__(self, parent_panel):
                self.panel = parent_panel
                options = [
                    discord.SelectOption(label="Cor do Kick", value="kick_color", emoji="👢"),
                    discord.SelectOption(label="Cor do Ban", value="ban_color", emoji="🚫"),
                    discord.SelectOption(label="Cor do Warn", value="warn_color", emoji="⚠️")
                ]
                super().__init__(placeholder="Escolha qual cor editar", options=options)
            
            async def callback(self, inter: discord.Interaction):
                field = self.values[0]
                
                async def save_color(color_inter: discord.Interaction, color: int):
                    self.panel.update_config({field: color})
                    await self.panel.send_success(color_inter, f"Cor atualizada para #{color:06X}!")
                    await self.panel.refresh(color_inter)
                
                modal = ColorPickerModal(callback=save_color)
                await inter.response.send_modal(modal)
        
        view = discord.ui.View()
        view.add_item(ColorSelect(self.panel))
        await interaction.response.send_message("🎨 Escolha qual cor deseja editar:", view=view, ephemeral=True)


class SetLogChannelButton(Button):
    def __init__(self, panel: ModerationPanel):
        super().__init__(label="Canal de Logs", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        class LogChannelView(discord.ui.View):
            def __init__(self, parent_panel):
                super().__init__(timeout=60)
                self.panel = parent_panel
                
                async def on_channel_select(inter, channel):
                    self.panel.update_config({'log_channel_id': channel.id})
                    await self.panel.send_success(inter, f"Canal de logs configurado: {channel.mention}")
                    await self.panel.refresh(inter)
                
                self.add_item(ChannelSelect(callback=on_channel_select, placeholder="Selecione o canal de logs"))
        
        view = LogChannelView(self.panel)
        await interaction.response.send_message("📋 Selecione o canal de logs:", view=view, ephemeral=True)


class ToggleConfirmationButton(Button):
    def __init__(self, panel: ModerationPanel):
        config = panel.get_config()
        enabled = config.get('require_confirmation', True)
        super().__init__(
            label="Desativar Confirmação" if enabled else "Ativar Confirmação",
            style=discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success,
            emoji="⚠️",
            row=1
        )
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        config = self.panel.get_config()
        new_state = not config.get('require_confirmation', True)
        self.panel.update_config({'require_confirmation': new_state})
        await self.panel.send_success(
            interaction,
            f"Confirmação de ações {'ativada' if new_state else 'desativada'}!"
        )
        await self.panel.refresh(interaction)


class ToggleAutoModButton(Button):
    def __init__(self, panel: ModerationPanel):
        am = panel.get_config().get('auto_mod', {})
        enabled = am.get('enabled', False)
        super().__init__(label='Auto-Mod' + (' Off' if enabled else ' On'), style=discord.ButtonStyle.success if not enabled else discord.ButtonStyle.danger, emoji='🤖', row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        am = cfg.get('auto_mod', {})
        am['enabled'] = not am.get('enabled', False)
        self.panel.update_config({'auto_mod': am})
        await self.panel.send_success(interaction, f"Auto-Mod {'ativado' if am['enabled'] else 'desativado'}.")
        await self.panel.refresh(interaction)

class EditAutoModParamsButton(Button):
    def __init__(self, panel: ModerationPanel):
        super().__init__(label='Params Auto-Mod', style=discord.ButtonStyle.secondary, emoji='⚙️', row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        am = self.panel.get_config().get('auto_mod', {})
        fields = {
            'spam_limit': {'label':'Limite mensagens (janela)', 'default': str(am.get('spam_limit',5)), 'max_length':4},
            'cooldown_seconds': {'label':'Janela segundos', 'default': str(am.get('cooldown_seconds',5)), 'max_length':4},
            'caps_threshold': {'label':'Limite CAPS (0-1)', 'default': str(am.get('caps_threshold',0.7)), 'max_length':5},
            'block_links': {'label':'Bloquear links (sim/nao)', 'default': 'sim' if am.get('block_links',True) else 'nao', 'max_length':5},
            'max_mentions': {'label':'Máx menções', 'default': str(am.get('max_mentions',5)), 'max_length':4},
            'action': {'label':'Ação (delete/warn)', 'default': am.get('action','delete'), 'max_length':6}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            new_am = am.copy()
            try: new_am['spam_limit'] = max(1,int(data['spam_limit']))
            except: pass
            try: new_am['cooldown_seconds'] = max(1,int(data['cooldown_seconds']))
            except: pass
            try:
                val = float(data['caps_threshold'])
                if 0 < val <= 1: new_am['caps_threshold']=val
            except: pass
            new_am['block_links'] = data['block_links'].strip().lower() in ('sim','s','true','1')
            try: new_am['max_mentions'] = max(1,int(data['max_mentions']))
            except: pass
            if data['action'] in ('delete','warn'): new_am['action']=data['action']
            self.panel.update_config({'auto_mod': new_am})
            await self.panel.send_success(inter, 'Parâmetros atualizados.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Parâmetros Auto-Mod', fields, _submit))

class EditBlacklistButton(Button):
    def __init__(self, panel: ModerationPanel):
        super().__init__(label='Blacklist', style=discord.ButtonStyle.secondary, emoji='🚫', row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        am = self.panel.get_config().get('auto_mod', {})
        fields = {
            'blacklist': {
                'label': 'Palavras separadas por vírgula',
                'default': ','.join(am.get('blacklist_words', [])),
                'required': False,
                'max_length': 1000,
                'style': discord.TextStyle.paragraph
            }
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            raw = data['blacklist'].strip()
            words = [w.strip().lower() for w in raw.split(',') if w.strip()][:100]
            am['blacklist_words'] = words
            self.panel.update_config({'auto_mod': am})
            await self.panel.send_success(inter, f"Blacklist atualizada ({len(words)} palavras).")
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Editar Blacklist', fields, _submit))

class CloseModerationButton(Button):
    def __init__(self, panel: ModerationPanel):
        super().__init__(label="Fechar", style=discord.ButtonStyle.secondary, emoji="❌", row=4)
        self.panel = panel
    
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        embed = discord.Embed(description="✅ Painel fechado.", color=0x00FF00)
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()
