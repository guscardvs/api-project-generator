from gyver.attrs import define


@define
class ProjectFolders:
    tests_folder: str
    core_folder: str
    routes_name: str
    main_router_file: str
    main_file: str
    api_folder: str
    dependencies_name: str
    schemas_name: str
    domain_name: str
    exceptions_folder: str
    database_name: str
    alembic_folder: str
    commons: str


project_folders = ProjectFolders(
    "tests",
    "core",
    "routes",
    "routes",
    "main",
    "api",
    "dependencies",
    "schemas",
    "domain",
    "exc",
    "database",
    "migrations",
    "common",
)
