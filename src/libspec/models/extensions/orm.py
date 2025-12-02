"""ORM extension models for libspec specifications.

This module defines models for object-relational mapping:
- Model definitions and relationships
- Query patterns and optimizations
- Migration and schema management
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from libspec.models.base import ExtensionModel
from pydantic import Field, RootModel


class OrmExtension(RootModel[Any]):
    root: Any = Field(
        ...,
        description='Extension for object-relational mapping: models, relationships, queries, migrations.',
        title='ORM Extension',
    )


class OnUpdate(Enum):
    CASCADE = 'CASCADE'
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    RESTRICT = 'RESTRICT'
    NO_ACTION = 'NO ACTION'


class OnDelete(Enum):
    CASCADE = 'CASCADE'
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    RESTRICT = 'RESTRICT'
    NO_ACTION = 'NO ACTION'


class ColumnSpec(ExtensionModel):
    name: str = Field(..., description='Column name')
    type: str = Field(
        ..., description="Column type (e.g., 'Integer', 'String(255)', 'JSON')"
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
    python_type: str | None = Field(None, description='Python type for this column')


class Type(Enum):
    one_to_one = 'one_to_one'
    one_to_many = 'one_to_many'
    many_to_one = 'many_to_one'
    many_to_many = 'many_to_many'


class Lazy(Enum):
    select = 'select'
    joined = 'joined'
    subquery = 'subquery'
    selectin = 'selectin'
    raise_ = 'raise'
    dynamic = 'dynamic'
    write_only = 'write_only'


class RelationshipSpec(ExtensionModel):
    name: str = Field(..., description='Relationship attribute name')
    type: Type = Field(..., description='Relationship type')
    target: str = Field(..., description='Target model name')
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


class IndexSpec(ExtensionModel):
    name: str | None = Field(None, description='Index name')
    columns: list[str] = Field(..., description='Columns in the index')
    unique: bool | None = Field(None, description='Whether index is unique')
    type: str | None = Field(
        None, description="Index type (e.g., 'btree', 'hash', 'gin', 'gist')"
    )
    where: str | None = Field(None, description='Partial index condition')
    include: list[str] | None = Field(
        None, description='Included columns (covering index)'
    )


class Type1(Enum):
    check = 'check'
    unique = 'unique'
    foreign_key = 'foreign_key'
    primary_key = 'primary_key'
    exclude = 'exclude'


class Initially(Enum):
    IMMEDIATE = 'IMMEDIATE'
    DEFERRED = 'DEFERRED'


class ConstraintSpec(ExtensionModel):
    name: str | None = Field(None, description='Constraint name')
    type: Type1 = Field(..., description='Constraint type')
    columns: list[str] | None = Field(None, description='Columns involved')
    expression: str | None = Field(None, description='Constraint expression')
    deferrable: bool | None = Field(
        None, description='Whether constraint is deferrable'
    )
    initially: Initially | None = Field(None, description='Initial constraint mode')


class Type2(Enum):
    single_table = 'single_table'
    joined = 'joined'
    concrete = 'concrete'


class PolymorphicSpec(ExtensionModel):
    type: Type2 | None = Field(None, description='Inheritance type')
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


class Pattern(Enum):
    repository = 'repository'
    active_record = 'active_record'
    data_mapper = 'data_mapper'
    query_builder = 'query_builder'
    raw_sql = 'raw_sql'


class QueryPatternSpec(ExtensionModel):
    name: str = Field(..., description='Pattern name')
    pattern: Pattern | None = Field(None, description='Query pattern type')
    method: str | None = Field(None, description='Method reference')
    description: str | None = Field(None, description='Pattern description')
    example: str | None = Field(None, description='Usage example')


class Tool(Enum):
    alembic = 'alembic'
    flyway = 'flyway'
    django = 'django'
    custom = 'custom'


class MigrationSpec(ExtensionModel):
    tool: Tool | None = Field(None, description='Migration tool')
    directory: str | None = Field(None, description='Migration directory')
    auto_generate: bool | None = Field(
        None, description='Whether auto-generation is supported'
    )
    revision_format: str | None = Field(None, description='Revision ID format')
    branching: bool | None = Field(
        None, description='Whether migration branching is supported'
    )


class Name(Enum):
    postgresql = 'postgresql'
    mysql = 'mysql'
    sqlite = 'sqlite'
    oracle = 'oracle'
    mssql = 'mssql'
    mariadb = 'mariadb'
    cockroachdb = 'cockroachdb'


class DatabaseSupportSpec(ExtensionModel):
    name: Name = Field(..., description='Database name')
    dialect: str | None = Field(None, description='SQLAlchemy dialect')
    min_version: str | None = Field(None, description='Minimum supported version')
    features: list[str] | None = Field(
        None, description='Database-specific features supported'
    )
    async_driver: str | None = Field(None, description='Async driver package')


class ModelSpec(ExtensionModel):
    name: str = Field(..., description='Model class name')
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
