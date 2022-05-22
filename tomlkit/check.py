def is_tomlkit(v):
    from .container import Container
    from .container import OutOfOrderTableProxy
    from .items import Item as _Item

    if isinstance(v, _Item):
        return True
    if isinstance(v, Container):
        return True
    if isinstance(v, OutOfOrderTableProxy):
        return True
    return False
