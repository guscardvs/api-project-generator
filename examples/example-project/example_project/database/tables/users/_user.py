from sqlalchemy import Table, Column, Integer
from example_project.database.metadata import metadata

# Add your table columns here

user = Table(
    "user", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True)
)

