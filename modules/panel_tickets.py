"""
Painel de Tickets - Configuração Avançada
Desenvolvido por: MARKIZIN
"""
import discord
from discord.ui import Button
from .panel_system import BasePanel, ChannelSelect, EditTextModal
from typing import Any, Dict

class TicketsPanel(BasePanel):
    def __init__(self, config_manager, guild_id: int, author_id: int):
        super().__init__(config_manager, guild_id, author_id, "tickets")
        self._build_buttons()

    def _build_buttons(self):
        # Row 0: Ações principais do painel
        self.add_item(ManualTicketsButton(self))
        self.add_item(PostPanelMessageButton(self))
        self.add_item(ToggleTicketsButton(self))
        self.add_item(SetPanelChannelButton(self))
        
        # Row 1: Estrutura base dos tickets
        self.add_item(SetCategoryButton(self))
        self.add_item(SetMultiCategoriesButton(self))
        self.add_item(SetSupportRolesButton(self))
        self.add_item(CustomizeNameTemplateButton(self))
        
        # Row 2: Ajustes avançados e métricas
        self.add_item(ToggleInitialFormButton(self))
        self.add_item(TogglePriorityButton(self))
        self.add_item(EditSLAButton(self))
        self.add_item(EditLimitsButton(self))
        self.add_item(ViewStatsButton(self))
        
        # Row 3: Recursos funcionais dos tickets
        self.add_item(ToggleClaimButton(self))
        self.add_item(ToggleFeedbackButton(self))
        self.add_item(ToggleTranscriptButton(self))
        self.add_item(CustomizeMessagesButton(self))
        self.add_item(EditTicketEmbedButton(self))
        
        # Row 4: Toggles e controles de navegação
        self.add_item(ToggleAutoCloseButton(self))
        self.add_item(ToggleSLAEnabledButton(self))
        self.add_item(BackTicketsButton(self))
        self.add_item(CloseTicketsButton(self))
        self.add_item(DeleteTicketsButton(self))

    def create_embed(self) -> discord.Embed:
        cfg = self.get_config()
        embed = discord.Embed(
            title="🎫 Painel de Tickets - Sistema de Suporte",
            description=(
                "**Como funciona:** Sistema completo de atendimento via tickets privados.\n"
                "**Passo 1:** Configure canal e categoria\n"
                "**Passo 2:** Defina cargos de suporte\n"
                "**Passo 3:** Ative o sistema e poste o painel\n\n"
                f"Status: {'🟢 Ativado' if cfg.get('enabled') else '🔴 Desativado'}\n"
                f"Canal do painel: {'<#'+str(cfg.get('panel_channel_id'))+'>' if cfg.get('panel_channel_id') else '❌ Configure primeiro'}\n"
                f"Categoria única: {'<#'+str(cfg.get('category_id'))+'>' if cfg.get('category_id') else '❌ Configure primeiro'}\n"
                f"Multi categorias: {', '.join([str(cid) for cid in cfg.get('category_ids', [])]) if cfg.get('category_ids') else '❌ Opcional'}\n"
                f"Cargos suporte: {', '.join(['<@&'+str(rid)+'>' for rid in cfg.get('support_role_ids', [])]) if cfg.get('support_role_ids') else '❌ Configure primeiro'}\n"
                f"Claim obrigatório: {'✅' if cfg.get('claim_required') else '❌'} | Feedback: {'✅' if cfg.get('feedback_enabled') else '❌'}\n"
                f"Transcrição: {'✅' if cfg.get('transcript_enabled') else '❌'}\n"
                f"Auto close: {str(cfg.get('auto_close_minutes'))+' min' if cfg.get('auto_close_minutes') else '❌ Desativado'} | Máx abertos: {cfg.get('max_open_per_user', 3)}\n"
                f"Tickets criados: {cfg.get('ticket_counter',0)} | Fechados: {cfg.get('closed_counter',0)}"
            ),
            color=0x5865F2
        )
        embed.set_footer(text="💡 Dica: Comece configurando Canal do Painel e Categoria antes de ativar")
        embed = self.config_manager.apply_style(self.guild_id, embed)
        return embed

class ToggleTicketsButton(Button):
    def __init__(self, panel: TicketsPanel):
        enabled = panel.get_config().get('enabled', False)
        super().__init__(label="Desativar" if enabled else "Ativar", style=discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success, emoji="🔁", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('enabled', False)
        # Requer canal do painel e categoria
        if new_state and (not cfg.get('panel_channel_id') or not cfg.get('category_id')):
            await self.panel.send_error(interaction, "Defina canal do painel e categoria antes de ativar.")
            return
        self.panel.update_config({'enabled': new_state})
        await self.panel.send_success(interaction, f"Tickets {'ativados' if new_state else 'desativados'}.")
        await self.panel.refresh(interaction)

class SetPanelChannelButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Canal Painel", style=discord.ButtonStyle.secondary, emoji="📢", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        class PanelChannelView(discord.ui.View):
            def __init__(self, parent):
                super().__init__(timeout=60)
                async def on_select(inter, channel):
                    parent.update_config({'panel_channel_id': channel.id})
                    await parent.send_success(inter, f"✅ Canal do painel definido: {channel.mention}\n\n**Próximo passo:** Configure a Categoria onde os tickets serão criados.")
                    await parent.refresh(inter)
                self.add_item(ChannelSelect(callback=on_select, placeholder="Selecione canal para painel"))
        embed = discord.Embed(title="📢 Canal do Painel", description="**O que é?** Canal onde os membros clicarão para abrir tickets.\n\n**Recomendação:** Use um canal específico como #suporte ou #atendimento.\n\n**Permissões necessárias:** O bot precisa enviar mensagens e embeds neste canal.", color=0x5865F2)
        await interaction.response.send_message(embed=embed, view=PanelChannelView(self.panel), ephemeral=True)

class SetCategoryButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Categoria", style=discord.ButtonStyle.secondary, emoji="🗂️", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("**🗂️ Como pegar o ID da categoria:**\n\n1️⃣ Ative o Modo Desenvolvedor no Discord (Configurações → Avançado → Modo Desenvolvedor)\n2️⃣ Clique com botão direito na categoria\n3️⃣ Selecione 'Copiar ID'\n4️⃣ Cole o número aqui\n\n**O que é?** Categoria onde os canais de ticket serão criados automaticamente.\n\n**Dica:** Crie uma categoria chamada 'Tickets' antes.", ephemeral=True)
        class CategoryModal(discord.ui.Modal, title="🗂️ Definir Categoria de Tickets"):
            category_id_input = discord.ui.TextInput(label="ID da Categoria (números)", placeholder="Ex: 1234567890123456789", required=True, max_length=20, style=discord.TextStyle.short)
            def __init__(self, parent):
                super().__init__()
                self.panel = parent
            async def on_submit(self, inter: discord.Interaction):
                try:
                    cid = int(self.category_id_input.value.strip())
                    cat = inter.guild.get_channel(cid)
                    if not cat or not isinstance(cat, discord.CategoryChannel):
                        raise ValueError("ID inválido ou não é uma categoria")
                    self.panel.update_config({'category_id': cid})
                    await self.panel.send_success(inter, f"✅ Categoria definida: {cat.name}\n\n**Próximo passo:** Configure os Cargos de Suporte.")
                    await self.panel.refresh(inter)
                except ValueError as e:
                    await self.panel.send_error(inter, f"❌ Erro: {e}\n\nVerifique se copiou apenas números e se é uma categoria válida.")
        modal = CategoryModal(self.panel)
        await interaction.followup.send_modal(modal)

class SetSupportRolesButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Cargos Suporte", style=discord.ButtonStyle.secondary, emoji="🛠️", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("**🛠️ Cargos de Suporte - Explicação:**\n\n**O que são?** Cargos que poderão ver e responder tickets.\n\n**Como pegar IDs:**\n1️⃣ Ative Modo Desenvolvedor\n2️⃣ Clique direito no cargo (Configurações → Cargos)\n3️⃣ Copiar ID\n4️⃣ Cole no campo separando com vírgula\n\n**Exemplo:** 123456789,987654321,555555555\n\n**Importante:** Membros com esses cargos terão acesso a TODOS os tickets.", ephemeral=True)
        class RolesModal(discord.ui.Modal, title="🛠️ Definir Cargos de Suporte"):
            roles_input = discord.ui.TextInput(label="IDs separados por vírgula", placeholder="Ex: 1234567890,9876543210", required=True, max_length=200, style=discord.TextStyle.short)
            def __init__(self, parent):
                super().__init__()
                self.panel = parent
            async def on_submit(self, inter: discord.Interaction):
                raw = self.roles_input.value
                ids = []
                invalid = []
                for part in raw.split(','):
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        rid = int(part)
                        if inter.guild.get_role(rid):
                            ids.append(rid)
                        else:
                            invalid.append(part)
                    except Exception:
                        invalid.append(part)
                msg = f"✅ Cargos de suporte configurados: {len(ids)} cargo(s).\n\n**Próximo passo:** Agora você pode Ativar o sistema e depois Postar o Painel."
                if invalid:
                    msg += f"\n\n⚠️ IDs inválidos ignorados: {', '.join(invalid[:3])}"
                self.panel.update_config({'support_role_ids': ids})
                await self.panel.send_success(inter, msg)
                await self.panel.refresh(inter)
        modal = RolesModal(self.panel)
        await interaction.followup.send_modal(modal)

class ToggleClaimButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Claim", style=discord.ButtonStyle.secondary, emoji="🙋", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('claim_required', False)
        self.panel.update_config({'claim_required': new_state})
        await self.panel.send_success(interaction, f"Claim {'obrigatório' if new_state else 'opcional'}.")
        await self.panel.refresh(interaction)

class ToggleFeedbackButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Feedback", style=discord.ButtonStyle.secondary, emoji="⭐", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('feedback_enabled', True)
        self.panel.update_config({'feedback_enabled': new_state})
        await self.panel.send_success(interaction, f"Feedback {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)

class ToggleTranscriptButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Transcrição", style=discord.ButtonStyle.secondary, emoji="🧾", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('transcript_enabled', True)
        self.panel.update_config({'transcript_enabled': new_state})
        await self.panel.send_success(interaction, f"Transcrição {'ativada' if new_state else 'desativada'}.")
        await self.panel.refresh(interaction)

class EditLimitsButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Limites", style=discord.ButtonStyle.secondary, emoji="⏱️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'auto_close_minutes': {
                'label': 'Auto fechar (minutos, vazio para desativar)',
                'placeholder': 'Ex: 60',
                'default': '' if cfg.get('auto_close_minutes') is None else str(cfg.get('auto_close_minutes')),
                'required': False,
                'max_length': 6
            },
            'max_open_per_user': {
                'label': 'Máx tickets abertos por usuário',
                'placeholder': 'Ex: 3',
                'default': str(cfg.get('max_open_per_user', 3)),
                'required': True,
                'max_length': 3
            }
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            auto_close = data['auto_close_minutes'].strip()
            val_close = None
            if auto_close:
                try:
                    val_close = int(auto_close)
                    if val_close <= 0:
                        val_close = None
                except Exception:
                    val_close = None
            try:
                max_open = int(data['max_open_per_user'])
                if max_open <= 0:
                    max_open = 3
            except Exception:
                max_open = 3
            self.panel.update_config({'auto_close_minutes': val_close, 'max_open_per_user': max_open})
            await self.panel.send_success(inter, "Limites atualizados.")
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Editar Limites', fields, _submit))

class SetMultiCategoriesButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Multi Categorias", style=discord.ButtonStyle.secondary, emoji="📂", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        existing = ','.join([str(cid) for cid in cfg.get('category_ids', [])])
        class MultiCatModal(discord.ui.Modal, title="📂 Definir Multi Categorias"):
            cats_input = discord.ui.TextInput(label="IDs separados por vírgula", placeholder="123,456,789", default=existing, required=False, max_length=200)
            def __init__(self, parent):
                super().__init__()
                self.panel = parent
            async def on_submit(self, inter: discord.Interaction):
                raw = self.cats_input.value
                ids = []
                for part in raw.split(','):
                    try:
                        cid = int(part.strip())
                        cat = inter.guild.get_channel(cid)
                        if isinstance(cat, discord.CategoryChannel):
                            ids.append(cid)
                    except Exception:
                        continue
                self.panel.update_config({'category_ids': ids})
                await self.panel.send_success(inter, f"Multi categorias atualizada ({len(ids)}).")
                await self.panel.refresh(inter)
        await interaction.response.send_modal(MultiCatModal(self.panel))

class CustomizeMessagesButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Mensagens", style=discord.ButtonStyle.secondary, emoji="✏️", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'panel_title': {'label': 'Título Painel', 'default': cfg.get('panel_title',''), 'max_length': 100},
            'panel_description': {'label': 'Descrição Painel', 'default': cfg.get('panel_description',''), 'max_length': 500, 'style': discord.TextStyle.paragraph},
            'panel_button_label': {'label': 'Label Botão', 'default': cfg.get('panel_button_label','Abrir Ticket'), 'max_length': 40},
            'ticket_open_title': {'label': 'Título ao Abrir', 'default': cfg.get('ticket_open_title',''), 'max_length': 100}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            self.panel.update_config(data)
            await self.panel.send_success(inter, 'Mensagens atualizadas.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Personalizar Mensagens', fields, _submit))

class EditTicketEmbedButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Embed Ticket", style=discord.ButtonStyle.secondary, emoji="🖼️", row=3)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        fields = {
            'ticket_open_description': {'label': 'Descrição padrão ticket', 'default': cfg.get('ticket_open_description','Explique seu problema.'), 'style': discord.TextStyle.paragraph, 'max_length': 1000},
            'panel_color': {'label': 'Cor hexadecimal embed (sem #)', 'default': f"{cfg.get('panel_color',0x5865F2):06X}", 'max_length': 6, 'required': True},
            'initial_form_subject_label': {'label': 'Label campo assunto', 'default': cfg.get('initial_form_subject_label','Assunto'), 'max_length': 50},
            'initial_form_description_label': {'label': 'Label campo descrição', 'default': cfg.get('initial_form_description_label','Descrição'), 'max_length': 50}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            # Validar cor
            color_raw = data['panel_color'].strip().upper()
            try:
                if len(color_raw) not in (3,6):
                    raise ValueError
                panel_color = int(color_raw, 16)
            except Exception:
                panel_color = 0x5865F2
            update = {
                'ticket_open_description': data['ticket_open_description'],
                'panel_color': panel_color,
                'initial_form_subject_label': data['initial_form_subject_label'],
                'initial_form_description_label': data['initial_form_description_label']
            }
            self.panel.update_config(update)
            await self.panel.send_success(inter, 'Embed do ticket atualizada.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Editar Embed Ticket', fields, _submit))

class CustomizeNameTemplateButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Template Nome", style=discord.ButtonStyle.secondary, emoji="🏷️", row=1)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        class TemplateModal(discord.ui.Modal, title="🏷️ Template Nome Ticket"):
            template_input = discord.ui.TextInput(label="Template ({counter},{user},{category})", placeholder="ticket-{counter}", default=cfg.get('ticket_name_template','ticket-{counter}'), max_length=50)
            def __init__(self, parent):
                super().__init__()
                self.panel = parent
            async def on_submit(self, inter: discord.Interaction):
                template = self.template_input.value.strip() or 'ticket-{counter}'
                self.panel.update_config({'ticket_name_template': template})
                await self.panel.send_success(inter, f'Template atualizado: {template}')
                await self.panel.refresh(inter)
        await interaction.response.send_modal(TemplateModal(self.panel))

class ToggleInitialFormButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Formulário Inicial", style=discord.ButtonStyle.secondary, emoji="📝", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('require_initial_form', False)
        self.panel.update_config({'require_initial_form': new_state})
        await self.panel.send_success(interaction, f"Formulário inicial {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)

class TogglePriorityButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Prioridades", style=discord.ButtonStyle.secondary, emoji="🚦", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('enable_priority', False)
        self.panel.update_config({'enable_priority': new_state})
        await self.panel.send_success(interaction, f"Sistema de prioridades {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)

class EditSLAButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="SLA", style=discord.ButtonStyle.secondary, emoji="⏱️", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        # Suporte legado (migra antiga chave única para dict se existir)
        if 'sla_minutes' in cfg and 'sla_by_priority' not in cfg and cfg.get('sla_minutes'):
            legacy_val = cfg.get('sla_minutes')
            self.panel.update_config({'sla_by_priority': {'URGENTE': legacy_val, 'NORMAL': legacy_val*2, 'BAIXA': legacy_val*3}})
        sla_map = cfg.get('sla_by_priority', {'URGENTE':120, 'NORMAL':720, 'BAIXA':1440})
        fields = {
            'sla_urgente': {'label': 'SLA URGENTE (min)', 'default': str(sla_map.get('URGENTE',120)), 'max_length': 6},
            'sla_normal': {'label': 'SLA NORMAL (min)', 'default': str(sla_map.get('NORMAL',720)), 'max_length': 6},
            'sla_baixa': {'label': 'SLA BAIXA (min)', 'default': str(sla_map.get('BAIXA',1440)), 'max_length': 6},
            'alert_roles': {'label': 'IDs cargos alerta (vírgula)', 'default': ','.join([str(r) for r in cfg.get('sla_alert_role_ids', [])]), 'required': False, 'max_length': 200},
            'escalation_roles': {'label': 'IDs cargos escalonamento', 'default': ','.join([str(r) for r in cfg.get('escalation_role_ids', [])]), 'required': False, 'max_length': 200}
        }
        async def _submit(inter: discord.Interaction, data: Dict[str, Any]):
            new_map = {}
            for k, label in (('sla_urgente','URGENTE'), ('sla_normal','NORMAL'), ('sla_baixa','BAIXA')):
                try:
                    val = int(data[k])
                    if val > 0: new_map[label] = val
                except: pass
            alert_ids = []
            for part in data['alert_roles'].split(','):
                part = part.strip()
                if part:
                    try: alert_ids.append(int(part))
                    except: pass
            esc_ids = []
            for part in data['escalation_roles'].split(','):
                part = part.strip()
                if part:
                    try: esc_ids.append(int(part))
                    except: pass
            self.panel.update_config({'sla_by_priority': new_map, 'sla_alert_role_ids': alert_ids, 'escalation_role_ids': esc_ids})
            await self.panel.send_success(inter, 'SLA por prioridade atualizado.')
            await self.panel.refresh(inter)
        await interaction.response.send_modal(EditTextModal('Configurar SLA Prioridades', fields, _submit))

class ToggleAutoCloseButton(Button):
    def __init__(self, panel: TicketsPanel):
        enabled = panel.get_config().get('auto_close_enabled', False)
        super().__init__(label='Auto-Close' + (' On' if enabled else ' Off'), style=discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary, emoji='⏰', row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('auto_close_enabled', False)
        self.panel.update_config({'auto_close_enabled': new_state})
        await self.panel.send_success(interaction, f"Auto-close {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)

class ToggleSLAEnabledButton(Button):
    def __init__(self, panel: TicketsPanel):
        enabled = panel.get_config().get('sla_enabled', True)
        super().__init__(label='SLA' + (' On' if enabled else ' Off'), style=discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary, emoji='📈', row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        new_state = not cfg.get('sla_enabled', True)
        self.panel.update_config({'sla_enabled': new_state})
        await self.panel.send_success(interaction, f"SLA {'ativado' if new_state else 'desativado'}.")
        await self.panel.refresh(interaction)

class ViewStatsButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Estatísticas", style=discord.ButtonStyle.secondary, emoji="📊", row=2)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        guild = interaction.guild
        category_ids = cfg.get('category_ids') or ([] if not cfg.get('category_id') else [cfg.get('category_id')])
        stats = {}
        total_open = 0
        priority_counts = {}
        for cid in category_ids:
            cat = guild.get_channel(cid)
            if not isinstance(cat, discord.CategoryChannel):
                continue
            cat_open = 0
            for ch in cat.channels:
                if isinstance(ch, discord.TextChannel) and ch.topic and 'user:' in ch.topic:
                    cat_open += 1
                    total_open += 1
                    if 'priority:' in ch.topic:
                        try:
                            pr = ch.topic.split('priority:')[1].split()[0].upper()
                            priority_counts[pr] = priority_counts.get(pr,0)+1
                        except:
                            pass
            stats[cat.name] = cat_open
        # Tempo médio de criação (idade média)
        ages = []
        for cid in category_ids:
            cat = guild.get_channel(cid)
            if not isinstance(cat, discord.CategoryChannel):
                continue
            for ch in cat.channels:
                if isinstance(ch, discord.TextChannel) and ch.topic and 'user:' in ch.topic:
                    ages.append((discord.utils.utcnow() - ch.created_at).total_seconds()/60)
        avg_age = (sum(ages)/len(ages)) if ages else 0
        desc_lines = [f"Total abertos: {total_open}", f"Idade média (min): {avg_age:.1f}"]
        if priority_counts:
            desc_lines.append("Prioridades:")
            for pr, count in priority_counts.items():
                desc_lines.append(f"- {pr}: {count}")
        for cat_name, count in stats.items():
            desc_lines.append(f"{cat_name}: {count} aberto(s)")
        embed = discord.Embed(title="📊 Estatísticas de Tickets", description="\n".join(desc_lines), color=0x2F3136)
        embed = self.panel.config_manager.apply_style(guild.id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CloseTicketsButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Fechar", style=discord.ButtonStyle.secondary, emoji="❌", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        for item in self.panel.children:
            item.disabled = True
        embed = discord.Embed(description="✅ Painel de tickets fechado.", color=0x00FF00)
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.edit_message(embed=embed, view=self.panel)
        self.panel.stop()

class DeleteTicketsButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Apagar", style=discord.ButtonStyle.danger, emoji="🗑️", row=4)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        if getattr(interaction.message, 'flags', None) and interaction.message.flags.ephemeral:
            for item in self.panel.children:
                item.disabled = True
            embed = discord.Embed(description="✅ Painel fechado (efêmero).", color=0x00FF00)
            embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
            await interaction.response.edit_message(embed=embed, view=self.panel)
            self.panel.stop()
        else:
            await interaction.response.send_message("✅ Painel apagado!", ephemeral=True)
            await interaction.message.delete()
            self.panel.stop()

class BackTicketsButton(Button):
    def __init__(self, panel: TicketsPanel):
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

class PostPanelMessageButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Postar Painel", style=discord.ButtonStyle.primary, emoji="📨", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        cfg = self.panel.get_config()
        channel_id = cfg.get('panel_channel_id')
        if not channel_id:
            await self.panel.send_error(interaction, 'Defina o canal do painel primeiro.')
            return
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await self.panel.send_error(interaction, 'Canal inválido.')
            return
        embed = discord.Embed(
            title=cfg.get('panel_title', '🎫 Suporte - Abra um Ticket'),
            description=cfg.get('panel_description', 'Clique no botão abaixo para abrir um ticket de suporte.'),
            color=cfg.get('panel_color', 0x5865F2)
        )
        embed = self.panel.config_manager.apply_style(interaction.guild.id, embed)
        class OpenTicketView(discord.ui.View):
            def __init__(self, cm):
                super().__init__(timeout=None)
                self.add_item(OpenTicketButton(cm))
        try:
            await channel.send(embed=embed, view=OpenTicketView(self.panel.config_manager))
        except discord.Forbidden:
            await self.panel.send_error(interaction, 'Sem permissão para enviar no canal.')
            return
        await self.panel.send_success(interaction, 'Painel de tickets publicado.')

class OpenTicketButton(discord.ui.Button):
    def __init__(self, config_manager):
        super().__init__(label='Abrir Ticket', style=discord.ButtonStyle.success, emoji='🎫', custom_id='open_ticket_btn')
        self.config_manager = config_manager
    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        cfg = self.config_manager.get_guild_config(guild.id, 'tickets')
        if not cfg.get('enabled'):
            await interaction.response.send_message('❌ Sistema de tickets desativado.', ephemeral=True)
            return
        # Limite por usuário
        user_open = 0
        # Contar em todas categorias configuradas ou categoria única
        categories_to_scan = []
        if cfg.get('category_ids'):
            for cid in cfg.get('category_ids'):
                cat = guild.get_channel(cid)
                if isinstance(cat, discord.CategoryChannel):
                    categories_to_scan.append(cat)
        else:
            cat_single = guild.get_channel(cfg.get('category_id')) if cfg.get('category_id') else None
            if isinstance(cat_single, discord.CategoryChannel):
                categories_to_scan.append(cat_single)
        for cat in categories_to_scan:
            for ch in cat.channels:
                if ch.topic and f'user:{interaction.user.id}' in ch.topic:
                    user_open += 1
        max_open = cfg.get('max_open_per_user', 3)
        if user_open >= max_open:
            await interaction.response.send_message(f'❌ Você já possui {user_open} tickets abertos (limite {max_open}).', ephemeral=True)
            return
        counter = cfg.get('ticket_counter', 0) + 1
        # Contador por categoria (multi suporte)
        cat_counters = cfg.get('category_counters', {})
        target_for_counter = None
        if cfg.get('category_ids'):
            # Será selecionada depois, incrementaremos após seleção real
            pass
        else:
            target_for_counter = cfg.get('category_id')
        # Atualização provisória global
        cfg['ticket_counter'] = counter
        self.config_manager.update_guild_config(guild.id, 'tickets', {'ticket_counter': counter})
        name = f'ticket-{counter}'
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False)}
        for rid in cfg.get('support_role_ids', []):
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        overwrites[interaction.user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        # Seleção de categoria se múltiplas
        target_category = None
        if cfg.get('category_ids'):
            class CategorySelect(discord.ui.Select):
                def __init__(self, cats):
                    options = [discord.SelectOption(label=guild.get_channel(cid).name[:100], value=str(cid)) for cid in cats if guild.get_channel(cid)]
                    super().__init__(placeholder='Selecione categoria do ticket', min_values=1, max_values=1, options=options)
                async def callback(self, inter: discord.Interaction):
                    nonlocal target_category
                    cid = int(self.values[0])
                    target_category = guild.get_channel(cid)
                    # Incrementar contador específico da categoria
                    nonlocal counter, cat_counters
                    cat_counters = cfg.get('category_counters', {})
                    prev = cat_counters.get(str(cid), 0) + 1
                    cat_counters[str(cid)] = prev
                    self.view.stop()
                    self.view.stop()
                    await inter.response.send_message('Categoria selecionada.', ephemeral=True)
            view = discord.ui.View(timeout=60)
            view.add_item(CategorySelect(cfg.get('category_ids')))
            await interaction.response.send_message('Escolha a categoria para o ticket.', view=view, ephemeral=True)
            await view.wait()
            if not target_category:
                return
        else:
            target_category = guild.get_channel(cfg.get('category_id')) if cfg.get('category_id') else None
        if not isinstance(target_category, discord.CategoryChannel):
            await interaction.followup.send('❌ Nenhuma categoria válida configurada.', ephemeral=True)
            return
        # Template de nome
        name_template = cfg.get('ticket_name_template', 'ticket-{counter}')
        # Se contador por categoria disponível usar esse valor
        if target_category:
            cat_counters = cfg.get('category_counters', cat_counters if 'cat_counters' in locals() else {})
            cat_count_val = cat_counters.get(str(target_category.id), counter)
            # Salvar counters atualizados
            self.config_manager.update_guild_config(guild.id, 'tickets', {'category_counters': cat_counters})
        else:
            cat_count_val = counter
        name = name_template.replace('{counter}', str(cat_count_val)).replace('{user}', interaction.user.name[:10]).replace('{category}', target_category.name[:10] if target_category else 'na')
        # Verificar formulário inicial
        initial_subject = None
        initial_description = None
        if cfg.get('require_initial_form'):
            class InitialFormModal(discord.ui.Modal, title=cfg.get('initial_form_subject_label', 'Assunto')):
                subject = discord.ui.TextInput(label=cfg.get('initial_form_subject_label','Assunto'), max_length=100, required=True)
                desc = discord.ui.TextInput(label=cfg.get('initial_form_description_label','Descrição'), style=discord.TextStyle.paragraph, max_length=1000, required=True)
                async def on_submit(self, inter: discord.Interaction):
                    nonlocal initial_subject, initial_description
                    initial_subject = self.subject.value
                    initial_description = self.desc.value
                    await inter.response.send_message('Processando...', ephemeral=True)
            modal = InitialFormModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            if not initial_subject:
                return
        # Prioridade
        priority_selected = None
        if cfg.get('enable_priority'):
            class PrioritySelect(discord.ui.Select):
                def __init__(self, priorities):
                    options = [discord.SelectOption(label=p, value=str(i)) for i,p in enumerate(priorities)]
                    super().__init__(placeholder='Selecione prioridade', options=options, min_values=1, max_values=1)
                async def callback(self, inter: discord.Interaction):
                    nonlocal priority_selected
                    priority_selected = cfg.get('priorities', [])[int(self.values[0])]
                    await inter.response.send_message(f'Prioridade: {priority_selected}', ephemeral=True)
                    self.view.stop()
            view_priority = discord.ui.View(timeout=60)
            view_priority.add_item(PrioritySelect(cfg.get('priorities', ['🟡 Normal'])))
            if not cfg.get('require_initial_form'):
                await interaction.response.send_message('Escolha a prioridade do ticket.', view=view_priority, ephemeral=True)
            else:
                await interaction.followup.send('Escolha a prioridade do ticket.', view=view_priority, ephemeral=True)
            await view_priority.wait()
        topic = f'user:{interaction.user.id}'
        if priority_selected:
            topic += f' priority:{priority_selected}'
        channel = await guild.create_text_channel(name, category=target_category, overwrites=overwrites, topic=topic)
        opener_desc = cfg.get('ticket_open_description', 'Explique seu problema. Um membro da equipe responderá em breve.')
        if initial_subject:
            opener_desc = f"**Assunto:** {initial_subject}\n\n{initial_description}"
        opener_embed = discord.Embed(title=cfg.get('ticket_open_title', '🎫 Ticket Criado'), description=opener_desc, color=cfg.get('panel_color', 0x5865F2))
        opener_embed = self.config_manager.apply_style(guild.id, opener_embed)
        if priority_selected:
            opener_embed.add_field(name='Prioridade', value=priority_selected, inline=False)
        class TicketControlView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(ClaimTicketButton())
                self.add_item(CloseTicketButton(self.config_manager))
        await channel.send(content=interaction.user.mention, embed=opener_embed, view=TicketControlView())
        if not cfg.get('require_initial_form') and not cfg.get('enable_priority'):
            await interaction.response.send_message(f'✅ Ticket criado: {channel.mention}', ephemeral=True)
        else:
            await interaction.followup.send(f'✅ Ticket criado: {channel.mention}', ephemeral=True)

class ClaimTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Claim', style=discord.ButtonStyle.primary, emoji='🙋')
    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not channel or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message('❌ Canal inválido.', ephemeral=True)
            return
        # Marca claim no topic
        if channel.topic and 'claimed:' in channel.topic:
            await interaction.response.send_message('⚠️ Ticket já possui claim.', ephemeral=True)
            return
        new_topic = (channel.topic or '') + f' claimed:{interaction.user.id}'
        try:
            await channel.edit(topic=new_topic)
        except Exception:
            pass
        await interaction.response.send_message(f'✅ Você assumiu este ticket.', ephemeral=True)
        try:
            await channel.send(f'👤 Ticket agora sendo atendido por {interaction.user.mention}.')
        except Exception:
            pass

class CloseTicketButton(discord.ui.Button):
    def __init__(self, config_manager):
        super().__init__(label='Fechar', style=discord.ButtonStyle.danger, emoji='🔒')
        self.config_manager = config_manager
    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        cfg = self.config_manager.get_guild_config(interaction.guild.id, 'tickets')
        if not cfg.get('enabled'):
            await interaction.response.send_message('❌ Sistema de tickets desativado.', ephemeral=True)
            return
        # Verificar claim obrigatório
        if cfg.get('claim_required'):
            if not channel.topic or 'claimed:' not in channel.topic:
                await interaction.response.send_message('❌ Este ticket precisa ser assumido (claim) antes de fechar.', ephemeral=True)
                return
        # Transcript
        transcript_url = None
        if cfg.get('transcript_enabled'):
            all_messages = []
            async for msg in channel.history(limit=1000, oldest_first=True):
                created = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                content = (msg.content or '').replace('\n', '<br>')
                all_messages.append(f"<div><b>{msg.author.display_name}</b> <span style='color:gray'>[{created}]</span><br>{content}</div>")
            # Chunk em partes de 300 para evitar embeds gigantes
            from pathlib import Path
            transcripts_dir = Path('transcripts')
            transcripts_dir.mkdir(exist_ok=True)
            chunk_size = 300
            files = []
            for i in range(0, len(all_messages), chunk_size):
                chunk = all_messages[i:i+chunk_size]
                html = "<html><body><h2>Transcript Ticket</h2>" + "\n".join(chunk) + "</body></html>"
                disk_path = transcripts_dir / f"transcript_{channel.name}_part{i//chunk_size+1}.html"
                try:
                    disk_path.write_text(html, encoding='utf-8')
                except Exception:
                    pass
                files.append(discord.File(fp=html.encode('utf-8'), filename=disk_path.name))
            file = files[0] if files else None
        else:
            file = None
        opener_id = None
        if channel.topic and 'user:' in channel.topic:
            try:
                opener_id = int(channel.topic.split('user:')[1].split()[0])
            except Exception:
                pass
        # Feedback
        if cfg.get('feedback_enabled') and opener_id:
            member = interaction.guild.get_member(opener_id)
            if member:
                class FeedbackView(discord.ui.View):
                    def __init__(self, cm, guild_id, opener):
                        super().__init__(timeout=300)
                        self.cm = cm
                        self.gid = guild_id
                        self.opener = opener
                        for i in range(1,6):
                            self.add_item(FeedbackButton(i, cm, guild_id, opener_id))
                class FeedbackButton(discord.ui.Button):
                    def __init__(self, rating, cm, gid, uid):
                        super().__init__(label=str(rating), style=discord.ButtonStyle.secondary)
                        self.rating = rating
                        self.cm = cm
                        self.gid = gid
                        self.uid = uid
                    async def callback(self, inter: discord.Interaction):
                        t_cfg = self.cm.get_guild_config(self.gid, 'tickets')
                        fb = t_cfg.get('feedback_store', {})
                        fb[str(self.uid)] = self.rating
                        self.cm.update_guild_config(self.gid, 'tickets', {'feedback_store': fb})
                        await inter.response.send_message(f'✅ Feedback registrado: {self.rating} estrela(s). Obrigado!', ephemeral=True)
                        self.view.stop()
                try:
                    await member.send(embed=self.config_manager.apply_style(interaction.guild.id, discord.Embed(title='⭐ Avaliação', description='Avalie seu atendimento (1-5):', color=0xFFD700)), view=FeedbackView(self.config_manager, interaction.guild.id, member))
                except Exception:
                    pass
        try:
            await interaction.response.send_message('🔒 Fechando ticket...', ephemeral=True)
        except Exception:
            pass
        try:
            if file:
                await channel.send(content='🧾 Transcript gerado (parte 1).', file=file)
                # Enviar partes adicionais
                if cfg.get('transcript_enabled') and 'files' in locals() and len(files) > 1:
                    for extra in files[1:]:
                        await channel.send(file=extra)
            await channel.edit(name=channel.name + '-fechado')
        except Exception:
            pass
        try:
            await channel.send('Este ticket será arquivado em 10s.')
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=10))
        except Exception:
            pass
        try:
            await channel.delete(reason='Ticket fechado')
        except Exception:
            pass
        # Incrementar contador fechado
        closed = cfg.get('closed_counter', 0) + 1
        self.config_manager.update_guild_config(interaction.guild.id, 'tickets', {'closed_counter': closed})

class ManualTicketsButton(Button):
    def __init__(self, panel: TicketsPanel):
        super().__init__(label="Manual", style=discord.ButtonStyle.success, emoji="📖", row=0)
        self.panel = panel
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Manual do Sistema de Tickets",
            description=(
                "**Guia completo de configuração do painel de tickets profissional.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="🚀 Passo 1: Configuração Básica",
            value=(
                "1️⃣ **Canal do Painel**: Defina onde aparecerá o botão 'Abrir Ticket'\n"
                "2️⃣ **Categoria**: Escolha a categoria onde os tickets serão criados\n"
                "3️⃣ **Cargos Suporte**: Adicione cargos que terão acesso aos tickets\n"
                "4️⃣ **Ativar Sistema**: Clique no botão verde para ativar\n"
                "5️⃣ **Postar Painel**: Publique o painel no canal escolhido"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Passo 2: Recursos Funcionais",
            value=(
                "🙋 **Claim**: Staff pode reivindicar tickets\n"
                "⭐ **Feedback**: Pedir avaliação ao fechar ticket\n"
                "🧾 **Transcrição**: Salvar histórico do ticket em arquivo\n"
                "✏️ **Mensagens**: Personalizar textos de abertura/fechamento\n"
                "🖼️ **Embed**: Customizar visual dos tickets"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Passo 3: Funcionalidades Avançadas",
            value=(
                "🏷️ **Template Nome**: Ex: `ticket-{user}-{number}`\n"
                "📝 **Formulário Inicial**: Coletar informações ao abrir\n"
                "🚦 **Prioridades**: Baixa/Média/Alta/Urgente\n"
                "⏱️ **SLA**: Tempo máximo de resposta\n"
                "📊 **Estatísticas**: Ver métricas de tickets"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📂 Multi Categorias",
            value=(
                "Configure múltiplas categorias para organizar tickets por tipo:\n"
                "• Suporte Técnico\n"
                "• Vendas\n"
                "• Parcerias\n"
                "Membros escolhem a categoria ao abrir o ticket."
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏰ Auto-Close e Limites",
            value=(
                "**Limites**: Máximo de tickets abertos por usuário\n"
                "**Auto-Close**: Fechar tickets inativos automaticamente\n"
                "**SLA Toggle**: Ativar alertas de tempo de resposta"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Dica: Configure passo a passo para evitar erros. Teste antes de ativar!")
        embed = self.panel.config_manager.apply_style(self.panel.guild_id, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)
