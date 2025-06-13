from fastapi_filter.base.filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from src.sports.models import Sport, SportObject, Inventory, SportObjectInventory


class InventoryFilter(Filter):
    name__in: list[str] | None = None

    class Constants(Filter.Constants):
        model = Inventory


class SportObjectInventoryFilter(Filter):
    amount__lt: int | None = None
    amount__gte: int | None = None
    inventory: InventoryFilter | None = FilterDepends(
        with_prefix("inventory", InventoryFilter))

    class Constants(Filter.Constants):
        model = SportObjectInventory


class SportFilter(Filter):
    name__in: list[str] | None = None

    class Constants(Filter.Constants):
        model = Sport


class SportObjectFilter(Filter):
    name__ilike: str | None = None
    tags: SportFilter | None = FilterDepends(with_prefix("tag", SportFilter))
    inventory: SportObjectInventoryFilter | None = FilterDepends(
        with_prefix("inventory", SportObjectInventoryFilter))

    class Constants(Filter.Constants):
        model = SportObject
