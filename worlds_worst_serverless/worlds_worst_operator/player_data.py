from dataclasses import dataclass


@dataclass
class Player:
    """
    Class to hold player information
    """

    name: str
    character_class: str
    max_hit_points: int
    max_ex: int
    hit_points: int
    ex: int
    status_effects: list
    action: str
    enhanced: bool
    auth_token: str
    context: str
    target: str
    history: list
