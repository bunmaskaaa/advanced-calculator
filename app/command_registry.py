from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

# NOTE: We avoid importing Calculator to prevent circular imports.
# Handlers receive (calc, args) where calc is your Calculator instance.
Handler = Callable[[object, List[str]], None]

@dataclass
class CommandSpec:
    name: str
    handler: Handler
    help: str
    aliases: List[str]

_registry: Dict[str, CommandSpec] = {}
_alias_to_name: Dict[str, str] = {}

def command(name: str, help: str, aliases: Optional[List[str]] = None):
    """
    Decorator to register a REPL command. Usage:

        @command("echo", "print arguments back", aliases=["say"])
        def echo(calc, args):
            print(" ".join(args))
    """
    def decorator(func: Handler) -> Handler:
        spec = CommandSpec(name=name, handler=func, help=help, aliases=list(aliases or []))
        _registry[name] = spec
        for al in spec.aliases:
            _alias_to_name[al] = name
        return func
    return decorator

def resolve(name: str) -> Optional[CommandSpec]:
    canonical = _alias_to_name.get(name, name)
    return _registry.get(canonical)

def all_specs() -> List[CommandSpec]:
    # Return a stable order: alphabetical by name
    return sorted(_registry.values(), key=lambda s: s.name)

def aliases_for(name: str) -> List[str]:
    spec = _registry.get(name)
    return list(spec.aliases) if spec else []