from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    from dataclasses import MISSING

    class _FieldValue:
        def __init__(self, default: Any = MISSING, default_factory: Any = MISSING):
            self.default = default
            self.default_factory = default_factory

    def Field(default: Any = MISSING, default_factory: Any = MISSING):
        return _FieldValue(default=default, default_factory=default_factory)

    class BaseModel:
        def __init__(self, **kwargs: Any) -> None:
            annotations: dict[str, Any] = {}
            for cls in reversed(self.__class__.mro()):
                annotations.update(getattr(cls, "__annotations__", {}))
            for name in annotations:
                if name in kwargs:
                    value = kwargs[name]
                else:
                    default = getattr(self.__class__, name, MISSING)
                    if isinstance(default, _FieldValue):
                        if default.default_factory is not MISSING:
                            value = default.default_factory()
                        elif default.default is not MISSING:
                            value = default.default
                        else:
                            raise TypeError(f"Missing required field: {name}")
                    elif default is not MISSING:
                        value = default
                    else:
                        raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)

        def model_dump(self) -> dict[str, Any]:
            return {k: getattr(self, k) for k in self.__class__.__annotations__}
