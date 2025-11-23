"""
Sistema de Formulários Customizados
Desenvolvido por: MARKIZIN
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
from pathlib import Path

class FormSystem:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.responses_file = Path("form_responses.json")
        self.responses = self._load_responses()
    
    def _load_responses(self) -> dict:
        """Carrega respostas salvas."""
        if not self.responses_file.exists():
            return {}
        try:
            with open(self.responses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_responses(self):
        """Salva respostas."""
        try:
            with open(self.responses_file, 'w', encoding='utf-8') as f:
                json.dump(self.responses, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar respostas: {e}")
    
    def get_forms(self, guild_id: int) -> dict:
        """Retorna todos os formulários do servidor."""
        return self.config_manager.get_guild_config(guild_id, "forms")
    
    def get_form(self, guild_id: int, form_id: str) -> dict:
        """Retorna um formulário específico."""
        forms = self.get_forms(guild_id)
        return forms.get(form_id, {})
    
    def save_form(self, guild_id: int, form_id: str, form_data: dict):
        """Salva um formulário."""
        forms = self.get_forms(guild_id)
        forms[form_id] = form_data
        self.config_manager.update_guild_config(guild_id, "forms", forms)
    
    def delete_form(self, guild_id: int, form_id: str):
        """Deleta um formulário."""
        forms = self.get_forms(guild_id)
        if form_id in forms:
            del forms[form_id]
            self.config_manager.update_guild_config(guild_id, "forms", forms)
    
    def save_response(self, guild_id: int, form_id: str, user_id: int, responses: dict):
        """Salva resposta de um formulário."""
        guild_key = str(guild_id)
        if guild_key not in self.responses:
            self.responses[guild_key] = {}
        if form_id not in self.responses[guild_key]:
            self.responses[guild_key][form_id] = []
        
        self.responses[guild_key][form_id].append({
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "responses": responses
        })
        self._save_responses()
    
    def get_responses(self, guild_id: int, form_id: str) -> list:
        """Retorna respostas de um formulário."""
        guild_key = str(guild_id)
        return self.responses.get(guild_key, {}).get(form_id, [])

class FormModal(discord.ui.Modal):
    def __init__(self, form_system: FormSystem, guild_id: int, form_data: dict):
        super().__init__(title=form_data.get("title", "Formulário")[:45])
        self.form_system = form_system
        self.guild_id = guild_id
        self.form_data = form_data
        
        # Adicionar campos (máximo 5 por modal)
        for i, field in enumerate(form_data.get("fields", [])[:5]):
            text_input = discord.ui.TextInput(
                label=field["label"][:45],
                placeholder=field.get("placeholder", "")[:100],
                required=field.get("required", True),
                style=discord.TextStyle.paragraph if field.get("multiline", False) else discord.TextStyle.short,
                min_length=field.get("min_length", 1),
                max_length=field.get("max_length", 1000)
            )
            self.add_item(text_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Coletar respostas
        responses = {}
        fields = self.form_data.get("fields", [])[:5]
        for i, item in enumerate(self.children):
            if isinstance(item, discord.ui.TextInput):
                responses[fields[i]["label"]] = item.value
        
        # Salvar resposta
        self.form_system.save_response(
            self.guild_id,
            self.form_data["id"],
            interaction.user.id,
            responses
        )
        
        # Enviar confirmação
        embed = discord.Embed(
            title="✅ Formulário Enviado!",
            description="Sua resposta foi registrada com sucesso.",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Notificar canal se configurado
        response_channel_id = self.form_data.get("response_channel_id")
        if response_channel_id:
            channel = interaction.guild.get_channel(response_channel_id)
            if channel:
                result_embed = discord.Embed(
                    title=f"📋 Nova Resposta: {self.form_data.get('title')}",
                    description=f"Usuário: {interaction.user.mention}",
                    color=0x5865F2,
                    timestamp=datetime.now()
                )
                
                for label, value in responses.items():
                    result_embed.add_field(
                        name=label,
                        value=value[:1024],
                        inline=False
                    )
                
                try:
                    await channel.send(embed=result_embed)
                except:
                    pass

class FormBuilderModal(discord.ui.Modal, title="📝 Criar Formulário"):
    def __init__(self, form_system: FormSystem, guild_id: int):
        super().__init__()
        self.form_system = form_system
        self.guild_id = guild_id
        
        self.form_title = discord.ui.TextInput(
            label="Título do Formulário",
            placeholder="Ex: Aplicação para Staff",
            max_length=100,
            required=True
        )
        self.add_item(self.form_title)
        
        self.form_description = discord.ui.TextInput(
            label="Descrição",
            placeholder="Descreva o propósito do formulário",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False
        )
        self.add_item(self.form_description)
    
    async def on_submit(self, interaction: discord.Interaction):
        form_id = f"form_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        form_data = {
            "id": form_id,
            "title": self.form_title.value,
            "description": self.form_description.value,
            "fields": [],
            "created_by": interaction.user.id,
            "created_at": datetime.now().isoformat()
        }
        
        self.form_system.save_form(self.guild_id, form_id, form_data)
        
        embed = discord.Embed(
            title="✅ Formulário Criado!",
            description=f"**Título:** {self.form_title.value}\n\nAgora adicione campos ao formulário.",
            color=0x00FF00
        )
        
        view = FormEditorView(self.form_system, self.guild_id, form_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class AddFieldModal(discord.ui.Modal, title="➕ Adicionar Campo"):
    def __init__(self, form_system: FormSystem, guild_id: int, form_id: str):
        super().__init__()
        self.form_system = form_system
        self.guild_id = guild_id
        self.form_id = form_id
        
        self.field_label = discord.ui.TextInput(
            label="Nome do Campo",
            placeholder="Ex: Nome Completo, Idade, Experiência...",
            max_length=45,
            required=True
        )
        self.add_item(self.field_label)
        
        self.field_placeholder = discord.ui.TextInput(
            label="Placeholder (texto de exemplo)",
            placeholder="Ex: Digite seu nome completo...",
            max_length=100,
            required=False
        )
        self.add_item(self.field_placeholder)
        
        self.field_required = discord.ui.TextInput(
            label="Obrigatório? (sim/não)",
            placeholder="sim",
            max_length=3,
            default="sim",
            required=True
        )
        self.add_item(self.field_required)
        
        self.field_multiline = discord.ui.TextInput(
            label="Múltiplas linhas? (sim/não)",
            placeholder="não",
            max_length=3,
            default="não",
            required=True
        )
        self.add_item(self.field_multiline)
    
    async def on_submit(self, interaction: discord.Interaction):
        form_data = self.form_system.get_form(self.guild_id, self.form_id)
        
        if len(form_data.get("fields", [])) >= 5:
            await interaction.response.send_message(
                "❌ Limite de 5 campos atingido! (Limitação do Discord)",
                ephemeral=True
            )
            return
        
        field = {
            "label": self.field_label.value,
            "placeholder": self.field_placeholder.value,
            "required": self.field_required.value.lower() in ["sim", "s", "yes", "y"],
            "multiline": self.field_multiline.value.lower() in ["sim", "s", "yes", "y"],
            "min_length": 1,
            "max_length": 1000
        }
        
        if "fields" not in form_data:
            form_data["fields"] = []
        
        form_data["fields"].append(field)
        self.form_system.save_form(self.guild_id, self.form_id, form_data)
        
        embed = discord.Embed(
            title="✅ Campo Adicionado!",
            description=f"**Campo:** {field['label']}\n**Obrigatório:** {'Sim' if field['required'] else 'Não'}\n**Múltiplas linhas:** {'Sim' if field['multiline'] else 'Não'}",
            color=0x00FF00
        )
        
        view = FormEditorView(self.form_system, self.guild_id, self.form_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class FormEditorView(discord.ui.View):
    def __init__(self, form_system: FormSystem, guild_id: int, form_id: str):
        super().__init__(timeout=300)
        self.form_system = form_system
        self.guild_id = guild_id
        self.form_id = form_id
    
    @discord.ui.button(label="Adicionar Campo", style=discord.ButtonStyle.success, emoji="➕", row=0)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddFieldModal(self.form_system, self.guild_id, self.form_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Visualizar", style=discord.ButtonStyle.primary, emoji="👁️", row=0)
    async def preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        form_data = self.form_system.get_form(self.guild_id, self.form_id)
        
        embed = discord.Embed(
            title=f"📋 {form_data.get('title')}",
            description=form_data.get('description', 'Sem descrição'),
            color=0x5865F2
        )
        
        fields = form_data.get("fields", [])
        if fields:
            field_list = "\n".join([
                f"{i+1}. **{f['label']}** {'(obrigatório)' if f.get('required') else '(opcional)'}"
                for i, f in enumerate(fields)
            ])
        else:
            field_list = "Nenhum campo adicionado ainda"
        
        embed.add_field(
            name=f"Campos ({len(fields)}/5)",
            value=field_list,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Publicar", style=discord.ButtonStyle.primary, emoji="📤", row=0)
    async def publish(self, interaction: discord.Interaction, button: discord.ui.Button):
        form_data = self.form_system.get_form(self.guild_id, self.form_id)
        
        if not form_data.get("fields"):
            await interaction.response.send_message(
                "❌ Adicione pelo menos um campo antes de publicar!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"📋 {form_data.get('title')}",
            description=form_data.get('description', 'Clique no botão abaixo para preencher'),
            color=0x5865F2
        )
        
        view = FormPublicView(self.form_system, self.guild_id, form_data)
        
        await interaction.response.send_message(
            "Escolha o canal para publicar:",
            view=ChannelSelectViewForm(interaction, embed, view),
            ephemeral=True
        )
    
    @discord.ui.button(label="Canal de Respostas", style=discord.ButtonStyle.secondary, emoji="📬", row=1)
    async def response_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View(timeout=180)
        
        select = discord.ui.ChannelSelect(
            placeholder="Canal para receber respostas...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )
        
        async def select_callback(select_interaction: discord.Interaction):
            channel = select.values[0]
            form_data = self.form_system.get_form(self.guild_id, self.form_id)
            form_data["response_channel_id"] = channel.id
            self.form_system.save_form(self.guild_id, self.form_id, form_data)
            
            embed = discord.Embed(
                title="✅ Canal Configurado",
                description=f"Respostas serão enviadas para {channel.mention}",
                color=0x00FF00
            )
            
            await select_interaction.response.send_message(embed=embed, ephemeral=True)
        
        select.callback = select_callback
        view.add_item(select)
        
        await interaction.response.send_message("Selecione o canal:", view=view, ephemeral=True)
    
    @discord.ui.button(label="Ver Respostas", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def view_responses(self, interaction: discord.Interaction, button: discord.ui.Button):
        responses = self.form_system.get_responses(self.guild_id, self.form_id)
        
        if not responses:
            await interaction.response.send_message(
                "📭 Ainda não há respostas para este formulário.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"📊 Respostas ({len(responses)})",
            description=f"Total de respostas recebidas: **{len(responses)}**",
            color=0x5865F2
        )
        
        # Mostrar últimas 5 respostas
        for i, resp in enumerate(responses[-5:], 1):
            user_id = resp.get("user_id")
            timestamp = datetime.fromisoformat(resp.get("timestamp"))
            
            response_text = "\n".join([
                f"**{label}:** {value[:100]}"
                for label, value in resp.get("responses", {}).items()
            ])
            
            embed.add_field(
                name=f"{i}. <@{user_id}> - {timestamp.strftime('%d/%m/%Y %H:%M')}",
                value=response_text[:1024],
                inline=False
            )
        
        if len(responses) > 5:
            embed.set_footer(text=f"Mostrando últimas 5 de {len(responses)} respostas")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Deletar", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.form_system.delete_form(self.guild_id, self.form_id)
        
        embed = discord.Embed(
            title="✅ Formulário Deletado",
            description="O formulário foi removido.",
            color=0x00FF00
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.secondary, emoji="✖️", row=2)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

class ChannelSelectViewForm(discord.ui.View):
    def __init__(self, original_interaction: discord.Interaction, embed: discord.Embed, form_view: discord.ui.View):
        super().__init__(timeout=180)
        self.original_interaction = original_interaction
        self.embed = embed
        self.form_view = form_view
        # Guardar referência direta ao select para evitar depender de children[0]
        self.channel_select = discord.ui.ChannelSelect(
            placeholder="Selecione o canal...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )
        self.channel_select.callback = self._select_callback
        self.add_item(self.channel_select)
    
    async def _select_callback(self, interaction: discord.Interaction):
        # Usar referência direta ao select
        channel = self.channel_select.values[0]
        
        try:
            await channel.send(embed=self.embed, view=self.form_view)
            
            success_embed = discord.Embed(
                title="✅ Formulário Publicado!",
                description=f"O formulário foi publicado em {channel.mention}",
                color=0x00FF00
            )
            
            await interaction.response.edit_message(embed=success_embed, view=None)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para enviar mensagens nesse canal!",
                ephemeral=True
            )

class FormPublicView(discord.ui.View):
    def __init__(self, form_system: FormSystem, guild_id: int, form_data: dict):
        super().__init__(timeout=None)  # Permanente
        self.form_system = form_system
        self.guild_id = guild_id
        self.form_data = form_data
    
    @discord.ui.button(label="Preencher Formulário", style=discord.ButtonStyle.primary, emoji="📝", custom_id="fill_form")
    async def fill_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FormModal(self.form_system, self.guild_id, self.form_data)
        await interaction.response.send_modal(modal)

class FormListView(discord.ui.View):
    def __init__(self, guild: discord.Guild, form_system: FormSystem):
        super().__init__(timeout=180)
        self.guild = guild
        self.form_system = form_system
        
        forms = form_system.get_forms(guild.id)
        
        if forms:
            options = [
                discord.SelectOption(
                    label=form["title"][:100],
                    value=form_id,
                    description=f"{len(form.get('fields', []))} campos"
                )
                for form_id, form in list(forms.items())[:25]
            ]
            
            self.form_select = discord.ui.Select(
                placeholder="Selecione um formulário...",
                options=options,
                min_values=1,
                max_values=1
            )
            self.form_select.callback = self._select_callback
            self.add_item(self.form_select)
    
    async def _select_callback(self, interaction: discord.Interaction):
        form_id = self.form_select.values[0]
        view = FormEditorView(self.form_system, self.guild.id, form_id)
        
        form_data = self.form_system.get_form(self.guild.id, form_id)
        
        embed = discord.Embed(
            title=f"📋 Editando: {form_data.get('title')}",
            description="Use os botões abaixo para gerenciar o formulário.",
            color=0x5865F2
        )
        
        await interaction.response.edit_message(embed=embed, view=view)

class FormCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, form_system: FormSystem):
        self.bot = bot
        self.form_system = form_system
    
    @app_commands.command(name="formulario", description="Gerencia formulários customizados")
    @app_commands.checks.has_permissions(administrator=True)
    async def form_command(self, interaction: discord.Interaction):
        forms = self.form_system.get_forms(interaction.guild.id)
        
        embed = discord.Embed(
            title="📋 Gerenciador de Formulários",
            description=(
                "Crie formulários personalizados para aplicações, pesquisas, feedback e mais!\n\n"
                f"**Formulários ativos:** {len(forms)}"
            ),
            color=0x5865F2
        )
        
        embed.add_field(
            name="🎯 Casos de Uso",
            value="• Aplicações para Staff\n• Pesquisas de satisfação\n• Denúncias\n• Parcerias\n• Eventos",
            inline=True
        )
        
        embed.add_field(
            name="✨ Recursos",
            value="• Até 5 campos por formulário\n• Campos obrigatórios/opcionais\n• Respostas curtas ou longas\n• Notificações automáticas",
            inline=True
        )
        
        view = FormMainView(self.form_system, interaction.guild)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class FormMainView(discord.ui.View):
    def __init__(self, form_system: FormSystem, guild: discord.Guild):
        super().__init__(timeout=180)
        self.form_system = form_system
        self.guild = guild
    
    @discord.ui.button(label="Criar Novo", style=discord.ButtonStyle.success, emoji="➕", row=0)
    async def create_new(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FormBuilderModal(self.form_system, self.guild.id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Meus Formulários", style=discord.ButtonStyle.primary, emoji="📝", row=0)
    async def my_forms(self, interaction: discord.Interaction, button: discord.ui.Button):
        forms = self.form_system.get_forms(self.guild.id)
        
        if not forms:
            await interaction.response.send_message(
                "📭 Você ainda não criou nenhum formulário.\nUse **Criar Novo** para começar!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📋 Seus Formulários",
            description="Selecione um formulário para editar:",
            color=0x5865F2
        )
        
        view = FormListView(self.guild, self.form_system)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.secondary, emoji="✖️", row=0)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

async def setup(bot: commands.Bot, config_manager):
    """Configura o sistema de formulários."""
    form_system = FormSystem(config_manager)
    await bot.add_cog(FormCommands(bot, form_system))
    return form_system
