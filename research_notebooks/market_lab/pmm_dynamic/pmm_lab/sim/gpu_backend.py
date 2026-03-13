"""GPU backend stub — not implemented in v1."""


class CupyBackend:
    """GPU array backend using CuPy. NOT IMPLEMENTED in v1."""

    def __init__(self):
        raise NotImplementedError(
            "GPU backend is not implemented in v1. Use 'cpu' backend."
        )
