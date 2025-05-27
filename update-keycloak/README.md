Tool for updating roles or user permissions via the Keycloak REST API

**Case 1:** Add roles to a composite role

**Usage:**
```
  python3 update_keycloak.py --realm <realm-name> --composite_role <composite-role-name> --role-filename <filename>
```

**Arguments:**
 ```
  --realm            : Name of the Keycloak realm.
  --composite_role   : Name of the existing composite role to which new roles will be added.
  --role-filename    : Path to a text file containing a list of role names (one role per line).
```

Format of the role file (`<filename>`):
  Each line in the file should contain the name of a role to be added to the composite role.

Example content of the file:
```
  Role1
  Role2
  Role3
  ...
```

**Note:** This tool requires Keycloak credentials to authenticate.
Provide the following credentials in a `.env` file located in the same directory as the script:
```
KEYCLOAK_USERNAME=<your-username>
KEYCLOAK_PASSWORD=<your-password>
```
⚠️ Ensure that the .env file is not committed to github.