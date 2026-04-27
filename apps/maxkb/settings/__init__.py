# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： __init__.py.py
    @date：2025/4/11 16:39
    @desc:
"""
from .base import *
from .logging import *
from .auth import *

from common.utils.logger import maxkb_logger

import os

if os.environ.get('MINI_PROGRAM_LIGHTWEIGHT') != '1':
    from .lib import *
    from .mem import *
