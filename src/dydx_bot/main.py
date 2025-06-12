"""
dYdX v4 Perpetual Trading Bot - Main Application

Protocol-First Entry Point using official dydx-v4-client
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from .config import Settings, settings
from .connection import DydxClientManager

# Configure rich console and logging
console = Console()
app = typer.Typer(
    name="dydx-trader",
    help="dYdX v4 Perpetual Trading Bot - Protocol-First Implementation"
)

# Global application state
client_manager: Optional[DydxClientManager] = None
shutdown_event = asyncio.Event()


def setup_logging(log_level: str = "INFO") -> None:
    """Setup rich logging with protocol-first focus"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


async def initialize_application() -> DydxClientManager:
    """Initialize the dYdX v4 trading bot with protocol-first approach"""
    console.print("[bold blue]Initializing dYdX v4 Trading Bot[/bold blue]")
    
    # Validate configuration for trading
    try:
        settings.validate_for_trading()
        console.print(f"✓ Configuration validated for {settings.dydx_network}")
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise
    
    # Initialize dYdX v4 client manager
    manager = DydxClientManager(settings)
    await manager.connect()
    
    # Perform health check
    health = await manager.health_check()
    console.print(f"✓ Client health check: {health}")
    
    return manager


async def shutdown_application(manager: DydxClientManager) -> None:
    """Graceful shutdown of the trading bot"""
    console.print("[yellow]Shutting down dYdX v4 Trading Bot[/yellow]")
    
    try:
        await manager.disconnect()
        console.print("✓ Client disconnected")
    except Exception as e:
        console.print(f"[red]Error during shutdown: {e}[/red]")


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully"""
    console.print(f"[yellow]Received signal {signum}, initiating shutdown...[/yellow]")
    shutdown_event.set()


async def main_async() -> None:
    """Main async application loop"""
    global client_manager
    
    try:
        # Initialize the application
        client_manager = await initialize_application()
        
        console.print("[green]dYdX v4 Trading Bot initialized successfully![/green]")
        console.print("[blue]Protocol-first implementation using official dydx-v4-client[/blue]")
        
        # Main application loop - for now just wait for shutdown
        console.print("[cyan]Bot is running... Press Ctrl+C to stop[/cyan]")
        
        # TODO: Add main trading loop here
        # - Market data subscription via IndexerSocket
        # - Signal generation and strategy execution
        # - Risk management and position monitoring
        # - Terminal dashboard updates
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
    except KeyboardInterrupt:
        console.print("[yellow]Keyboard interrupt received[/yellow]")
    except Exception as e:
        console.print(f"[red]Application error: {e}[/red]")
        raise
    finally:
        if client_manager:
            await shutdown_application(client_manager)


@app.command()
def run(
    log_level: str = typer.Option("INFO", help="Logging level"),
    config_file: Optional[str] = typer.Option(None, help="Custom config file path"),
) -> None:
    """
    Run the dYdX v4 perpetual trading bot
    
    Protocol-first implementation using official dydx-v4-client.
    """
    # Setup logging
    setup_logging(log_level)
    
    # Override settings if config file provided
    if config_file:
        # TODO: Implement custom config file loading
        console.print(f"[yellow]Custom config file not yet implemented: {config_file}[/yellow]")
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the main async application
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("[yellow]Application stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


@app.command()
def test_connection() -> None:
    """Test dYdX v4 client connection and configuration"""
    
    async def test_async():
        console.print("[blue]Testing dYdX v4 client connection...[/blue]")
        
        try:
            manager = DydxClientManager(settings)
            await manager.connect()
            
            health = await manager.health_check()
            console.print(f"✓ Health check results: {health}")
            
            # Test basic IndexerClient functionality
            if health["indexer_client"]:
                time_response = await manager.indexer_client.utility.get_time()
                console.print(f"✓ Server time: {time_response}")
            
            console.print("[green]Connection test successful![/green]")
            
            await manager.disconnect()
            
        except Exception as e:
            console.print(f"[red]Connection test failed: {e}[/red]")
            sys.exit(1)
    
    setup_logging("INFO")
    asyncio.run(test_async())


@app.command()
def config_info() -> None:
    """Display current configuration information"""
    console.print("[blue]dYdX v4 Trading Bot Configuration[/blue]")
    console.print(f"Network: {settings.dydx_network}")
    console.print(f"Paper Trading: {settings.paper_trading}")
    console.print(f"Initial Capital: ${settings.initial_capital:,.2f}")
    console.print(f"Max Leverage: {settings.max_leverage}x")
    console.print(f"Risk Tolerance: {settings.risk_tolerance * 100:.1f}%")
    console.print(f"Wallet Configured: {settings.has_wallet_config()}")


def main() -> None:
    """Entry point for the CLI application"""
    app()


if __name__ == "__main__":
    main()
