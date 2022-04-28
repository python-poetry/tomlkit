def is_ppo(v):
    from datetime import date
    from datetime import datetime
    from datetime import time
    from datetime import timedelta
    PPO_TYPES = [int, bool, float, date, time, datetime, list, tuple, dict, str]
    if type(v) in PPO_TYPES:
        return True
    return False

def is_tomlkit(v):
    from .items import Item as _Item
    from .container import Container
    from .container import OutOfOrderTableProxy
    if isinstance(v, _Item):
        return True
    if isinstance(v, Container):
        return True
    if isinstance(v, OutOfOrderTableProxy):
        return True
    return False
