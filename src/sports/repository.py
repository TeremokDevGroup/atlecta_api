import logging
from typing import Type

from fastapi_filter.contrib.sqlalchemy import Filter
from geoalchemy2.functions import ST_Distance, ST_MakePoint, ST_SetSRID
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.repository import ModelType, SQLAlchemyRepository
from src.sports.models import Inventory, Sport, SportObject, SportObjectImage, SportObjectInventory
from src.sports.schemas import (
    SportObjectCreateSchema,
    SportObjectImageCreateSchema,
    SportObjectUpdateSchema,
)
from src.utils import parse_pydantic_schema


class InventoryRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Inventory) -> None:
        super().__init__(model, db_session)

    async def get_or_create_inventory(self, name: str) -> Sport:
        inventory = await self.db_session.scalar(select(Inventory).filter_by(name=name))
        if inventory is None:
            inventory = Inventory(name=name)
            self.db_session.add(inventory)
        return inventory


class SportRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = Sport) -> None:
        super().__init__(model, db_session)

    async def get_or_create_sport(self, name: str) -> Sport:
        sport = await self.db_session.scalar(select(Sport).filter_by(name=name))
        if sport is None:
            sport = Sport(name=name)
            self.db_session.add(sport)
        return sport


class SportObjectImageRepository(SQLAlchemyRepository):
    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = SportObjectImage) -> None:
        super().__init__(model, db_session)

    async def create(self, sport_object_id: int, data: SportObjectImageCreateSchema) -> SportObject:
        async with self.db_session as session:
            # WARNING: Handle error if there is no such sport object in database
            stmt = select(SportObject).where(
                SportObject.id == sport_object_id)
            res = await session.execute(stmt)
            sport_object = res.scalar_one()

            parsed_schema = parse_pydantic_schema(data)
            instance = self.model(**parsed_schema)

            sport_object.images.append(instance)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)

        return instance

    async def get_all_by_object_id(self, order: str = "id", limit: int = 100, offset: int = 0, **filters) -> list[ModelType] | None:
        async with self.db_session as session:
            stmt = select(SportObject).filter_by(**filters)

            result = await session.execute(stmt)
            sport_object = result.scalars().first()

            if sport_object:
                return sport_object.images
            else:
                return None


class SportObjectRepository(SQLAlchemyRepository):

    def __init__(self, db_session: AsyncSession, model: Type[ModelType] = SportObject) -> None:
        super().__init__(model, db_session)

    async def create(self, data: SportObjectCreateSchema) -> ModelType:
        async with self.db_session as session:
            parsed_schema = parse_pydantic_schema(data)
            tags = parsed_schema.pop("tags")
            instance = self.model(**parsed_schema)

            # WARNING: Just a feeling I get, that this is so bad...
            for tag in tags:
                query = select(Sport).where(Sport.name == tag.name)
                db_tag = (await session.execute(query)).scalar_one_or_none()

                # TODO: Do not create a tag if there is no such tag in database
                if db_tag is None:
                    # db_tag = tag
                    # session.add(db_tag)
                    continue

                instance.tags.append(db_tag)

            session.add(instance)
            # await session.flush()
            await session.commit()

            return instance

    async def get_multi(
        self,
        order_by: str = "id",
        order_direction: str = "asc",
        limit: int = 100,
        last_id: int | None = None,
        filter: Filter | None = None
    ) -> list[SportObject]:
        async with self.db_session as session:
            # Define allowed columns for ordering to prevent SQL injection
            order_columns = {
                "id": self.model.id,
                "name": self.model.name,
                # Add other columns as needed, e.g., "y_coord": self.model.y_coord
            }

            # Validate order_by
            if order_by not in order_columns:
                raise ValueError(
                    f"Invalid order_by column: {order_by}. Allowed: {list(order_columns.keys())}")

            # Choose ascending or descending order
            order_func = asc if order_direction.lower() == "asc" else desc
            order_column = order_columns[order_by]

            stmt = (
                select(self.model)
                .outerjoin(self.model.images)
                .outerjoin(self.model.tags)
                .outerjoin(self.model.inventory)
                .outerjoin(Inventory)
                .where(self.model.id > (last_id or 0))  # Keyset pagination
                .order_by(order_func(order_column))
                .limit(limit)
            )

            if filter:
                stmt = filter.filter(stmt)
                # stmt = filter.sort(stmt)

            try:
                print(stmt)
                result = await session.execute(stmt)
                return result.unique().scalars().all()
            except Exception as e:
                # Log the error if needed (e.g., using logging module)
                raise Exception(f"Database query failed: {str(e)}")

    async def find_nearest(
        self,
        y_coord: float,
        x_coord: float,
        limit: int = 10,
        max_distance_meters: float | None = None,
        **filters
    ) -> list[SportObject]:
        user_point = ST_SetSRID(ST_MakePoint(x_coord, y_coord), 4326)
        distance = ST_Distance(self.model.location,
                               user_point).label("distance")
        query = select(self.model, distance)

        if filters:
            query = query.filter_by(**filters)
        if max_distance_meters is not None:
            query = query.where(distance <= max_distance_meters)

        query = query.order_by(distance).limit(limit)
        result = await self.db_session.execute(query)

        nearest_objects = [row[0] for row in result.all()]
        return nearest_objects

    async def update_single(self, data: SportObjectUpdateSchema) -> SportObject:
        parsed_schema = parse_pydantic_schema(data)
        tags = parsed_schema.pop("tags", None)
        inventory = parsed_schema.pop("inventory", None)

        update_data = data.model_dump(
            exclude_none=True, exclude_unset=True)
        update_data.pop("tags", None)
        update_data.pop("inventory", None)

        stmt = select(SportObject).where(
            SportObject.id == data.id)
        row = await self.db_session.execute(stmt)
        sport_object = row.scalars().one()

        for key, value in update_data.items():
            if hasattr(sport_object, key):
                setattr(sport_object, key, value)
            else:
                # Log a warning if a field from the schema doesn't exist on the model.
                # This might indicate a mismatch between schema and model definitions.
                print(
                    f"Warning: Attribute '{key}' from update data not found on UserProfile model.")
        # Update tags
        if tags is not None:
            sport_object.tags = []
            for tag in tags:
                query = select(Sport).where(Sport.name == tag.name)
                db_tag = (await self.db_session.execute(query)).scalar_one_or_none()

                if db_tag:
                    sport_object.tags.append(db_tag)

        # Update inventory

        # Update inventory
        if inventory is not None:
            # Create a map of existing inventory associations by inventory_id
            existing_inventory = {
                assoc.inventory_id: assoc for assoc in sport_object.inventory}
            new_inventory = []

            for item in inventory:
                query = select(Inventory).where(
                    Inventory.name == item.inventory.name)
                db_inventory = (await self.db_session.execute(query)).scalar_one_or_none()
                if db_inventory:
                    # Create new association
                    inventory_assoc = SportObjectInventory(
                        inventory_id=db_inventory.id,
                        sport_object_id=sport_object.id,
                        amount=item.amount,
                        inventory=db_inventory
                    )
                    new_inventory.append(inventory_assoc)
                else:
                    logging.warning(
                        f"Inventory with name {item.inventory.name} not found.")

            # Update the inventory relationship
            sport_object.inventory = new_inventory

            # Delete remaining old associations (not in the new inventory list)
            for assoc in existing_inventory.values():
                await self.db_session.delete(assoc)

        # Save changes
        try:
            self.db_session.add(sport_object)
            await self.db_session.flush()
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            logging.error(f"Transaction failed: {str(e)}")
            raise

        # Refresh to ensure relationships are loaded
        await self.db_session.refresh(sport_object)
        logging.info(f"Updated SportObject: {sport_object}")

        return sport_object
