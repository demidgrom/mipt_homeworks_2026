from collections.abc import Callable
from dataclasses import dataclass, field
from abc import abstractmethod
from typing import Any, TypeVar, cast

from part4_oop.interfaces import Cache, HasCache, Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class DictStorage(Storage[K, V]):
    _data: dict[K, V] = field(default_factory=dict, init=False)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        if self.exists(key):
            return self._data[key]

        return None

    def exists(self, key: K) -> bool:
        return key in self._data

    def remove(self, key: K) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


@dataclass
class AbstractPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) >= self.capacity:
            return self._order[0]

        return None

    @abstractmethod
    def register_access(self, key: K) -> None:
        pass

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._order) != 0


@dataclass
class FIFOPolicy(AbstractPolicy[K]):

    def register_access(self, key: K) -> None:
        if key in self._order:
            return

        self._order.append(key)


@dataclass
class LRUPolicy(AbstractPolicy[K]):

    def register_access(self, key: K) -> None:
        if key in self._order:
            self.remove_key(key)

        self._order.append(key)


@dataclass
class LFUPolicy(AbstractPolicy[K]):

    def register_access(self, key: K) -> None:
        if key in self._key_counter:
            self._key_counter[key] += 1
            return

        if len(self._key_counter) >= self.capacity:
            return

        self._key_counter[key] = 1

    def get_key_to_evict(self) -> K | None:
        if len(self._key_counter) > self.capacity:
            min_key: K = min(self._key_counter.items(), key=lambda count: count[1])[0]

            return min_key

        return None

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)

    def clear(self) -> None:
        self._key_counter.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._key_counter) != 0


class MIPTCache(Cache[K, V]):
    def __init__(self, storage: Storage[K, V], policy: Policy[K]) -> None:
        self.storage = storage
        self.policy = policy

    def set(self, key: K, value: V) -> None:
        self.policy.register_access(key)
        self.storage.set(key, value)

        free_data: K | None = self.policy.get_key_to_evict()

        if free_data is not None:
            self.storage.remove(free_data)
            self.policy.remove_key(free_data)

    def get(self, key: K) -> V | None:
        self.policy.register_access(key)

        return self.storage.get(key)

    def exists(self, key: K) -> bool:
        return self.storage.exists(key)

    def remove(self, key: K) -> None:
        if self.exists(key):
            self.storage.remove(key)
            self.policy.remove_key(key)

    def clear(self) -> None:
        self.storage.clear()
        self.policy.clear()


class CachedProperty[V]:
    def __init__(self, func: Callable[[Any], V]) -> None:
        self._func = func
        self._attr_name: str | None = None

    def __get__(self, instance: HasCache[str, V] | None, owner: type) -> Any:
        if instance is None:
            return self

        if self._attr_name is None:
            for name, attr in owner.__dict__.items():
                if attr is self:
                    self._attr_name = name
                    break

            if self._attr_name is None:
                return None

        cache = instance.cache
        key = self._attr_name

        if cache.exists(key):
            return cast(V, cache.get(key))

        value = self._func(instance)
        cache.set(key, value)
        return value
