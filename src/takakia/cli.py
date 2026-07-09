"""
Interactive Command-Line REPL Interface.

Manages input reading loops, terminal layout rendering, command line history, 
slash-command dispatch routing, and dynamic response token streaming.
"""

from __future__ import annotations

import sys
from typing import Optional

try:
    import readline
except ImportError:
    readline = None

from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table

from takakia.config import ConfigManager
from takakia.l10n import t
from takakia.profiles import ProfileManager
from takakia.providers.base import ProviderError
from takakia.providers.compatible import OpenAICompatibleProvider
from takakia.session import ChatSession


class ChatCLI:
    """Manages the lifecycle, input capture, and UI rendering of the chat session."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        self.lang = self.config.language
        self.console = Console()
        
        self.profile_manager = ProfileManager()
        system_prompt = self.profile_manager.load_profile(self.config.default_profile)
        self.session = ChatSession(system_prompt=system_prompt)
        
        if self.config.provider_name.lower() in ("gemini", "google") or "generativelanguage.googleapis.com" in self.config.base_url.lower():
            from takakia.providers.google import GoogleGeminiProvider
            self.provider = GoogleGeminiProvider(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                default_model=self.config.default_model,
                extra_headers=self.config.extra_headers,
            )
        else:
            self.provider = OpenAICompatibleProvider(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                default_model=self.config.default_model,
                extra_headers=self.config.extra_headers,
            )
        self.history_path = self.config_manager.cache_dir / "chat_history.txt"

    def start(self) -> None:
        """Launches the interactive session loop and intercepts standard exit hooks."""
        self.console.print(
            t(
                "cli_welcome",
                lang=self.lang,
                profile=self.config.default_profile,
            )
        )
        
        if readline:
            try:
                readline.set_history_length(500)
                if self.history_path.is_file():
                    readline.read_history_file(str(self.history_path))
            except Exception:
                pass

        try:
            while True:
                try:
                    user_input = self._prompt_input()
                    if user_input is None:
                        break
                        
                    if not user_input:
                        continue

                    if user_input.startswith("/"):
                        should_continue = self._handle_command(user_input)
                        if not should_continue:
                            break
                    else:
                        self._process_chat_turn(user_input)
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Operation aborted.[/yellow]")
                    continue
                except Exception as e:
                    self._handle_unexpected_error(e)
        finally:
            if readline:
                try:
                    self.config_manager.ensure_directories()
                    readline.write_history_file(str(self.history_path))
                except Exception:
                    pass
            self.provider.close()

    def _prompt_input(self) -> Optional[str]:
        """Displays standard interface input labels and reads string characters from terminal."""
        self.console.print(t("cli_user_label", lang=self.lang))
        try:
            text = input("> ")
            return text.strip()
        except EOFError:
            return None

    def _process_chat_turn(self, message: str) -> None:
        """Sends new prompt payload text forward into streaming pipelines."""
        self.session.add_message(role="user", content=message)
        payload = self.session.get_payload()

        self.console.print(t("cli_assistant_label", lang=self.lang))
        full_response_buffer = []
        
        try:
            # Bypass intermediate Rich layout buffering to provide jitter-free character updates
            for token in self.provider.stream_chat(messages=payload, model=self.config.default_model):
                sys.stdout.write(token)
                sys.stdout.flush()
                full_response_buffer.append(token)
                
            # Align console metrics post stream rendering explicitly
            self.console.print()
            complete_text = "".join(full_response_buffer)
            if complete_text:
                self.session.add_message(role="assistant", content=complete_text)
                
        except KeyboardInterrupt:
            self.console.print()
            complete_text = "".join(full_response_buffer)
            if complete_text:
                self.session.add_message(role="assistant", content=complete_text)
            self.console.print("\n[yellow]Response generation stream suspended by user.[/yellow]")
        except ProviderError as pe:
            self.console.print()
            complete_text = "".join(full_response_buffer)
            if complete_text:
                self.session.add_message(role="assistant", content=complete_text)
            self._handle_provider_error(pe)
        except Exception as e:
            self.console.print()
            raise e

    def _handle_command(self, cmd_string: str) -> bool:
        """Parses commands starting with forward slashes."""
        parts = cmd_string.split(maxsplit=1)
        command = parts[0].lower().strip()
        argument = parts[1].strip() if len(parts) > 1 else ""

        if command in ("/exit", "/quit"):
            return False
        elif command == "/help":
            self._execute_help()
        elif command == "/clear":
            self.session.clear()
            self.console.print(t("cmd_clear_success", lang=self.lang))
        elif command == "/refresh":
            self._execute_refresh()
        elif command == "/model":
            self._execute_model(argument)
        elif command == "/profile":
            self._execute_profile(argument)
        elif command == "/setup":
            self._execute_setup()
        else:
            self.console.print(t("cmd_unknown", lang=self.lang))
            
        return True

    def _execute_help(self) -> None:
        """Renders functional command ledgers inside an optimized visual text grid layout."""
        table = Table(title=t("cmd_help_header", lang=self.lang), title_justify="left", show_header=False)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        
        table.add_row("/help", t("cmd_help_help", lang=self.lang))
        table.add_row("/clear", t("cmd_help_clear", lang=self.lang))
        table.add_row("/model", t("cmd_help_model", lang=self.lang))
        table.add_row("/profile", t("cmd_help_profile", lang=self.lang))
        table.add_row("/refresh", t("cmd_help_refresh", lang=self.lang))
        table.add_row("/setup", t("cmd_help_setup", lang=self.lang))
        table.add_row("/exit", t("cmd_help_exit", lang=self.lang))
        
        self.console.print(table)

    def _execute_refresh(self) -> None:
        """Forces manual asset scanning updates through underlying API channels."""
        self.console.print(t("cmd_refresh_start", lang=self.lang))
        try:
            models = self.provider.list_models()
            if models:
                self.config_manager.save_model_cache(models)
                self.console.print(t("cmd_refresh_success", lang=self.lang, count=len(models)))
            else:
                self.console.print("[bold yellow]No models found to register.[/bold yellow]")
        except ProviderError as pe:
            self._handle_provider_error(pe)

    def _execute_model(self, argument: str) -> None:
        """Displays currently active AI endpoints or hot-swaps active choices dynamically."""
        cached_models = self.config_manager.load_model_cache()
        
        if not argument:
            self.console.print(t("cmd_model_current", lang=self.lang, model=self.config.default_model))
            
            if not cached_models:
                self.console.print(t("cmd_model_cache_empty", lang=self.lang))
                return
                
            self.console.print("\n[underline]Available discovered models index choices:[/underline]")
            for idx, model in enumerate(cached_models, start=1):
                self.console.print(f"  [bold cyan]{idx}[/] - {escape(model)}")
                
            try:
                selection = input(t("cmd_model_switch", lang=self.lang)).strip()
                if not selection:
                    self.console.print(t("cmd_model_empty", lang=self.lang))
                    return
                argument = selection
            except (EOFError, KeyboardInterrupt):
                self.console.print()
                return

        if argument:
            target_model = argument.strip()
            if target_model.isdigit() and cached_models:
                num = int(target_model)
                if 1 <= num <= len(cached_models):
                    target_model = cached_models[num - 1]
                else:
                    self.console.print("[bold yellow]Selection choice index out of bounds. Action cancelled.[/bold yellow]")
                    return

            self.config.default_model = target_model
            self.config_manager.save_config(self.config)
            self.provider.default_model = self.config.default_model
            self.console.print(t("cmd_model_success", lang=self.lang, model=self.config.default_model))

    def _execute_profile(self, argument: str) -> None:
        """Manages behavioral persona adjustment layers interactively mid-session."""
        available_profiles = self.profile_manager.list_profiles()
        
        if not argument:
            self.console.print(t("cmd_profile_current", lang=self.lang, profile=self.config.default_profile))
            self.console.print(t("cmd_profile_list", lang=self.lang, profiles=", ".join(available_profiles)))
            
            try:
                argument = input(t("cmd_profile_switch", lang=self.lang)).strip()
            except (EOFError, KeyboardInterrupt):
                self.console.print()
                return
                
            if not argument:
                return

        clean_argument = argument.lower().strip()
        if clean_argument in available_profiles:
            self.config.default_profile = clean_argument
            self.config_manager.save_config(self.config)
            
            new_prompt = self.profile_manager.load_profile(clean_argument)
            self.session.update_system_prompt(new_prompt)
            self.console.print(t("cmd_profile_success", lang=self.lang, profile=clean_argument))
        else:
            self.console.print(t("cmd_profile_invalid", lang=self.lang, profile=argument))

    def _execute_setup(self) -> None:
        """Launches the configuration wizard to overwrite settings and hot-reloads runtime parameters."""
        self.console.print(t("cmd_setup_start", lang=self.lang))
        
        from takakia.wizard import SetupWizard
        
        wizard = SetupWizard(self.config_manager)
        new_config = wizard.run()
        
        if not new_config:
            return
            
        self.config = new_config
        self.lang = new_config.language
        
        # Explicitly teardown lingering HTTP transport pools before re-allocation
        self.provider.close()
        
        # Re-instantiate the provider completely to guarantee pristine encapsulation boundaries
        if new_config.provider_name.lower() in ("gemini", "google") or "generativelanguage.googleapis.com" in new_config.base_url.lower():
            from takakia.providers.google import GoogleGeminiProvider
            self.provider = GoogleGeminiProvider(
                api_key=new_config.api_key,
                base_url=new_config.base_url,
                default_model=new_config.default_model,
                extra_headers=new_config.extra_headers,
            )
        else:
            self.provider = OpenAICompatibleProvider(
                api_key=new_config.api_key,
                base_url=new_config.base_url,
                default_model=new_config.default_model,
                extra_headers=new_config.extra_headers,
            )
        
        new_prompt = self.profile_manager.load_profile(new_config.default_profile)
        self.session.update_system_prompt(new_prompt)

    def _handle_provider_error(self, error: ProviderError) -> None:
        """Extracts status signatures from custom provider boundaries safely."""
        from takakia.providers.base import AuthenticationError, HTTPStatusError, NetworkError
        
        self.console.print(f"\n[bold red]⚠ {t('err_title', lang=self.lang)}[/bold red]")
        
        if isinstance(error, AuthenticationError):
            self.console.print(f" {t('err_auth', lang=self.lang)}")
        elif isinstance(error, NetworkError):
            self.console.print(f" {t('err_network', lang=self.lang)}")
        elif isinstance(error, HTTPStatusError):
            self.console.print(f" {t('err_http_status', lang=self.lang, status=error.status_code)}")
            self.console.print(f" [dim]Details: {str(error)}[/dim]")
        else:
            self.console.print(f" [red]{str(error)}[/red]")

    def _handle_unexpected_error(self, error: Exception) -> None:
        """Fallback crash handler ensuring graceful program notifications."""
        self.console.print(f"\n[bold red]⚠ Internal Runtime System Fault Encountered.[/bold red]")
        self.console.print(f" [red]Description: {str(error)}[/red]\n")
