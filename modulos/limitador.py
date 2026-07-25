# -*- coding: utf-8 -*-
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000 per day", "1000 per hour"],
    storage_uri="memory://"
)
