# Commands executed in this example

- Create Project structure and open in vscode

  ```bash
  api-project create --code
  ```

- Create table users

  ```bash
  api-project create:table users --table-name user
  ```

- Create enum UserRoles

  ```bash
  api-project create:enum --enum-name user-roles --auto-opts regular --auto-opts staff --auto-opts superuser
  ```

- Create dto UserIn

  ```bash
  api-project create:dto users --dto-name user-in
  ```
