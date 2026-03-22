# Bot Discord — Moderação e Economia

Bot completo de Discord com moderação, economia, níveis, sorteios e utilitários.
Desenvolvido por **MARKIZIN**.

---

## Instalação

### Requisitos

- Python 3.10 ou superior
- Conta no [Discord Developer Portal](https://discord.com/developers/applications)

### Passo 1 — Instalar

Dê **duplo-clique** no arquivo `instalar.bat`.
Ele instala tudo automaticamente e pede o token do bot.

### Passo 2 — Iniciar

Dê **duplo-clique** no arquivo `iniciar.bat`.

> Para instruções detalhadas, veja `COMO_INSTALAR.txt`.
> Para hospedagem na nuvem, veja `COMO_HOSPEDAR.txt`.

---

## Comandos

### Economia

| Comando | Descrição |
|---------|-----------|
| `/daily` | Coletar créditos diários |
| `/saldo` | Ver saldo |
| `/transferir` | Transferir créditos |
| `/top` | Ranking de saldos |
| `/trabalhar` | Trabalhar para ganhar créditos |
| `/roubar` | Tentar roubar créditos de outro membro |
| `/apostar coinflip` | Apostar cara ou coroa |
| `/apostar roleta` | Apostar na roleta |
| `/shop` | Ver loja de itens |
| `/buy` | Comprar item |
| `/inventory` | Ver inventário |

### Moderação

| Comando | Descrição |
|---------|-----------|
| `/kick` | Expulsar membro |
| `/ban` | Banir membro |
| `/warn` | Avisar membro |
| `/timeout` | Aplicar timeout |
| `/setlog` | Definir canal de logs |

### Níveis e XP

| Comando | Descrição |
|---------|-----------|
| `/rank` | Ver nível e XP |
| `/leaderboard` | Top 10 de XP |
| `/setlevel` | Definir nível (admin) |

### Sorteios

| Comando | Descrição |
|---------|-----------|
| `/sorteio criar` | Criar sorteio |
| `/sorteio reroll` | Re-sortear vencedores |
| `/sorteio listar` | Listar sorteios ativos |
| `/sorteio encerrar` | Encerrar manualmente |

### Utilitários

| Comando | Descrição |
|---------|-----------|
| `/sugestao` | Enviar sugestão para votação |
| `/enquete` | Criar enquete com opções |
| `/lembrete` | Criar lembrete |
| `/cargo-temp` | Dar cargo temporário |
| `/serverinfo` | Informações do servidor |
| `/userinfo` | Informações de membro |

### Configuração

| Comando | Descrição |
|---------|-----------|
| `/painel` | Painel de configuração completo |
| `/backup` | Criar backup |
| `/restore` | Restaurar backup |
| `/tema` | Mudar tema visual |
| `/permissoes` | Permissões por cargo |
| `/stats` | Estatísticas detalhadas |
| `/antiraid` | Proteção anti-raid |
| `/formulario` | Formulários customizáveis |

**Total: 39 comandos slash**

---

## Módulos

| Módulo | Descrição |
|--------|-----------|
| Boas-vindas | Mensagens de entrada e saída |
| Tickets | Suporte com categorias e SLA |
| Economia | Créditos, loja, apostas, trabalho |
| Moderação | Ban, kick, warn, auto-mod |
| Logs | Registro por categoria |
| Autorole | Cargos por reação |
| Embeds | Estilo visual global |
| Níveis/XP | Sistema de XP e cargos por nível |
| Sorteios | Giveaways com timer e requisitos |
| Utilitários | Sugestões, starboard, enquetes |
| Backup | Backup automático e manual |
| Temas | 5 temas visuais |
| Permissões | Controle de acesso por cargo |
| Import/Export | Compartilhar configurações entre servidores |
| Estatísticas | Tracking de uso |
| Anti-Raid | Proteção contra raids |
| Formulários | Formulários customizáveis |

---

## Estrutura

```
instalar.bat            Instalador automático
iniciar.bat             Iniciar o bot
bot.py                  Arquivo principal
requirements.txt        Dependências
.env.example            Modelo de configuração
COMO_INSTALAR.txt       Guia de instalação
COMO_HOSPEDAR.txt       Guia de hospedagem
squarecloud.app         Configuração para SquareCloud
Procfile                Configuração para Railway/Render
runtime.txt             Versão do Python
modules/
  panel_system.py       Core do sistema de painéis
  panel_command.py      Comando /painel
  panel_tickets.py      Sistema de tickets
  panel_welcome.py      Boas-vindas
  panel_modules.py      Economia e Moderação
  panel_autorole.py     Cargos por reação
  panel_embeds.py       Estilo de embeds
  panel_emojis.py       Emojis customizados
  panel_logs.py         Sistema de logs
  panel_leveling.py     Configuração de níveis
  panel_utilities.py    Configuração de utilitários
  components_v2.py      Infraestrutura Components V2
  leveling_system.py    Sistema de XP
  giveaway_system.py    Sistema de sorteios
  utilities_system.py   Utilitários
  backup_system.py      Backup/restore
  themes.py             Temas visuais
  permissions.py        Permissões por cargo
  import_export.py      Import/export
  stats_system.py       Estatísticas
  antiraid_system.py    Anti-raid
  form_system.py        Formulários
```

---

## Hospedagem

O bot pode rodar no seu computador ou na nuvem.

- **Local**: Use `instalar.bat` e `iniciar.bat`
- **SquareCloud**: Zipar tudo e fazer upload (configuração incluída)
- **Railway/Render**: Conectar repositório (Procfile incluído)
- **VPS Linux**: Instruções no `COMO_HOSPEDAR.txt`

---

## Proteção de Autoria

Este bot possui sistema de proteção multicamadas v2.0.
Modificações não autorizadas causam encerramento automático.

---

**Desenvolvido por MARKIZIN**
Perfil: https://ggmax.com.br/perfil/markizin002

Desenvolvido com discord.py 2.7.1 | Components V2
