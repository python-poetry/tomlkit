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
