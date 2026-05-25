"""Contrato base para los conectores de fuentes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from ..config import ElectionConfig, Settings


@dataclass
class RawMention:
    """Mencion cruda tal como llega de una fuente, antes del analisis."""

    source: str
    text: str
    published_at: datetime
    external_id: str | None = None
    author: str | None = None
    url: str | None = None
    lang: str = "es"
    engagement: int = 0
    reach: int = 0
    extra: dict = field(default_factory=dict)


class BaseConnector(ABC):
    """Interfaz comun de los conectores.

    `available` indica si el conector puede traer datos reales (p. ej. si tiene
    credenciales). Si no esta disponible, la ingesta lo omite y el monitor
    sigue funcionando con los datos sembrados.
    """

    source: str = "generic"

    def __init__(self, config: ElectionConfig, settings: Settings):
        self.config = config
        self.settings = settings

    @property
    def available(self) -> bool:
        return True

    @abstractmethod
    def fetch(self, limit: int = 100) -> list[RawMention]:
        """Devuelve menciones crudas de la fuente."""
        raise NotImplementedError
