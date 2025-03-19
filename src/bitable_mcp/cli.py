import json
import sys
from pathlib import Path
from typing import Optional, Dict
import logging
import sys
import os
import typer
from shutil import which


logger = logging.getLogger(__file__)

app = typer.Typer(
    name="bitable-mcp",
    help="bitable-mcp install tools",
    add_completion=False,
    no_args_is_help=True,  # Show help if no args provided
)



def get_claude_config_path() -> Path | None:
    """Get the Claude config directory based on platform."""
    if sys.platform == "win32":
        path = Path(Path.home(), "AppData", "Roaming", "Claude")
    elif sys.platform == "darwin":
        path = Path(Path.home(), "Library", "Application Support", "Claude")
    else:
        return None

    if path.exists():
        return path
    return None


def update_claude_config(
    server_name: str,
    command: str,
    args: list[str],
    *,
    env_vars: Optional[Dict[str, str]] = None,
) -> bool:
    """Add or update a FastMCP server in Claude's configuration.
    """
    config_dir = get_claude_config_path()
    if not config_dir:
        raise RuntimeError(
            "Claude Desktop config directory not found. Please ensure Claude Desktop "
            "is installed and has been run at least once to initialize its configuration."
        )

    config_file = config_dir / "claude_desktop_config.json"
    if not config_file.exists():
        try:
            config_file.write_text("{}")
        except Exception as e:
            logger.error(
                "Failed to create Claude config file",
                extra={
                    "error": str(e),
                    "config_file": str(config_file),
                },
            )
            return False

    try:
        config = json.loads(config_file.read_text())
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Always preserve existing env vars and merge with new ones
        if (
            server_name in config["mcpServers"]
            and "env" in config["mcpServers"][server_name]
        ):
            existing_env = config["mcpServers"][server_name]["env"]
            if env_vars:
                # New vars take precedence over existing ones
                env_vars = {**existing_env, **env_vars}
            else:
                env_vars = existing_env

        server_config = {
            "command": command,
            "args": args,
        }

        # Add environment variables if specified
        if env_vars:
            server_config["env"] = env_vars

        config["mcpServers"][server_name] = server_config

        config_file.write_text(json.dumps(config, indent=2))
        logger.info(
            f"Added server '{server_name}' to Claude config",
            extra={"config_file": str(config_file)},
        )
        return True
    except Exception as e:
        logger.error(
            "Failed to update Claude config",
            extra={
                "error": str(e),
                "config_file": str(config_file),
            },
        )
        return False


@app.command()
def install() -> None:
    """Install a current server in the Claude desktop app.
    """

    name = "bitable-mcp"

    env_dict = {}
    local_bin = Path(Path.home(), ".local", "bin")
    pyenv_shims = Path(Path.home(), ".pyenv", "shims")
    path = os.environ['PATH']
    if sys.platform == "win32":
        env_dict["PATH"] = f"{local_bin};{pyenv_shims};{path}"
    else:
        env_dict["PATH"] = f"{local_bin}:{pyenv_shims}:{path}"

    api_key = os.environ['PERSONAL_BASE_TOKEN'] if "PERSONAL_BASE_TOKEN" in os.environ else "your-api-key-here"
    app_token = os.environ['APP_TOKEN'] if "APP_TOKEN" in os.environ else "your-app-token"
    env_dict["PERSONAL_BASE_TOKEN"] = api_key
    env_dict["APP_TOKEN"] = app_token

    uv = which('uvx')
    command = uv if uv else "uvx"
    args = [name]

    # print("----------update", command, args, env_dict)

    if update_claude_config(
        command,
        name,
        args,
        env_vars=env_dict,
    ):
        logger.info(f"Successfully installed {name} in Claude app")
    else:
        logger.error(f"Failed to install {name} in Claude app")
        sys.exit(1)
