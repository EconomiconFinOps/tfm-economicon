"""Selección explícita del episodio de anomalía que se quiere explicar (JUP-038)."""
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


# `[0-9a-f]` explícito y no `\w`/`\d`, que en `str` aceptan Unicode.
_EPISODE_ID = re.compile(r"anomaly-[0-9a-f]{64}")


class AnomalySelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # `strict=True` impide que pydantic coaccione otros tipos a `str`: es un identificador, no texto libre.
    episode_id: str = Field(strict=True)

    @field_validator("episode_id")
    @classmethod
    def match_whole_identifier(cls, value: str) -> str:
        # `fullmatch` en Python y no `pattern=` de pydantic: ese patrón lo evalúa un motor de Rust cuyo
        # `$`/`\Z` difieren de los de `re`, y en `re` un `$` acepta un `\n` final ("anomaly-<hex>\n").
        # `fullmatch` exige coincidencia completa sin depender del motor ni de esa sutileza de anclas.
        if _EPISODE_ID.fullmatch(value) is None:
            raise ValueError("Expected anomaly- followed by 64 lowercase hexadecimal characters")
        return value
