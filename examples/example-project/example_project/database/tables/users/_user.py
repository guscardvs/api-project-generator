from example_project.database.metadata import metadata
from sqlalchemy import Column, Integer, Table

# Add your table columns here

user = Table(
    "user", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True)
)

