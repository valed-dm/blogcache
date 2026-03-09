"""Shared rate limiter instance for the application.

A single Limiter is used app-wide so that route-specific limits (e.g. 10/minute
on POST /posts/) are applied via the same instance that is registered in
app.state.limiter, as required by SlowAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
