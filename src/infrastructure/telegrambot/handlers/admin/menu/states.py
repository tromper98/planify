from enum import Enum

class MenuLevel(Enum):
    MAIN = 'main'
    SLOTS = 'slots'
    APPOINTMENTS = 'appointments'
    ADMIN = 'admin'
    SETTINGS = 'settings'

class NavigationState:

    @staticmethod
    def get_back_target(current_level: MenuLevel) -> MenuLevel:
        navigation_map = {
            MenuLevel.SLOTS: MenuLevel.MAIN,
            MenuLevel.APPOINTMENTS: MenuLevel.MAIN,
            MenuLevel.ADMIN: MenuLevel.MAIN,
            MenuLevel.SETTINGS: MenuLevel.MAIN,
            MenuLevel.MAIN: None
        }
        return navigation_map.get(current_level)


    @staticmethod
    def get_breadcrumbs(current_level: MenuLevel) -> list:
        breadcrumbs = []
        level = current_level

        while level:
            breadcrumbs.insert(0, level)
            level = NavigationState.get_back_target(level)

        return breadcrumbs