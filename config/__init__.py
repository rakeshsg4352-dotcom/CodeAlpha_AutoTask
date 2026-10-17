"""
Config package initialization.
Sets up PyMySQL as the MySQLdb driver for Django ORM,
and ensures seamless compatibility with standard XAMPP MariaDB (10.4+):
- Bypasses strict minimum database version assertions
- Disables 'INSERT ... RETURNING' syntax (which requires MariaDB 10.5+)
"""
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Patch Django's database version check to support standard XAMPP MariaDB 10.4.x
try:
    from django.db.backends.base.base import BaseDatabaseWrapper
    BaseDatabaseWrapper.check_database_version_supported = lambda self: None
except Exception:
    pass

# MariaDB 10.4.x (standard XAMPP) does not support RETURNING syntax
try:
    from django.db.backends.mysql.features import DatabaseFeatures
    DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
    DatabaseFeatures.can_return_rows_from_bulk_insert = property(lambda self: False)
except Exception:
    pass
