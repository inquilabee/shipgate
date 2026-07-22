"""Shared registry helper."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self, items: dict[str, T], *, unknown_message: str) -> None:
        self._items = dict(items)
        self._unknown_message = unknown_message

    def get(self, name: str) -> T:
        try:
            return self._items[name]
        except KeyError as exc:
            raise ValueError(self._unknown_message.format(name=name)) from exc

    def keys(self) -> frozenset[str]:
        return frozenset(self._items)

    def items(self) -> dict[str, T]:
        return dict(self._items)

    def __contains__(self, name: object) -> bool:
        return name in self._items
