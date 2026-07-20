"""
Interactive Initial Configuration Setup Wizard.

Guides users step-by-step through setting language preferences, provider URLs,
and API key entries while validating credentials dynamically against live endpoints.
"""

from __future__ import annotations

import getpass
import re
import sys
from typing import Optional
from urllib.parse import urlparse

from rich.console import Console

from takakia.config import AppConfig, ConfigManager
from takakia.l10n import t
from takakia.providers.base import AuthenticationError, ProviderError
from takakia.providers.compatible import OpenAICompatibleProvider


class SetupWizard:
    """Provides a step-by-step CLI setup wizard to generate clean application configurations."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.console = Console()

    def run(self) -> Optional[AppConfig]:
        """
        Executes the interactive onboarding sequence.
        
        Returns a validated, production-ready AppConfig instance after saving
        the setup results safely to disk, or None if terminated by the user.
        """
        try:
            self.console.print(t("wizard_welcome", lang="en"))
            
            # 1. Select Interface Language
            lang = self._setup_language()
            
            # Load existing configuration to preserve non-prompted parameters
            config = self.config_manager.load_config()
            config.language = lang
            
            # 2. Select Provider Profile details
            provider_name = input(f"{t('wizard_provider_name', lang=lang)} [{config.provider_name}]: ").strip()
            if not provider_name:
                provider_name = config.provider_name
            config.provider_name = provider_name

            # Determine reasonable base URL defaults based on selected provider names
            default_url = "https://openrouter.ai/api/v1"
            if provider_name.lower() == "openrouter/free":
                default_url = "https://api.openai.com/v1"
                config.default_model = "gpt-4o-mini"
            elif provider_name.lower() in ("gemini", "google"):
                default_url = "https://generativelanguage.googleapis.com"
                config.default_model = "gemini-2.5-flash"
            elif config.base_url:
                default_url = config.base_url
                
            base_url = input(f"{t('wizard_url_prompt', lang=lang)} [{default_url}]: ").strip()
            if not base_url:
                base_url = default_url
            
            # Enforce and self-heal basic connection layer protocol scheme requirements
            cleaned_url = base_url.rstrip("/")
            if not (cleaned_url.startswith("http://") or cleaned_url.startswith("https://")):
                # Prefix temporarily to trick urlparse into mapping the netloc correctly
                temp_url = f"http://{cleaned_url}"
                hostname = urlparse(temp_url).hostname or ""

                is_local = (
                    hostname in ("localhost", "127.0.0.1", "::1") or
                    re.match(r"^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)", hostname)
                )
                cleaned_url = f"http://{cleaned_url}" if is_local else f"https://{cleaned_url}"
            config.base_url = cleaned_url

            # 3. Securely Capture API Token Credentials
            while True:
                try:
                    api_key = getpass.getpass(f"{t('wizard_key_prompt', lang=lang)}: ").strip()
                    if api_key:
                        config.api_key = api_key
                        break
                except KeyboardInterrupt:
                    # Explicitly line feed out of intercepted password fields to clean line metrics
                    self.console.print()
                    raise
                self.console.print(t("wizard_key_required", lang=lang))

            # Add default OpenRouter parameters if the default provider remains active
            if "openrouter.ai" in config.base_url.lower():
                config.extra_headers = {
                    "HTTP-Referer": "https://github.com/username/takakia",
                    "X-Title": "Lightweight Study Chat CLI"
                }

            # 4. Attempt Automated Model Discovery Context Verification
            self.console.print(t("wizard_fetch_models", lang=lang))
            
            discovered_models: list[str] = []
            test_provider = None
            try:
                if config.is_gemini_native:
                    from takakia.providers.google import GoogleGeminiProvider
                    test_provider = GoogleGeminiProvider(
                        api_key=config.api_key,
                        base_url=config.base_url,
                        default_model=config.default_model,
                        extra_headers=config.extra_headers
                    )
                else:
                    test_provider = OpenAICompatibleProvider(
                        api_key=config.api_key,
                        base_url=config.base_url,
                        default_model=config.default_model,
                        extra_headers=config.extra_headers
                    )
                discovered_models = test_provider.list_models()
                
                if discovered_models:
                    self.console.print(t("wizard_fetch_success", lang=lang))
                    self.config_manager.save_model_cache(discovered_models)
            except ProviderError as pe:
                self.console.print(t("wizard_fetch_failed", lang=lang, error=str(pe)))
                if isinstance(pe, AuthenticationError):
                    self.console.print("\n[bold red]FATAL: API Key is invalid. Aborting setup.[/bold red]")
                    return None
            finally:
                if test_provider is not None:
                    test_provider.close()

            # 5. Model Selection Finalization
            if discovered_models:
                visible_sample = discovered_models[:10]
                self.console.print(f"\n[underline]Discovered Provider Models Sample (Top 10):[/underline]")
                for idx, m in enumerate(visible_sample, start=1):
                    self.console.print(f"  {idx} - {m}")
                if len(discovered_models) > 10:
                    self.console.print(f"  ... and {len(discovered_models) - 10} more options cached.")
                    
                self.console.print(f"\n{t('wizard_model_select', lang=lang)}")
                selection = input(f"[{config.default_model}]: ").strip()
                
                if selection:
                    if selection.isdigit():
                        num = int(selection)
                        # Bounds check evaluates the full array list sequence safely
                        if 1 <= num <= len(discovered_models):
                            config.default_model = discovered_models[num - 1]
                        else:
                            self.console.print(f"\n[bold yellow]Selection choice index {num} out of range. Retaining baseline default.[/bold yellow]\n")
                    else:
                        config.default_model = selection
            else:
                custom_selection = input(f"{t('wizard_model_custom', lang=lang)} [{config.default_model}]: ").strip()
                if custom_selection:
                    config.default_model = custom_selection

            # 6. Persist Configuration Securely to Disk
            self.config_manager.save_config(config)
            self.console.print(t("wizard_success", lang=lang))
            
            return config

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
