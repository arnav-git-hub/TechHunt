"""Registry of connector implementations and their public labels."""

from connectors.base import EventConnector
from connectors.commudle import CommudleConnector
from connectors.devfolio import DevfolioConnector
from connectors.devpost import DevpostConnector
from connectors.kaggle import KaggleConnector
from connectors.luma import LumaConnector
from connectors.meetup import MeetupConnector
from connectors.mlh import MLHConnector
from connectors.mock import MockConnector
from connectors.unstop import UnstopConnector

CONNECTORS: dict[str, type[EventConnector]] = {
    "mock": MockConnector, "commudle": CommudleConnector, "devfolio": DevfolioConnector,
    "devpost": DevpostConnector, "kaggle": KaggleConnector, "luma": LumaConnector,
    "meetup": MeetupConnector, "mlh": MLHConnector, "unstop": UnstopConnector,
}
SOURCE_LABELS = {
    "mock": "TechHunt demo data", "commudle": "Commudle", "devfolio": "Devfolio",
    "devpost": "Devpost", "kaggle": "Kaggle", "luma": "Luma", "meetup": "Meetup",
    "mlh": "Major League Hacking", "unstop": "Unstop",
}
