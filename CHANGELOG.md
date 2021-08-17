## 0.6.0 (2021-08-17)

### Feat

- **create:entity**: added single-file option to create:entity command

## 0.5.2 (2021-08-14)

### Fix

- **update:imports**: wrong path was passed to update_enums call

## 0.5.1 (2021-08-14)

### Fix

- **update:imports**: fixed bug where on updating enums all imports failed

## 0.5.0 (2021-08-13)

### Feat

- **commands/fix**: added command update:imports and changed import engine to prevent skipping changed files

## 0.4.1 (2021-08-09)

### Fix

- **enum**: changed auto-opts format from key = int to KEY = "key"

## 0.4.0 (2021-08-01)

### Feat

- **create:entity**: new command for creating sync/async entities automatically

## 0.3.4 (2021-08-01)

### Fix

- **dunder_provider**: added driver-types enum to dunder provider

## 0.3.3 (2021-08-01)

### Fix

- **pyproject_toml**: fixed comparison
- **postgres-support**: fixed bug in pyproject_toml creation
- **postgres-support**: changed postgres sync lib from psycopg2 to psycopg2-binary

## 0.3.1 (2021-08-01)

## 0.3.0 (2021-08-01)

### Feat

- **create:api**: now validates if folder already exists or is a file
- **create:api**: added port customization to connection, changed readme.md to conform to new api
- **create:api**: added support for postgresql drivers, reduced dependencies, fixed minor bugs in alembic files and added support for non async in DatabaseProvider

## 0.3.0a0 (2021-07-17)

## 0.2.0 (2021-07-17)

## 0.1.0 (2021-07-17)

### Feat

- **commands**: created new commands and changed old command
- **commands**: created create_table_command
- **base**: stable initial version
- **global**: initial commit setup

### Fix

- **commitizen**: added commititzen to project
- **files**: removed wrongly commited files
- **config**: fixed config sources
- **stories**: removed wrongly imported folder
