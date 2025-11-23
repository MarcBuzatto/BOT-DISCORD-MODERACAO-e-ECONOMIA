# BOT DISCORD - MODERAÇÃO + ECONOMIA

Bot completo de Discord com sistemas de moderação e economia desenvolvido por **MARKIZIN**.

## 🎯 Funcionalidades

### 📦 Sistemas Principais
- **Sistema de Painéis**: Configuração completa via interface interativa
- **Economia**: Sistema completo de moedas, trabalho, loja e apostas
- **Moderação**: Avisos, timeouts, bans e sistema de logs
- **Tickets**: Sistema de suporte com categorias personalizáveis
- **Boas-vindas**: Mensagens customizáveis com placeholders
- **Anti-Raid**: Proteção contra raids com múltiplos níveis

### 🎨 Sistemas Adicionais
- **Backup/Restore**: Backup automático e manual de configurações
- **Temas**: 5 temas pré-configurados + temas customizados
- **Permissões**: Sistema de permissões por cargo
- **Import/Export**: Importação/exportação de configurações
- **Estatísticas**: Tracking de uso de comandos e atividades
- **Formulários**: Sistema de formulários customizáveis

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Token de bot do Discord
- Permissões necessárias no servidor

## 🚀 Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/MarcBuzatto/BOT-DISCORD---MODERA-O-ECONOMIA.git
cd "BOT DISCORD - MODERAÇÃO + ECONOMIA"
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure o arquivo .env**
```env
DISCORD_TOKEN=seu_token_aqui
```

4. **Execute o bot**
```bash
python bot.py
```

## 📝 Comandos Principais

- `/painel` - Abre o painel de configuração completo
- `/saldo` - Verifica seu saldo
- `/trabalhar` - Trabalha para ganhar moedas
- `/loja` - Abre a loja de itens
- `/ticket` - Abre um ticket de suporte
- `/avisar` - Avisa um usuário (moderação)

**Total: 26 comandos slash**

## 🛡️ Proteção de Autoria

Este bot possui sistema de proteção multicamadas (v2.0):
- ✅ Verificação de integridade em múltiplas camadas
- ✅ Monitoramento contínuo em background
- ✅ Ofuscação de dados sensíveis
- ⚠️ Modificações não autorizadas causarão encerramento do bot

## 📦 Estrutura de Arquivos

```
├── bot.py                  # Arquivo principal
├── requirements.txt        # Dependências
├── COMO_INSTALAR.txt      # Guia de instalação detalhado
├── .env                    # Configurações (não versionado)
├── panel_config.json       # Configurações dos painéis
└── modules/                # Módulos do bot
    ├── panel_*.py         # Sistema de painéis
    ├── backup_system.py   # Sistema de backup
    ├── themes.py          # Sistema de temas
    ├── permissions.py     # Sistema de permissões
    ├── import_export.py   # Import/Export
    ├── stats_system.py    # Estatísticas
    ├── antiraid_system.py # Anti-Raid
    └── form_system.py     # Formulários
```

## 👤 Desenvolvedor

**MARKIZIN**
- 🔗 Perfil: https://ggmax.com.br/perfil/markizin002
- 📧 Contato: Disponível no perfil

## 📄 Licença

Este bot é proprietário. Uso comercial não autorizado é proibido.

---

⚡ Desenvolvido com Discord.py 2.3.2
