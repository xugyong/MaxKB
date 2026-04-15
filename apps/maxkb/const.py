# -*- coding: utf-8 -*-
#
import os

from dotenv import load_dotenv

from .conf import ConfigManager

__all__ = ['BASE_DIR', 'PROJECT_DIR', 'VERSION', 'CONFIG']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
VERSION = '2.0.0'

# Local development defaults.
# These values let MaxKB start on a developer machine without /opt/maxkb/conf.
os.environ.setdefault('MAXKB_CONFIG_TYPE', 'ENV')
os.environ.setdefault('MAXKB_DB_NAME', 'maxkb')
os.environ.setdefault('MAXKB_DB_HOST', '127.0.0.1')
os.environ.setdefault('MAXKB_DB_PORT', '5432')
os.environ.setdefault('MAXKB_DB_USER', 'root')
os.environ.setdefault('MAXKB_DB_PASSWORD', 'Password123@postgres')
os.environ.setdefault('MAXKB_REDIS_HOST', '127.0.0.1')
os.environ.setdefault('MAXKB_REDIS_PORT', '6379')
os.environ.setdefault('MAXKB_REDIS_PASSWORD', 'Password123@redis')
os.environ.setdefault('MAXKB_REDIS_DB', '0')
os.environ.setdefault('MAXKB_REDIS_MAX_CONNECTIONS', '100')
os.environ.setdefault('MAXKB_EMBEDDING_MODEL_PATH', '/opt/maxkb-app/model/embedding')
os.environ.setdefault('MAXKB_EMBEDDING_MODEL_NAME', '/opt/maxkb-app/model/embedding/shibing624_text2vec-base-chinese')
os.environ.setdefault('MAXKB_ADMIN_PATH', '/admin')
os.environ.setdefault('MAXKB_CHAT_PATH', '/chat')
os.environ.setdefault('MAXKB_SESSION_TIMEOUT', '28800')

# load environment variables from .env file
load_dotenv()
CONFIG = ConfigManager.load_user_config(root_path=PROJECT_DIR)

