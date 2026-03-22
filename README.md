# Bot Discord — Moderacao e Economia

Bot completo de Discord com moderacao, economia, niveis, sorteios e utilitarios.
Desenvolvido por **MARKIZIN**.

---

## Instalacao

### Requisitos

- Python 3.10 ou superior
- Conta no [Discord Developer Portal](https://discord.com/developers/applications)

### Passo 1 — Instalar

De **duplo-clique** no arquivo `instalar.bat`.
Ele instala tudo automaticamente e pede o token do bot.

### Passo 2 — Iniciar

De **duplo-clique** no arquivo `iniciar.bat`.

> Para instrucoes detalhadas, veja `COMO_INSTALAR.txt`.
> Para hospedagem na nuvem, veja `COMO_HOSPEDAR.txt`.

---

## Comandos

### Economia

| Comando | Descricao |
|---------|-----------|
| `/daily` | Coletar creditos diarios |
| `/saldo` | Ver saldo |
| `/transferir` | Transferir creditos |
| `/top` | Ranking de saldos |
| `/trabalhar` | Trabalhar para ganhar creditos |
| `/roubar` | Tentar roubar creditos de outro membro |
| `/apostar coinflip` | Apostar cara ou coroa |
| `/apostar roleta` | Apostar na roleta |
| `/shop` | Ver loja de itens |
| `/buy` | Comprar item |
| `/inventory` | Ver inventario |

### Moderacao

| Comando | Descricao |
|---------|-----------|
| `/kick` | Expulsar membro |
| `/ban` | Banir membro |
| `/warn` | Avisar membro |
| `/timeout` | Aplicar timeout |
| `/setlog` | Definir canal de logs |

### Niveis e XP

| Comando | Descricao |
|---------|-----------|
| `/rank` | Ver nivel e XP |
| `/leaderboard` | Top 10 de XP |
| `/setlevel` | Definir nivel (admin) |

### Sorteios

| Comando | Descricao |
|---------|-----------|
| `/sorteio criar` | Criar sorteio |
| `/sorteio reroll` | Re-sortear vencedores |
| `/sorteio listar` | Listar sorteios ativos |
| `/sorteio encerrar` | Encerrar manualmente |

### Utilitarios

| Comando | Descricao |
|---------|-----------|
| `/sugestao` | Enviar sugestao para votacao |
| `/enquete` | Criar enquete com opcoes |
| `/lembrete` | Criar lembrete |
| `/cargo-temp` | Dar cargo temporario |
| `/serverinfo` | Info do servidor |
| `/userinfo` | Info de membro |

### Configuracao

| Comando | Descricao |
|---------|-----------|
| `/painel` | Painel de configuracao completo |
| `/backup` | Criar backup |
| `/restore` | Restaurar backup |
| `/tema` | Mudar tema visual |
| `/permissoes` | Permissoes por cargo |
| `/stats` | Estatisticas detalhadas |
| `/antiraid` | Protecao anti-raid |
| `/formulario` | Formularios customizados |

**Total: 39 comandos slash**

---

## Modulos

| Modulo | Descricao |
|--------|-----------|
| Boas-vindas | Mensagens de entrada e saida |
| Tickets | Suporte com categorias e SLA |
| Economia | Creditos, loja, apostas, trabalho |
| Moderacao | Ban, kick, warn, auto-mod |
| Logs | Registro por categoria |
| Autorole | Cargos por reacao |
| Embeds | Estilo visual global |
| Niveis/XP | Sistema de XP e cargos por nivel |
| Sorteios | Giveaways com timer e requisitos |
| Utilitarios | Sugestoes, starboard, enquetes |
| Backup | Backup automatico e manual |
| Temas | 5 temas visuais |
| Permissoes | Controle de acesso por cargo |
| Import/Export | Compartilhar configs entre servidores |
| Estatisticas | Tracking de uso |
| Anti-Raid | Protecao contra raids |
| Formularios | Formularios customizaveis |

---

## Estrutura

```
instalar.bat            Instalador automatico
iniciar.bat             Iniciar o bot
bot.py                  Arquivo principal
requirements.txt        Dependencias
.env.example            Modelo de configuracao
COMO_INSTALAR.txt       Guia de instalacao
COMO_HOSPEDAR.txt       Guia de hospedagem
squarecloud.app         Config para SquareCloud
Procfile                Config para Railway/Render
runtime.txt             Versao do Python
modules/
  panel_system.py       Core do sistema de paineis
  panel_command.py      Comando /painel
  panel_tickets.py      Sistema de tickets
  panel_welcome.py      Boas-vindas
  panel_modules.py      Economia e Moderacao
  panel_autorole.py     Cargos por reacao
  panel_embeds.py       Estilo de embeds
  panel_emojis.py       Emojis customizados
  panel_logs.py         Sistema de logs
  panel_leveling.py     Config de niveis
  panel_utilities.py    Config de utilitarios
  components_v2.py      Infraestrutura Components V2
  leveling_system.py    Sistema de XP
  giveaway_system.py    Sistema de sorteios
  utilities_system.py   Utilitarios
  backup_system.py      Backup/restore
  themes.py             Temas visuais
  permissions.py        Permissoes por cargo
  import_export.py      Import/export
  stats_system.py       Estatisticas
  antiraid_system.py    Anti-raid
  form_system.py        Formularios
```

---

## Hospedagem

O bot pode rodar no seu computador ou na nuvem.

- **Local**: Use `instalar.bat` e `iniciar.bat`
- **SquareCloud**: Zipar tudo e fazer upload (config inclusa)
- **Railway/Render**: Conectar repositorio (Procfile incluso)
- **VPS Linux**: Instrucoes no `COMO_HOSPEDAR.txt`

---

## Protecao de Autoria

Este bot possui sistema de protecao multicamadas v2.0.
Modificacoes nao autorizadas causam encerramento automatico.

---

**Desenvolvido por MARKIZIN**
Perfil: https://ggmax.com.br/perfil/markizin002

Desenvolvido com discord.py 2.7.1 | Components V2
