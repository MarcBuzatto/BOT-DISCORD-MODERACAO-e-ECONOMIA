"""
Painel de Autorole (Reaction Roles)
Desenvolvido por: MARKIZIN
"""
import discord
from discord.ui import Button
from .panel_system import BasePanel, RoleSelect
import re
from typing import Dict, Any

class AutorolePanel(BasePanel):
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, "autorole")
        self._build_buttons()

    def _build_buttons(self):
        # Row 0: Controles principais
        self.add_item(ManualAutoroleButton(self))
        self.add_item(ToggleAutoroleButton(self))
        self.add_item(SetTargetMessageButton(self))
        
        # Row 1: Gerência de roles
        self.add_item(AddReactionRoleButton(self))
        self.add_item(RemoveReactionRoleButton(self))
        self.add_item(PreviewReactionRolesButton(self))
        
        # Row 2: Navegação e controles
        self.add_item(BackAutoroleButton(self))
        self.add_item(CloseAutoroleButton(self))
        self.add_item(DeleteAutoroleButton(self))

    def create_embed(self) -> discord.Embed:
        cfg = self.get_config()
        enabled = cfg.get('enabled', False)
        rr_list = cfg.get('reaction_roles', [])
        embed = discord.Embed(
            title="🎭 Painel de Autorole (Reaction Roles)",
            description=(
                f"**Status:** {'🟢 Ativado' if enabled else '🔴 Desativado'}\n\n"
                "**Como funciona:** Membros reagem a uma mensagem e ganham cargos automaticamente.\n"
                "**Configure:** Defina mensagem, adicione reações e cargos correspondentes."
            ),
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        if rr_list:
            lines = []
            for idx, rr in enumerate(rr_list, start=1):
                emoji = rr.get('emoji', '?')
                role_id = rr.get('role_id')
                channel_id = rr.get('channel_id')
                message_id = rr.get('message_id')
                unique = rr.get('unique', False)
                lines.append(f"{idx}. {emoji} → <@&{role_id}> | Canal: <#{channel_id}> | Msg: {message_id} | {'Único' if unique else 'Multi'}")
            embed.add_field(name="Reações Configuradas", value="\n".join(lines)[:1024], inline=False)
        else:
            embed.add_field(name="Reações Configuradas", value="Nenhuma reação configurada.", inline=False)
        embed.set_footer(text="Use os botões para adicionar/remover reaction roles.")
        # Aplicar estilo global
        embed = self.config_manager.apply_style(self.guild_id, embed)
        return embed

class ToggleAutoroleButton(Button):
    def __init__(self, panel: AutorolePanel):
        enabled = panel.get_config().get('enabled', False)
        super().__init__(label="Desativar" if enabled else "Ativar", style=discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success, emoji="🔁", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('enabled', False)
        if new_state and not cfg.get('reaction_roles'):
            await self.panel.send_error(interaction, "Adicione pelo menos uma reação antes de ativar.")
            return
        self.panel.update_config({'enabled': new_state})
        await self.panel.send_success(interaction, f"Autorole {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)

class SetTargetMessageButton(Button):
    def __init__(self, panel: AutorolePanel):
        super().__init__(label="Definir Mensagem", style=discord.ButtonStyle.secondary, emoji="📝", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        class TargetModal(discord.ui.Modal, title="📝 Definir Mensagem-Alvo"):
            channel_id_input = discord.ui.TextInput(label="ID do Canal", placeholder="Ex: 123456789012345678", required=True, max_length=20)
            message_id_input = discord.ui.TextInput(label="ID da Mensagem", placeholder="Ex: 987654321098765432", required=True, max_length=20)
            def __init__(self, parent_panel):
                super().__init__()
                self.panel = parent_panel
            async def on_submit(self, inter: discord.Interaction):
                try:
                    channel_id = int(self.channel_id_input.value)
                    message_id = int(self.message_id_input.value)
                    channel = inter.guild.get_channel(channel_id)
                    if not channel:
                        raise ValueError("Canal inválido")
                    try:
                        await channel.fetch_message(message_id)
                    except Exception:
                        raise ValueError("Mensagem não encontrada ou inacessível")
                    # Salva referência genérica (mensagem pode ter múltiplas reações configuradas depois)
                    cfg = self.panel.get_config()
                    cfg.setdefault('base_messages', set())
                    # sets não são serializáveis - converter para lista
                    existing = cfg.get('base_messages', [])
                    if message_id not in existing:
                        existing.append(message_id)
                    self.panel.update_config({'base_messages': existing})
                    await self.panel.send_success(inter, f"Mensagem alvo registrada: {message_id} no canal {channel.mention}")
                    await self.panel.refresh(inter)
                except ValueError as e:
                    await self.panel.send_error(inter, f"Erro: {e}")
        await interaction.response.send_modal(TargetModal(self.panel))

class AddReactionRoleButton(Button):
    def __init__(self, panel: AutorolePanel):
        super().__init__(label="Adicionar", style=discord.ButtonStyle.success, emoji="➕", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        base_list = cfg.get('base_messages', [])
        if not base_list:
            await self.panel.send_error(interaction, "Defina uma mensagem alvo primeiro.")
            return
        class AddRRModal(discord.ui.Modal, title="➕ Novo Reaction Role"):
            message_id_input = discord.ui.TextInput(label="ID da Mensagem", placeholder="Escolha uma das mensagens alvo", required=True, max_length=20)
            emoji_input = discord.ui.TextInput(label="Emoji (Unicode ou :nome:id)", placeholder="😀 ou :custom:123", required=True, max_length=64)
            unique_input = discord.ui.TextInput(label="Grupo Único? (sim/nao)", default="nao", required=True, max_length=5)
            def __init__(self, parent_panel):
                super().__init__()
                self.panel = parent_panel
            async def on_submit(self, inter: discord.Interaction):
                # Escolher cargo via RoleSelect depois
                class RolePickView(discord.ui.View):
                    def __init__(self, parent_modal):
                        super().__init__(timeout=60)
                        self.modal = parent_modal
                        async def on_role_select(role_inter, role):
                            try:
                                message_id = int(self.modal.message_id_input.value)
                                if message_id not in base_list:
                                    raise ValueError("Mensagem não está registrada como alvo.")
                                emoji_raw = self.modal.emoji_input.value.strip()
                                unique_flag = self.modal.unique_input.value.lower() in ("sim", "s", "true", "1")
                                # Padronizar emoji
                                def normalize_emoji(raw: str) -> str:
                                    raw = raw.strip()
                                    # Já no formato <a:name:id> ou <:name:id>
                                    if raw.startswith('<') and raw.endswith('>'):
                                        return raw
                                    # Formatos :name:id ou name:id
                                    m = re.match(r'<a?:([A-Za-z0-9_~]+):(\d+)>', raw)
                                    if m:
                                        # Caso já corresponda, mas faltando <> caiu no if acima
                                        return raw
                                    m2 = re.match(r'a?:?([A-Za-z0-9_~]+):(\d+)', raw)
                                    if m2:
                                        name, _id = m2.groups()
                                        animated = raw.startswith('a:')
                                        return f"<{'a' if animated else ''}:{name}:{_id}>"
                                    # Se for só ID? manter
                                    # Caso unicode retorna direto
                                    return raw
                                emoji = normalize_emoji(emoji_raw)
                                # Verificar canal da mensagem (precisa procurar entre base_messages? usuário forneceu ID da mensagem para qualquer canal) assumimos canal não variado -> precisa do channel_id manual
                                # Para simplicidade pedir canal junto? Reusar message_id para descobrir? Precisaria varredura - simplificar pedindo canal
                                # Ajustar: pedir canal junto
                                # For simplicity, attach channel id = first base channel fetch attempt
                                channel_id = None
                                for ch in inter.guild.text_channels:
                                    try:
                                        m = await ch.fetch_message(message_id)
                                        channel_id = ch.id
                                        break
                                    except Exception:
                                        continue
                                if channel_id is None:
                                    raise ValueError("Mensagem não encontrada em canais acessíveis.")
                                rr_list = self.modal.panel.get_config().get('reaction_roles', [])
                                rr_list.append({
                                    'message_id': message_id,
                                    'channel_id': channel_id,
                                    'emoji': emoji,
                                    'role_id': role.id,
                                    'unique': unique_flag
                                })
                                self.modal.panel.update_config({'reaction_roles': rr_list})
                                await self.modal.panel.send_success(role_inter, f"Reaction role adicionado: {emoji} → {role.mention}")
                                # Adicionar reação na mensagem
                                channel = inter.guild.get_channel(channel_id)
                                try:
                                    target_msg = await channel.fetch_message(message_id)
                                    await target_msg.add_reaction(emoji)
                                except Exception:
                                    pass
                                await self.modal.panel.refresh(role_inter)
                            except ValueError as e:
                                await self.modal.panel.send_error(role_inter, str(e))
                        self.add_item(RoleSelect(callback=on_role_select, placeholder="Selecione o cargo para este emoji"))
                await inter.response.send_message("Selecione o cargo para o reaction role.", view=RolePickView(self), ephemeral=True)
        await interaction.response.send_modal(AddRRModal(self.panel))

class RemoveReactionRoleButton(Button):
    def __init__(self, panel: AutorolePanel):
        super().__init__(label="Remover", style=discord.ButtonStyle.secondary, emoji="➖", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        rr_list = self.panel.get_config().get('reaction_roles', [])
        if not rr_list:
            await self.panel.send_error(interaction, "Nenhum reaction role para remover.")
            return
        # Modal para índice
        class RemoveRRModal(discord.ui.Modal, title="➖ Remover Reaction Role"):
            index_input = discord.ui.TextInput(label="Número da linha", placeholder="Ex: 1", required=True, max_length=4)
            def __init__(self, parent_panel):
                super().__init__()
                self.panel = parent_panel
            async def on_submit(self, inter: discord.Interaction):
                try:
                    idx = int(self.index_input.value) - 1
                    rr_list2 = self.panel.get_config().get('reaction_roles', [])
                    if idx < 0 or idx >= len(rr_list2):
                        raise ValueError("Índice inválido")
                    removed = rr_list2.pop(idx)
                    self.panel.update_config({'reaction_roles': rr_list2})
                    await self.panel.send_success(inter, f"Reaction role removido: {removed.get('emoji')} → <@&{removed.get('role_id')}>")
                    await self.panel.refresh(inter)
                except ValueError as e:
                    await self.panel.send_error(inter, f"Erro: {e}")
        await interaction.response.send_modal(RemoveRRModal(self.panel))

class PreviewReactionRolesButton(Button):
    def __init__(self, panel: AutorolePanel):
        super().__init__(label="Preview", style=discord.ButtonStyle.secondary, emoji="👁️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        rr_list = cfg.get('reaction_roles', [])
        embed = discord.Embed(title="🎭 Reaction Roles Configurados", color=0x5865F2, timestamp=discord.utils.utcnow())
        if rr_list:
            lines = []
            for rr in rr_list:
                lines.append(f"{rr.get('emoji')} → <@&{rr.get('role_id')}> | Msg: {rr.get('message_id')}")
            embed.description = "\n".join(lines)[:4000]
        else:
            embed.description = "Nenhum reaction role configurado."
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CloseAutoroleButton(Button):
    def __init__(self, panel: AutorolePanel):
        super().__init__(label="Fechar", style=discord.ButtonStyle.secondary, emoji="❌", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        embed = discord.Embed(description="✅ Painel de autorole fechado.", color=0x00FF00)
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()

class DeleteAutoroleButton(Button):
    def __init__(self, panel: AutorolePanel):
        super().__init__(label="Apagar", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Painel apagado com sucesso!", ephemeral=True)
        await interaction.message.delete()
        self.panel.stop()

class BackAutoroleButton(Button):
    def __init__(self, panel: AutorolePanel):
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

class ManualAutoroleButton(Button):
    def __init__(self, panel: AutorolePanel):
        super().__init__(label="Manual", style=discord.ButtonStyle.success, emoji="📖", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Manual do Sistema de Autorole",
            description=(
                "**Guia para configurar cargos automáticos por reação.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x9B59B6,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="🚀 Passo 1: Definir Mensagem Alvo",
            value=(
                "1️⃣ **Criar mensagem**: Envie uma mensagem em um canal\n"
                "2️⃣ **Copiar IDs**: Anote ID do canal e ID da mensagem\n"
                "3️⃣ **Definir Target**: Cole os IDs no painel\n\n"
                "💡 **Como pegar IDs**: Modo desenvolvedor > Botão direito > Copiar ID"
            ),
            inline=False
        )
        
        embed.add_field(
            name="➕ Passo 2: Adicionar Reações",
            value=(
                "**Clique em Adicionar** e configure:\n"
                "• **Emoji**: Qual emoji usar (Unicode ou customizado)\n"
                "• **Cargo**: Qual cargo dar\n"
                "• **Único**: Remover outros cargos ao reagir\n"
                "• **Multi**: Permitir acumular vários cargos"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎮 Exemplos de Uso",
            value=(
                "🔴 **Notificações**: Cargos de avisos\n"
                "🎮 **Jogos**: Cargos de comunidades de jogos\n"
                "🎨 **Hobbies**: Arte, música, programação\n"
                "🎓 **Níveis**: Novato, intermediário, expert"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Importante",
            value=(
                "• Bot precisa ter permissão para gerenciar cargos\n"
                "• Cargo do bot deve estar acima dos cargos que ele dará\n"
                "• Ative o sistema após configurar tudo"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Dica: Use Preview para ver lista completa antes de ativar!")
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)
