# API Project Generator

Simple API Structure Generator using tecnologies:

- FastAPI
- SQLAlchemy
- aiohttp
- aiomysql

## Commands

- `create`: Creates the project structure and base classes

  > Optional `--code` option auto opens code through a `code project_folder_name` command.

  ```bash
  api-project create
  ```

- `create:table`: Creates a new table in file in {project_name}/database/tables/{table_module}/{table_file}.py

  ```bash
  api-project create:table [table_module] --table-name [table_name]
  ```

- `create:dto`: Creates a new DTO file in {project_name}/dtos/{dtos_module}/{dto_name}.py

  ```bash
  api-project create:dto [dtos_module] --dto-name [dto_name]
  ```

- `create:enum`: Creates a new Enum file in {project_name}/dtos/enums/{enum_name}.py

  > The `auto-opts` option in the command can be repeated and will be used as the enum field

  ```bash
  api-project create:enum --enum-name [enum_name] --auto-opts [opt_name]
  ```

### Observations

> All filenames and foldernames are
>
> normalized automatically to snake_case.
