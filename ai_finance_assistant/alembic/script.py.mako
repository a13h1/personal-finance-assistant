% reimport alembic.util
%!
from alembic import util
%>
<%page args="up_revision, down_revision, message"/>
"""
Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${util.format_time()}
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = None
def upgrade():
    pass

def downgrade():
    pass
