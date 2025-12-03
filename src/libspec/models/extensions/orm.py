"""ORM extension models for libspec specifications.

This module defines models for object-relational mapping:
- Model definitions and relationships
- Query patterns and optimizations
- Migration and schema management
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from libspec.models.base import ExtensionModel
from libspec.models.types import FunctionReference, LocalPath, NonEmptyStr, TypeAnnotationStr


class OnUpdate(str, Enum):
    """Foreign key ON UPDATE referential action.

    Values use lowercase with underscores, mapping to SQL keywords:
    - cascade: Update child rows when parent key changes (SQL: CASCADE)
    - set_null: Set child foreign key to NULL (SQL: SET NULL)
    - set_default: Set child foreign key to default value (SQL: SET DEFAULT)
    - restrict: Prevent update if children exist (SQL: RESTRICT)
    - no_action: Defer check until transaction end (SQL: NO ACTION)
    """

    cascade = 'cascade'
    set_null = 'set_null'
    set_default = 'set_default'
    restrict = 'restrict'
    no_action = 'no_action'


class OnDelete(str, Enum):
    """Foreign key ON DELETE referential action.

    Values use lowercase with underscores, mapping to SQL keywords:
    - cascade: Delete child rows when parent is deleted (SQL: CASCADE)
    - set_null: Set child foreign key to NULL (SQL: SET NULL)
    - set_default: Set child foreign key to default value (SQL: SET DEFAULT)
    - restrict: Prevent deletion if children exist (SQL: RESTRICT)
    - no_action: Defer check until transaction end (SQL: NO ACTION)
    """

    cascade = 'cascade'
    set_null = 'set_null'
    set_default = 'set_default'
    restrict = 'restrict'
    no_action = 'no_action'


class ColumnSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Column name')
    type: TypeAnnotationStr = Field(
        default=..., description="Column type (e.g., 'Integer', 'String(255)', 'JSON')"
    )
    nullable: bool | None = Field(True, description='Whether column allows NULL')
    primary_key: bool | None = Field(None, description='Whether this is a primary key')
    auto_increment: bool | None = Field(
        None, description='Whether value auto-increments'
    )
    default: Any | None = Field(None, description='Default value or callable')
    server_default: str | None = Field(
        None, description='Server-side default expression'
    )
    unique: bool | None = Field(None, description='Whether value must be unique')
    index: bool | None = Field(None, description='Whether column is indexed')
    foreign_key: str | None = Field(
        None, description="Foreign key reference (e.g., 'users.id')"
    )
    on_update: OnUpdate | None = Field(None, description='ON UPDATE action')
    on_delete: OnDelete | None = Field(None, description='ON DELETE action')
    check: str | None = Field(None, description='CHECK constraint expression')
    comment: str | None = Field(None, description='Column comment')
    python_type: TypeAnnotationStr | None = Field(
        None, description='Python type for this column'
    )

    @model_validator(mode='after')
    def validate_column_constraints(self) -> 'ColumnSpec':
        """Validate column constraint consistency."""
        # Primary keys cannot also be foreign keys (in the same column definition)
        if self.primary_key and self.foreign_key:
            raise ValueError(
                f"Column {self.name!r} cannot be both a primary key and a foreign key. "
                "Use a composite primary key with a separate foreign key constraint instead."
            )
        # Primary keys should not be nullable
        if self.primary_key and self.nullable:
            raise ValueError(
                f"Primary key column {self.name!r} cannot be nullable"
            )
        # on_update/on_delete only make sense with foreign_key
        if (self.on_update or self.on_delete) and not self.foreign_key:
            raise ValueError(
                f"Column {self.name!r} has on_update/on_delete without foreign_key"
            )
        return self


class RelationshipType(str, Enum):
    """ORM relationship cardinality.

    - one_to_one: Each parent has exactly one child
    - one_to_many: Each parent has zero or more children
    - many_to_one: Many children reference one parent (foreign key side)
    - many_to_many: Many-to-many via association table
    """

    one_to_one = 'one_to_one'
    one_to_many = 'one_to_many'
    many_to_one = 'many_to_one'
    many_to_many = 'many_to_many'


class Lazy(str, Enum):
    """SQLAlchemy relationship loading strategy.

    - select: Lazy load with separate SELECT on access
    - joined: Eager load with JOIN in same query
    - subquery: Eager load with subquery
    - selectin: Eager load with SELECT IN clause
    - raise_: Raise exception if relationship accessed (prevents N+1)
    - dynamic: Return query object instead of loading
    - write_only: Write-only relationship (no loading)
    """

    select = 'select'
    joined = 'joined'
    subquery = 'subquery'
    selectin = 'selectin'
    raise_ = 'raise'
    dynamic = 'dynamic'
    write_only = 'write_only'


class RelationshipSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Relationship attribute name')
    type: RelationshipType = Field(default=..., description='Relationship type')
    target: str = Field(default=..., description='Target model name')
    back_populates: str | None = Field(
        None, description='Back-reference attribute on target'
    )
    secondary: str | None = Field(
        None, description='Association table (for many-to-many)'
    )
    foreign_keys: list[str] | None = Field(None, description='Explicit foreign keys')
    lazy: Lazy | None = Field(None, description='Loading strategy')
    cascade: str | None = Field(
        None, description="Cascade options (e.g., 'all, delete-orphan')"
    )
    uselist: bool | None = Field(None, description='Whether relationship returns list')
    viewonly: bool | None = Field(None, description='Whether relationship is read-only')
    order_by: str | None = Field(None, description='Default ordering')

    @model_validator(mode='after')
    def validate_relationship_config(self) -> 'RelationshipSpec':
        """Validate relationship configuration consistency."""
        if self.secondary is not None and self.type != RelationshipType.many_to_many:
            raise ValueError(
                f"Relationship '{self.name}' has 'secondary' table but type is "
                f"'{self.type.value}'; secondary only applies to many_to_many"
            )
        return self


class IndexSpec(ExtensionModel):
    name: str | None = Field(default=None, description='Index name')
    columns: list[str] = Field(default=..., description='Columns in the index')
    unique: bool | None = Field(None, description='Whether index is unique')
    type: str | None = Field(
        None, description="Index type (e.g., 'btree', 'hash', 'gin', 'gist')"
    )
    where: str | None = Field(None, description='Partial index condition')
    include: list[str] | None = Field(
        None, description='Included columns (covering index)'
    )


class ConstraintType(str, Enum):
    """Database table constraint type.

    - check: CHECK constraint on column values
    - unique: UNIQUE constraint
    - foreign_key: FOREIGN KEY constraint
    - primary_key: PRIMARY KEY constraint
    - exclude: PostgreSQL EXCLUDE constraint
    """

    check = 'check'
    unique = 'unique'
    foreign_key = 'foreign_key'
    primary_key = 'primary_key'
    exclude = 'exclude'


class Initially(str, Enum):
    """When deferrable constraints are checked.

    - immediate: Check constraint at statement end
    - deferred: Check constraint at transaction commit
    """

    IMMEDIATE = 'immediate'
    DEFERRED = 'deferred'


class ConstraintSpec(ExtensionModel):
    name: str | None = Field(default=None, description='Constraint name')
    type: ConstraintType = Field(default=..., description='Constraint type')
    columns: list[str] | None = Field(None, description='Columns involved')
    expression: str | None = Field(None, description='Constraint expression')
    deferrable: bool | None = Field(
        None, description='Whether constraint is deferrable'
    )
    initially: Initially | None = Field(None, description='Initial constraint mode')


class InheritanceType(str, Enum):
    """SQLAlchemy model inheritance strategy.

    - single_table: All classes in one table with discriminator
    - joined: Each class has its own table, joined on primary key
    - concrete: Each concrete class has its own complete table
    """

    single_table = 'single_table'
    joined = 'joined'
    concrete = 'concrete'


class PolymorphicSpec(ExtensionModel):
    type: InheritanceType | None = Field(None, description='Inheritance type')
    discriminator: str | None = Field(None, description='Discriminator column')
    identity: str | None = Field(None, description='Polymorphic identity value')


class TimestampSpec(ExtensionModel):
    created_at: str | None = Field(None, description='Created timestamp column name')
    updated_at: str | None = Field(None, description='Updated timestamp column name')
    deleted_at: str | None = Field(
        None, description='Soft delete timestamp column name'
    )
    timezone: bool | None = Field(
        None, description='Whether timestamps include timezone'
    )


class SessionManagementSpec(ExtensionModel):
    scoped_session: bool | None = Field(
        None, description='Whether scoped sessions are used'
    )
    autoflush: bool | None = Field(None, description='Default autoflush setting')
    autocommit: bool | None = Field(None, description='Default autocommit setting')
    expire_on_commit: bool | None = Field(
        None, description='Whether objects expire on commit'
    )
    context_manager: bool | None = Field(
        None, description='Whether session supports context manager'
    )
    async_support: bool | None = Field(
        None, description='Whether async sessions are supported'
    )


class Pattern(str, Enum):
    """Database query/persistence pattern.

    - repository: Repository pattern (abstraction over data access)
    - active_record: Objects know how to persist themselves
    - data_mapper: Separate mapper handles persistence
    - query_builder: Fluent query construction
    - raw_sql: Direct SQL execution
    """

    repository = 'repository'
    active_record = 'active_record'
    data_mapper = 'data_mapper'
    query_builder = 'query_builder'
    raw_sql = 'raw_sql'


class QueryPatternSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Pattern name')
    pattern: Pattern | None = Field(None, description='Query pattern type')
    method: FunctionReference | None = Field(None, description='Method reference')
    description: str | None = Field(None, description='Pattern description')
    example: str | None = Field(None, description='Usage example')


class Tool(str, Enum):
    """Database migration tool.

    - alembic: SQLAlchemy's Alembic
    - flyway: Flyway (Java/general)
    - django: Django's built-in migrations
    - custom: Custom migration implementation
    """

    alembic = 'alembic'
    flyway = 'flyway'
    django = 'django'
    custom = 'custom'


class MigrationSpec(ExtensionModel):
    tool: Tool | None = Field(None, description='Migration tool')
    directory: LocalPath | None = Field(None, description='Migration directory')
    auto_generate: bool | None = Field(
        None, description='Whether auto-generation is supported'
    )
    revision_format: str | None = Field(None, description='Revision ID format')
    branching: bool | None = Field(
        None, description='Whether migration branching is supported'
    )


class Name(str, Enum):
    """Supported database system.

    - postgresql: PostgreSQL
    - mysql: MySQL
    - sqlite: SQLite
    - oracle: Oracle Database
    - mssql: Microsoft SQL Server
    - mariadb: MariaDB
    - cockroachdb: CockroachDB
    """

    postgresql = 'postgresql'
    mysql = 'mysql'
    sqlite = 'sqlite'
    oracle = 'oracle'
    mssql = 'mssql'
    mariadb = 'mariadb'
    cockroachdb = 'cockroachdb'


class DatabaseSupportSpec(ExtensionModel):
    name: Name = Field(default=..., description='Database name')
    dialect: str | None = Field(None, description='SQLAlchemy dialect')
    min_version: str | None = Field(None, description='Minimum supported version')
    features: list[str] | None = Field(
        None, description='Database-specific features supported'
    )
    async_driver: str | None = Field(None, description='Async driver package')


class ModelSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Model class name')
    table: str | None = Field(None, description='Database table name')
    schema_: str | None = Field(
        None, alias='schema', description='Database schema (if applicable)'
    )
    columns: list[ColumnSpec] | None = Field(None, description='Column definitions')
    primary_key: list[str] | None = Field(None, description='Primary key columns')
    relationships: list[RelationshipSpec] | None = Field(
        None, description='Relationships to other models'
    )
    indexes: list[IndexSpec] | None = Field(None, description='Index definitions')
    constraints: list[ConstraintSpec] | None = Field(
        None, description='Table constraints'
    )
    mixins: list[str] | None = Field(None, description='Mixin classes applied')
    polymorphic: PolymorphicSpec | None = None
    soft_delete: bool | None = Field(None, description='Whether soft delete is enabled')
    timestamps: TimestampSpec | None = None
    description: str | None = None


class ORMLibraryFields(ExtensionModel):
    models: list[ModelSpec] | None = Field(None, description='ORM model definitions')
    session_management: SessionManagementSpec | None = None
    query_patterns: list[QueryPatternSpec] | None = Field(
        None, description='Common query patterns'
    )
    migrations: MigrationSpec | None = None
    database_support: list[DatabaseSupportSpec] | None = Field(
        None, description='Supported databases'
    )
