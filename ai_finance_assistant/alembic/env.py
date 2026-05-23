from __future__ import with_statement
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add project path
HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
sys.path.insert(0, PROJECT_ROOT)

# Import models' MetaData object
from src.core import session_manager as sm  # noqa: E402
target_metadata = sm.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")

def get_url():
    return os.environ.get('DATABASE_URL', 'sqlite:///data/sessions.db')

def run_migrations_offline():
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
