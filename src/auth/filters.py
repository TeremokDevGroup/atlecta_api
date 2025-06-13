from typing import Literal
from fastapi_filter.base.filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import field_validator

from src.sports.filters import SportFilter

from src.auth.models import UserProfile


class UserProfileFilter(Filter):
    gender: Literal["0", "1"] | None = None
    sports: SportFilter | None = FilterDepends(
        with_prefix("sports", SportFilter))
    order_by: list[str] | None = None

    @field_validator("gender")
    def validate_gender(cls, value):
        if value is None:
            return None
        # Convert string input to integer
        try:
            return int(value)
        except ValueError:
            raise ValueError(
                f"gender must be '0' or '1' but received value is {value}")

    class Constants(Filter.Constants):
        model = UserProfile
        search_model_fields = ["first_name", "last_name"]
