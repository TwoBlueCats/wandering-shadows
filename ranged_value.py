from __future__ import annotations

import random
from typing import Union


class Range:
    def __init__(self, value=0, stop=None):
        self._value = value
        self._stop = stop or value

        if self._value > self._stop:
            self._value, self._stop = self._stop, self._value

    @property
    def value(self) -> int:
        return int(self)

    def __int__(self):
        return random.randint(self._value, self._stop)

    def __add__(self, other) -> Range:
        value = Range(self._value, self._stop)
        value += other
        return value

    def __iadd__(self, other: Union[int, Range]) -> Range:
        if isinstance(other, Range):
            self._value += other._value
            self._stop += other._stop
        else:
            self._value += other
            self._stop += other
        return self

    def __mul__(self, other: float) -> Range:
        if not isinstance(other, float):
            raise NotImplemented
        assert other >= 1
        value = Range(self._value, self._stop)
        value._value = int(value._value * other)
        value._stop = int(value._stop * other)
        return value

    def __str__(self):
        if self._value == self._stop:
            return str(self._value)
        else:
            return f"{self._value}-{self._stop}"

    def __gt__(self, other):
        return self._value > other
