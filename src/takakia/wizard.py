"""
Interactive Initial Configuration Setup Wizard.

Guides users step-by-step through setting language preferences, provider URLs,
and API key entries while validating credentials dynamically against live endpoints.
"""

from __future__ import annotations

import getpass
import re
from typing import Optional
from urllib.parse import urlparse

from rich.console import Console

from takakia.config import AppConfig, ConfigManager, ProviderConfig
from takakia.l10n import t
from takakia.providers.base import AuthenticationError, ProviderError
from takakia.providers.factory import ProviderFactory


class SetupWizard:
    """Provides a step-by-step CLI setup wizard to generate clean application configurations."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.console = Console()

    def run(self) -> Optional[AppConfig]:
        """Executes the interactive onboarding sequence."""
        try:
            self.console.print(t("wizard_welcome", lang="en"))
            
            lang = self._setup_language()
            
            config = self.config_manager.load_config()
            config.language = lang
            self.config_manager.save_config(config)
            
            self.run_provider_setup(config)
            
            return self.config_manager.load_config()

        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[bold yellow]Setup onboarding execution interrupted.[/bold yellow]")
            return None

    def run_provider_setup(self, config: Optional[AppConfig] = None) -> Optional[str]:
        """Configures a new provider and appends it to the configuration."""
        if config is None:
            config = self.config_manager.load_config()
        lang = config.language
        
        try:
            provider_key = input("Enter a short key for this provider (e.g., 'work', 'openai', 'gemini'): ").strip().lower()
            if not provider_key:
                self.console.print("[bold red]Provider key cannot be empty.[/bold red]")
                return None
                
            provider_key = re.sub(r'[^a-z0-9_-]', '', provider_key)
            
            provider_name = input(f"{t('wizard_provider_name', lang=lang)}: ").strip()
            if not provider_name:
                provider_name = provider_key.title()
                
            default_url = "https://openrouter.ai/api/v1"
            if "openai" in provider_key or "openai" in provider_name.lower():
                default_url = "https://api.openai.com/v1"
            elif "gemini" in provider_key or "google" in provider_name.lower():
                default_url = "https://generativelanguage.googleapis.com"
                
            base_url = input(f"{t('wizard_url_prompt', lang=lang)} [{default_url}]: ").strip()
            if not base_url:
                base_url = default_url
            
            cleaned_url = base_url.rstrip("/")
            if not (cleaned_url.startswith("http://") or cleaned_url.startswith("https://")):
                temp_url = f"http://{cleaned_url}"
                hostname = urlparse(temp_url).hostname or ""

                is_local = (
                    hostname in ("localhost", "127.0.0.1", "::1") or
                    re.match(r"^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)", hostname)
                )
                cleaned_url = f"http://{cleaned_url}" if is_local else f"https://{cleaned_url}"

            while True:
                try:
                    api_key = getpass.getpass(f"{t('wizard_key_prompt', lang=lang)}: ").strip()
                    if api_key:
                        break
                except KeyboardInterrupt:
                    self.console.print()
                    raise
                self.console.print(t("wizard_key_required", lang=lang))

            extra_headers = {}
            if "openrouter.ai" in cleaned_url.lower():
                extra_headers = {
                    "HTTP-Referer": "https://github.com/username/takakia",
                    "X-Title": "Lightweight Study Chat CLI"
                }

            default_model = "meta-llama/llama-3.1-8b-instruct"
            if "api.openai.com" in cleaned_url:
                default_model = "gpt-4o-mini"
            elif "generativelanguage" in cleaned_url:
                default_model = "gemini-2.5-flash"

            p_config = ProviderConfig(
                name=provider_name,
                base_url=cleaned_url,
                api_key=api_key,
                default_model=default_model,
                extra_headers=extra_headers
            )
            
            self.console.print(t("wizard_fetch_models", lang=lang))
            
            discovered_models: list[str] = []
            test_provider = ProviderFactory.create(p_config)
            
            try:
                discovered_models = test_provider.list_models()
                if discovered_models:
                    self.console.print(t("wizard_fetch_success", lang=lang))
                    self.config_manager.save_model_cache(discovered_models, provider_key=provider_key)
            except ProviderError as pe:
                self.console.print(t("wizard_fetch_failed", lang=lang, error=str(pe)))
                if isinstance(pe, AuthenticationError):
                    self.console.print("\n[bold red]FATAL: API Key is invalid. Aborting setup.[/bold red]")
                    return None
            finally:
                test_provider.close()

            if discovered_models:
                visible_sample = discovered_models[:10]
                self.console.print(f"\n[underline]Discovered Provider Models Sample (Top 10):[/underline]")
                for idx, m in enumerate(visible_sample, start=1):
                    self.console.print(f"  {idx} - {m}")
                if len(discovered_models) > 10:
                    self.console.print(f"  ... and {len(discovered_models) - 10} more options cached.")
                    
                self.console.print(f"\n{t('wizard_model_select', lang=lang)}")
                selection = input(f"[{p_config.default_model}]: ").strip()
                
                if selection:
                    if selection.isdigit():
                        num = int(selection)
                        if 1 <= num <= len(discovered_models):
                            p_config.default_model = discovered_models[num - 1]
                        else:
                            self.console.print(f"\n[bold yellow]Selection choice index {num} out of range. Retaining baseline default.[/bold yellow]\n")
                    else:
                        p_config.default_model = selection
            else:
                custom_selection = input(f"{t('wizard_model_custom', lang=lang)} [{p_config.default_model}]: ").strip()
                if custom_selection:
                    p_config.default_model = custom_selection

            config.providers[provider_key] = p_config
            config.active_provider = provider_key
            
            self.config_manager.save_config(config)
            self.console.print(t("wizard_success", lang=lang))
            
            return provider_key

        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[bold yellow]Setup onboarding execution interrupted.[/bold yellow]")
            return None

    def _setup_language(self) -> str:
        """Presents internal internationalization choices and intercepts selection keys."""
        while True:
            choice = input(f"{t('wizard_lang_select', lang='en')} [en]: ").strip().lower()
            if not choice:
                return "en"
            if choice in ("en", "pt_br"):
                return choice
            self.console.print(t("wizard_lang_invalid", lang="en"))
