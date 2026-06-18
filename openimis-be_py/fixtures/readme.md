# fixture

folder use to preload data into openimis

## Standard Fixture Loading

To load a standard fixture (e.g., role.json) containing predefined Role data, use:

`python manage.py loaddata role.json`

This command loads role data into the database.

### Handling Foreign Key References in Fixtures

Since RoleRight references Role via a foreign key, but fixtures may store relationships using a natural key (e.g., uuid, name), we use a custom command to resolve and replace these references with actual database IDs.
Custom Command: load_fixture_foreign_key

This command allows loading fixtures while resolving foreign key references using a specified field.
Usage:

`python manage.py load_fixture_foreign_key <fixture_file> <field_name>`

    <fixture_file>: Path to the fixture file (e.g., fixtures/core/roles-right.json)
    <field_name>: The field to use as the natural key for resolving foreign keys (e.g., uuid, name)

Example:

`python manage.py load_fixture_foreign_key fixtures/core/roles-right.json uuid`

This command:

    Reads the fixture file.
    Looks up foreign key references in the related model (e.g., Role).
    Replaces the natural key field (e.g., uuid) with the actual primary key (id).
    Loads the modified fixture into the database.

Notes:

    Ensure that the related objects exist in the database before loading fixtures that reference them.
    The command supports multiple fields as natural keys (e.g., uuid, name, etc.), as specified by the user.

### Loading Other Fixtures

For other fixtures, the standard Django loaddata command can be used:

`python manage.py loaddata <fixture_file>`

For example:

`python manage.py loaddata fixtures/core/users.json`

This ensures the fixture data is loaded directly into the database.