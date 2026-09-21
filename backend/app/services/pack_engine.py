"""Route-order bag packing with weight + volume caps; reject when exceed.

品类约束：印刷品（printed）与液体（liquid）不得同袋；普通（normal）
可与任一方同袋。当当前袋因品类互斥无法装入时，即使重量体积仍够，
也新开一袋。
"""

from __future__ import annotations

from dataclasses import dataclass, field

NORMAL = "normal"
PRINTED = "printed"
LIQUID = "liquid"
CATEGORIES = (NORMAL, PRINTED, LIQUID)


@dataclass(frozen=True)
class StopItem:
    stop_id: int
    seq: int
    weight_kg: float
    volume_l: float
    label: str = ""
    category: str = NORMAL


@dataclass
class Bag:
    bag_index: int
    items: list[StopItem] = field(default_factory=list)
    weight_kg: float = 0.0
    volume_l: float = 0.0

    def has_category(self, category: str) -> bool:
        return any(it.category == category for it in self.items)


@dataclass(frozen=True)
class PackResult:
    bags: list[Bag]
    rejects: list[tuple[StopItem, str]]


def category_compatible(bag: Bag, category: str) -> bool:
    """印刷与液体互斥；普通品类可与任一方同袋。"""
    if category == PRINTED:
        return not bag.has_category(LIQUID)
    if category == LIQUID:
        return not bag.has_category(PRINTED)
    return True


def can_fit(bag: Bag, item: StopItem, max_weight: float, max_volume: float) -> bool:
    return (
        category_compatible(bag, item.category)
        and bag.weight_kg + item.weight_kg <= max_weight + 1e-9
        and bag.volume_l + item.volume_l <= max_volume + 1e-9
    )


def pack_route(
    stops: list[StopItem],
    max_weight: float,
    max_volume: float,
) -> PackResult:
    ordered = sorted(stops, key=lambda s: s.seq)
    bags: list[Bag] = []
    rejects: list[tuple[StopItem, str]] = []
    current: Bag | None = None

    for item in ordered:
        if item.weight_kg > max_weight or item.volume_l > max_volume:
            reason = []
            if item.weight_kg > max_weight:
                reason.append(f"超重 {item.weight_kg}>{max_weight}")
            if item.volume_l > max_volume:
                reason.append(f"超体积 {item.volume_l}>{max_volume}")
            rejects.append((item, "；".join(reason)))
            continue

        if current is None or not can_fit(current, item, max_weight, max_volume):
            current = Bag(bag_index=len(bags) + 1)
            bags.append(current)

        if not can_fit(current, item, max_weight, max_volume):
            # should not happen after single-item check, but keep safe
            rejects.append((item, "无法装入新袋"))
            continue

        current.items.append(item)
        current.weight_kg += item.weight_kg
        current.volume_l += item.volume_l

    return PackResult(bags=bags, rejects=rejects)
