# Commands executed in this example

- Create Project structure and open in vscode

  ```bash
  api-project create --code
  ```

- Create table users

  ```bash
  api-project create:table users user
  ```

- Create enum UserRoles

  ```bash
  api-project create:enum user-roles --auto-opts regular --auto-opts staff --auto-opts superuser
  ```

- Create dto UserIn

  ```bash
  api-project create:dto users user-in
  ```
