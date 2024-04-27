from src.sports.services import SportService
from src.sports.repository import SportRepository


def sport_service():
    return SportService(SportRepository)
