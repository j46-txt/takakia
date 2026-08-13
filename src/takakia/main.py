"""
Application Entry Point and Global Exception Interceptor.

Orchestrates startup verification sequences, initial configuration routing,
and establishes platform-compliant silent diagnostic log output paths.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from takakia.config import ConfigManager
from takakia.cli import BANNER, ChatCLI
from takakia.l10n import t


def setup_diagnostic_logger(config_manager: ConfigManager) -> logging.Logger:
    """
    Configures standard file logging structures inside platform cache destinations.
    
    Guarantees runtime file access operations do not interfere with main loop execution.
    """
    config_manager.ensure_directories()
    log_file_path = config_manager.log_dir / "error.log"
    
    logger = logging.getLogger("takakia")
    logger.setLevel(logging.ERROR)
    
    if not logger.handlers:
        try:
            file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            logger.addHandler(logging.NullHandler())
            
    return logger


def main() -> None:
    """Core initialization routine acting as the structural CLI process execution binary."""
    # Secure standard streaming pipes on Windows nodes against legacy code pages
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

    console = Console()
    
    # Render application banner exactly once at startup
    console.print(BANNER)
    
    config_manager = ConfigManager()
    logger = setup_diagnostic_logger(config_manager)
    
    current_config = config_manager.load_config()
    ui_lang = current_config.language if current_config else "en"

    try:
        if not config_manager.is_configured():
            from takakia.wizard import SetupWizard
            wizard = SetupWizard(config_manager)
            current_config = wizard.run()
            if not current_config:
                sys.exit(0)
            ui_lang = current_config.language

        cli = ChatCLI(config_manager)
        cli.start()

    except KeyboardInterrupt:
        sys.exit(0)
        
    except SystemExit as exit_signal:
        sys.exit(exit_signal.code)
        
    except Exception as unexpected_error:
        try:
            logger.exception("A fatal unhandled crash occurred at user runtime:")
        except Exception:
            pass
        
        try:
            fresh_config = config_manager.load_config()
            if fresh_config and fresh_config.language:
                ui_lang = fresh_config.language
        except Exception:
            pass

        try:
            error_title = f"[bold red]⚠ {t('err_title', lang=ui_lang)}[/bold red]"
            log_location = config_manager.log_dir / "error.log"
            
            error_details = (
                f"[red]Error Type:[/] {type(unexpected_error).__name__}\n"
                f"[red]Description:[/] {str(unexpected_error)}\n\n"
                f"[dim]Detailed internal system execution logs have been saved to:\n"
                f"{log_location}[/dim]"
            )
            
            console.print()
            console.print(
                Panel.fit(
                    error_details,
                    title=error_title,
                    border_style="red",
                    padding=(1, 2)
                )
            )
        except Exception:
            # Absolute baseline runtime isolation safety fallback path
            sys.stderr.write(f"\n⚠ Fatal Application Crash: {type(unexpected_error).__name__} - {str(unexpected_error)}\n")
            
        sys.exit(1)


if __name__ == "__main__":
    main()
