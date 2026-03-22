"""
Infraestrutura Components V2 - Helpers para criar layouts modernos
Desenvolvido por: MARKIZIN
https://ggmax.com.br/perfil/markizin002

PROTECAO DE AUTORIA - NAO REMOVER
"""
import discord
from discord import ui
import hashlib
from datetime import datetime, timezone

# PROTECAO DE AUTORIA - NAO REMOVER
_AUTHOR_CHECK = hashlib.md5(b"MARKIZIN").hexdigest()
_AUTHOR_NAME = "MARKIZIN"
_AUTHOR_URL = "https://ggmax.com.br/perfil/markizin002"
_AUTHOR_FOOTER = f"Desenvolvido por {_AUTHOR_NAME}"

if _AUTHOR_CHECK != "7e94cd9fff4a493ba6b9b2abcc38f3c0":
    raise RuntimeError("Falha na verificacao de integridade autoral")


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BrandedView(ui.LayoutView):
    """Base para todas as views Components V2 do bot.
    Inclui automaticamente o footer autoral MARKIZIN.
    Remover a marca causa falha de integridade.
    """

    def __init__(self, *, timeout=120, author_id=None):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author_id and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Somente quem abriu este painel pode interagir.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.walk_children():
            if isinstance(item, ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


def brand_footer():
    """Retorna o componente de footer autoral. NAO REMOVER."""
    return ui.TextDisplay(f"-# {_AUTHOR_FOOTER}")


def author_button():
    """Retorna o botao link para o perfil do autor. NAO REMOVER."""
    return ui.Button(label=_AUTHOR_NAME, url=_AUTHOR_URL, style=discord.ButtonStyle.link)


def make_card(
    title: str,
    description: str,
    color: int | discord.Color = 0x5865F2,
    fields: list[tuple[str, str]] | None = None,
    thumbnail_url: str | None = None,
    author_id: int | None = None,
    timeout: float = 120,
    buttons: list[ui.Button] | None = None,
) -> BrandedView:
    """Cria um card Components V2 completo e estilizado."""
    view = BrandedView(timeout=timeout, author_id=author_id)

    inner_components = []

    section_texts = [f"## {title}", description]

    if thumbnail_url:
        section = ui.Section(
            *section_texts,
            accessory=ui.Thumbnail(thumbnail_url),
        )
        inner_components.append(section)
    else:
        inner_components.append(ui.TextDisplay(f"## {title}"))
        if description:
            inner_components.append(ui.TextDisplay(description))

    if fields:
        inner_components.append(ui.Separator(visible=True))
        field_lines = []
        for name, value in fields:
            field_lines.append(f"**{name}:** {value}")
        inner_components.append(ui.TextDisplay("\n".join(field_lines)))

    if isinstance(color, int):
        color = discord.Color(color)
    container = ui.Container(*inner_components, accent_colour=color)
    view.add_item(container)

    if buttons:
        action_row = ui.ActionRow(*buttons)
        view.add_item(action_row)

    # PROTECAO: Footer autoral obrigatorio
    view.add_item(brand_footer())

    return view


def make_success(text: str, author_id: int | None = None) -> BrandedView:
    """Card de sucesso verde."""
    return make_card("Concluido", text, color=0x00FF00, author_id=author_id, timeout=30)


def make_error(text: str, author_id: int | None = None) -> BrandedView:
    """Card de erro vermelho."""
    return make_card("Erro", text, color=0xFF0000, author_id=author_id, timeout=30)


def make_info(title: str, text: str, author_id: int | None = None) -> BrandedView:
    """Card informativo azul."""
    return make_card(title, text, color=0x5865F2, author_id=author_id)
