"""
Localization and Translation Management System.

Provides zero-overhead dictionary lookup translations for multi-language execution
environments. Supports English and Brazilian Portuguese out of the box with safe
structural fallbacks.
"""

from __future__ import annotations

from typing import Any

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "wizard_welcome": "[bold cyan]Welcome to the AI CLI setup wizard![/bold cyan]\nLet's configure your environment in a few quick steps.\n",
        "wizard_lang_select": "Choose your interface language / Escolha o idioma (en / pt_br)",
        "wizard_lang_invalid": "[bold red]Invalid selection.[/bold red] Defaulting to English.",
        "wizard_provider_name": "Enter provider name (e.g., OpenRouter, Gemini, OpenAI, Custom)",
        "wizard_url_prompt": "Enter provider API base URL",
        "wizard_key_prompt": "Enter your API key (input hidden)",
        "wizard_key_required": "[bold red]Error: API Key cannot be empty.[/bold red]",
        "wizard_fetch_models": "\n[yellow]Connecting to endpoint to fetch available models...[/yellow]",
        "wizard_fetch_success": "[bold green]Successfully retrieved available models from provider![/bold green]",
        "wizard_fetch_failed": "[bold yellow]Could not fetch models automatically ({error}). Using safe default.[/bold yellow]",
        "wizard_model_select": "Select a default model from the list above",
        "wizard_model_custom": "Enter a custom model identifier if your choice is not listed",
        "wizard_success": "\n[bold green]Configuration saved successfully![/bold green]\nYou can now launch the chat client using the launch command.\n",
        
        "author_note": "\n[dim]Note: Lightweight Study Chat CLI Built with Clean Architecture.[/dim]\n",
        "cli_welcome": "[bold blue]Chat Session Initialized[/bold blue] (Provider: [green]{provider}[/green] | Profile: [yellow]{profile}[/yellow] | Language: [yellow]{lang}[/yellow])\nType [bold cyan]/help[/bold cyan] to see available commands. Press [bold]Ctrl+D[/bold] or type [bold cyan]/exit[/bold cyan] to quit.\n",
        "cli_user_label": "\n[bold green]You[/bold green]",
        "cli_assistant_label": "[bold magenta]Assistant[/bold magenta]",
        "cli_stream_error": "\n[bold red]Stream interrupted by connection failure.[/bold red]",
        
        "cmd_help_header": "\n[bold underline]Available Session Commands:[/bold underline]",
        "cmd_help_exit": "Exit the application session cleanly.",
        "cmd_help_clear": "Reset conversational logs, starting a clean thread context.",
        "cmd_help_model": "Display the currently selected AI model or switch to a new one.",
        "cmd_help_profile": "Display or switch system prompt profiles dynamically.",
        "cmd_help_provider": "List, switch, add, or remove AI providers.",
        "cmd_help_refresh": "Force a manual update of cached provider models.",
        "cmd_help_setup": "Rerun the configuration wizard to rewrite keys and endpoints.",
        "cmd_help_help": "Show this command syntax mapping ledger.",
        
        "cmd_model_current": "\nActive model identifier: [bold green]{model}[/bold green]",
        "cmd_model_switch": "Enter new model identifier or name selection index: ",
        "cmd_model_success": "[bold green]Switched model to:[/bold green] {model}",
        "cmd_model_empty": "[bold yellow]Selection canceled. Model left unchanged.[/bold yellow]",
        "cmd_model_cache_empty": "[bold yellow]Model cache is currently empty. Run /refresh to discover models online.[/bold yellow]",
        
        "cmd_profile_current": "\nActive system profile: [bold green]{profile}[/bold green]",
        "cmd_profile_list": "Available prompt profiles: {profiles}",
        "cmd_profile_switch": "Enter profile name to activate: ",
        "cmd_profile_success": "[bold green]Switched system profile context to:[/bold green] {profile}",
        "cmd_profile_invalid": "[bold red]Error: Profile '{profile}' does not exist.[/bold red]",
        
        "cmd_provider_list_title": "\n[bold underline]Configured Providers[/bold underline]",
        "cmd_provider_list_tip": "\n[dim]Tip: Use '/provider switch <key>' to change active provider.[/dim]",
        "cmd_provider_switch_prompt": "Enter the provider key to switch to: ",
        "cmd_provider_already_active": "[yellow]Provider '{provider}' is already active.[/yellow]",
        "cmd_provider_switched": "[bold green]Switched active provider to: '{provider}'. Session context cleared.[/bold green]",
        "cmd_provider_not_found": "[bold red]Error: Provider key '{provider}' not found.[/bold red]",
        
        "cmd_refresh_start": "[yellow]Contacting provider to update cached model architecture listings...[/yellow]",
        "cmd_refresh_success": "[bold green]Model discovery listings refreshed and cached cleanly.[/bold green] Total unique entries: {count}",
        "cmd_clear_success": "[bold green]Conversation context wiped cleanly. Starting a brand new thread session.[/bold green]",
        "cmd_setup_start": "\n[yellow]Launching the configuration setup wizard...[/yellow]\n",
        "cmd_unknown": "[bold red]Unknown internal command structure.[/bold red] Type [bold cyan]/help[/bold cyan] to view commands.",
        
        "err_title": "An unexpected error occurred",
        "err_action_tip": "Actionable Tip",
        "err_network": "Network transport handshake failed. Verify internet routing paths and base URL configuration values.",
        "err_auth": "Authentication verification denied. Your registered API Key configuration details appear invalid or expired.",
        "err_http_status": "Provider endpoint responded with an invalid state code: HTTP {status}.",
        "err_config_corrupt": "Your target settings file is structurally corrupted. Please run setup again to overwrite entries securely.",
    },
    "pt_br": {
        "wizard_welcome": "[bold cyan]Bem-vindo ao assistente de configuração CLI![/bold cyan]\nVamos configurar seu ambiente em poucos passos rápidos.\n",
        "wizard_lang_select": "Choose your interface language / Escolha o idioma (en / pt_br)",
        "wizard_lang_invalid": "[bold red]Seleção inválida.[/bold red] Definindo padrão como Inglês.",
        "wizard_provider_name": "Insira o nome do provedor (ex: OpenRouter, Gemini, OpenAI, Custom)",
        "wizard_url_prompt": "Insira a URL base da API do provedor",
        "wizard_key_prompt": "Insira sua chave de API (entrada oculta)",
        "wizard_key_required": "[bold red]Erro: A chave de API não pode estar vazia.[/bold red]",
        "wizard_fetch_models": "\n[yellow]Conectando ao endpoint para buscar modelos disponíveis...[/yellow]",
        "wizard_fetch_success": "[bold green]Modelos disponíveis recuperados com sucesso do provedor![/bold green]",
        "wizard_fetch_failed": "[bold yellow]Não foi possível buscar modelos automaticamente ({error}). Usando padrão seguro.[/bold yellow]",
        "wizard_model_select": "Selecione um modelo padrão da lista acima",
        "wizard_model_custom": "Insira um identificador de modelo customizado caso não esteja listado",
        "wizard_success": "\n[bold green]Configuração salva com sucesso![/bold green]\nVocê já pode iniciar o cliente de chat usando o comando de execução.\n",
        
        "author_note": "\n[dim]Nota: Chat CLI acadêmico construído sob os princípios de Clean Architecture.[/dim]\n",
        "cli_welcome": "[bold blue]Sessão de Chat Inicializada[/bold blue] (Provedor: [green]{provider}[/green] | Perfil: [yellow]{profile}[/yellow] | Idioma: [yellow]{lang}[/yellow])\nDigite [bold cyan]/help[/bold cyan] para ver os comandos disponíveis. Pressione [bold]Ctrl+D[/bold] ou digite [bold cyan]/exit[/bold cyan] para sair.\n",
        "cli_user_label": "\n[bold green]Você[/bold green]",
        "cli_assistant_label": "[bold magenta]Assistente[/bold magenta]",
        "cli_stream_error": "\n[bold red]Fluxo interrompido por falha de conexão de rede.[/bold red]",
        
        "cmd_help_header": "\n[bold underline]Comandos de Sessão Disponíveis:[/bold underline]",
        "cmd_help_exit": "Encerra a sessão do aplicativo de forma limpa.",
        "cmd_help_clear": "Limpa os logs de conversação, reiniciando o contexto histórico do zero.",
        "cmd_help_model": "Exibe o modelo de IA selecionado ou altera para uma nova escolha.",
        "cmd_help_profile": "Exibe ou altera dinamicamente os perfis de instrução do sistema.",
        "cmd_help_provider": "Lista, altera, adiciona ou remove provedores de IA.",
        "cmd_help_refresh": "Força uma atualização manual do cache de modelos.",
        "cmd_help_setup": "Reexecuta o assistente de configuração.",
        "cmd_help_help": "Exibe esta listagem explicativa de sintaxe de comandos.",
        
        "cmd_model_current": "\nIdentificador do modelo ativo: [bold green]{model}[/bold green]",
        "cmd_model_switch": "Insira o novo identificador do modelo ou o índice da lista: ",
        "cmd_model_success": "[bold green]Modelo alterado com sucesso para:[/bold green] {model}",
        "cmd_model_empty": "[bold yellow]Seleção cancelada. O modelo permaneceu inalterado.[/bold yellow]",
        "cmd_model_cache_empty": "[bold yellow]O cache de modelos está vazio. Execute /refresh para descobrir modelos online.[/bold yellow]",
        
        "cmd_profile_current": "\nPerfil de sistema ativo: [bold green]{profile}[/bold green]",
        "cmd_profile_list": "Perfis de instrução disponíveis: {profiles}",
        "cmd_profile_switch": "Insira o nome do perfil para ativação: ",
        "cmd_profile_success": "[bold green]Contexto de perfil de sistema alterado para:[/bold green] {profile}",
        "cmd_profile_invalid": "[bold red]Erro: O perfil '{profile}' não existe.[/bold red]",
        
        "cmd_provider_list_title": "\n[bold underline]Provedores Configurados[/bold underline]",
        "cmd_provider_list_tip": "\n[dim]Dica: Use '/provider switch <chave>' para mudar de provedor.[/dim]",
        "cmd_provider_switch_prompt": "Insira a chave do provedor para ativar: ",
        "cmd_provider_already_active": "[yellow]O provedor '{provider}' já está ativo.[/yellow]",
        "cmd_provider_switched": "[bold green]Provedor ativo alterado para: '{provider}'. Contexto limpo.[/bold green]",
        "cmd_provider_not_found": "[bold red]Erro: Chave de provedor '{provider}' não encontrada.[/bold red]",
        
        "cmd_refresh_start": "[yellow]Contatando provedor para atualizar as listagens de arquiteturas de modelos...[/yellow]",
        "cmd_refresh_success": "[bold green]Listagem de modelos atualizada e armazenada em cache.[/bold green] Total de registros: {count}",
        "cmd_clear_success": "[bold green]Contexto de conversação limpo. Iniciando uma nova thread do zero.[/bold green]",
        "cmd_setup_start": "\n[yellow]Iniciando o assistente interativo de configuração...[/yellow]\n",
        "cmd_unknown": "[bold red]Comando interno desconhecido.[/bold red] Digite [bold cyan]/help[/bold cyan] para ver comandos.",
        
        "err_title": "Ocorreu um erro inesperado",
        "err_action_tip": "Dica de Solução",
        "err_network": "Falha no handshake de transporte de rede. Verifique as rotas de internet.",
        "err_auth": "Verificação de autenticação negada. A chave de API configurada parece inválida.",
        "err_http_status": "O endpoint do provedor retornou um código de estado inválido: HTTP {status}.",
        "err_config_corrupt": "Seu arquivo de configurações está corrompido. Execute a configuração novamente.",
    }
}

DEFAULT_LANG = "en"

def t(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    target_lang = lang.lower() if lang.lower() in STRINGS else DEFAULT_LANG
    lang_dict = STRINGS[target_lang]
    
    if key in lang_dict:
        msg = lang_dict[key]
    else:
        msg = STRINGS[DEFAULT_LANG].get(key, f"Missing translation token: [{key}]")
        
    format_payload = {"lang": target_lang, **kwargs}
    
    try:
        return msg.format(**format_payload)
    except (KeyError, ValueError, IndexError):
        try:
            return msg.format(lang=target_lang)
        except (KeyError, ValueError, IndexError):
            return msg
