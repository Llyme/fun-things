import inspect


def get_frame(
    depth: int,
):
    frame = inspect.currentframe()
    n = 0

    while frame is not None:
        n += 1

        if n < depth:
            frame = frame.f_back
            continue

        return frame
