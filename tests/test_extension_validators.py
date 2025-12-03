"""Tests for extension model validators.

These tests verify Pydantic model validators for extension models
produce correct validation results for both valid and invalid inputs.
"""

from __future__ import annotations

import warnings

import pytest
from pydantic import ValidationError

from libspec.models.extensions.async_ import (
    CancellationMode,
    CancellationSpec,
    Priority,
    SchedulingSpec,
)
from libspec.models.extensions.data import EvaluationStrategySpec
from libspec.models.extensions.orm import (
    ColumnSpec,
    Lazy,
    RelationshipSpec,
    RelationshipType,
)
from libspec.models.extensions.testing import FactoryFieldSpec, ParametrizeSpec
from libspec.models.extensions.versioning import (
    DeprecationSpec,
    VersioningMethodFields,
    VersioningTypeFields,
)


# =============================================================================
# ORM Extension Validators
# =============================================================================


class TestColumnSpecAutoIncrement:
    """Test ColumnSpec auto_increment validator."""

    def test_auto_increment_with_primary_key_no_warning(self) -> None:
        """auto_increment with primary_key=True should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            col = ColumnSpec(
                name="id",
                type="Integer",
                primary_key=True,
                auto_increment=True,
                nullable=False,
            )
            assert col.auto_increment is True
            assert col.primary_key is True
            # Should not warn
            assert len([x for x in w if "auto_increment" in str(x.message)]) == 0

    def test_auto_increment_without_primary_key_warns(self) -> None:
        """auto_increment without primary_key should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            col = ColumnSpec(
                name="counter",
                type="Integer",
                auto_increment=True,
                nullable=True,
            )
            assert col.auto_increment is True
            # Should warn about auto_increment without primary_key
            auto_warns = [x for x in w if "auto_increment" in str(x.message)]
            assert len(auto_warns) == 1
            assert "primary_key is not True" in str(auto_warns[0].message)


class TestRelationshipSpecLazyUselist:
    """Test RelationshipSpec lazy/uselist validator."""

    def test_lazy_dynamic_with_uselist_true_valid(self) -> None:
        """lazy='dynamic' with uselist=True should be valid."""
        rel = RelationshipSpec(
            name="items",
            type=RelationshipType.one_to_many,
            target="Item",
            lazy=Lazy.dynamic,
            uselist=True,
        )
        assert rel.lazy == Lazy.dynamic
        assert rel.uselist is True

    def test_lazy_dynamic_with_uselist_false_error(self) -> None:
        """lazy='dynamic' with uselist=False should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            RelationshipSpec(
                name="item",
                type=RelationshipType.one_to_one,
                target="Item",
                lazy=Lazy.dynamic,
                uselist=False,
            )
        assert "lazy='dynamic'" in str(exc_info.value)
        assert "uselist=True" in str(exc_info.value)

    def test_lazy_dynamic_with_uselist_none_valid(self) -> None:
        """lazy='dynamic' with uselist=None should be valid."""
        rel = RelationshipSpec(
            name="items",
            type=RelationshipType.one_to_many,
            target="Item",
            lazy=Lazy.dynamic,
        )
        assert rel.lazy == Lazy.dynamic
        assert rel.uselist is None


class TestRelationshipSpecForeignKeys:
    """Test RelationshipSpec many_to_one foreign_keys validator."""

    def test_many_to_one_with_foreign_keys_no_warning(self) -> None:
        """many_to_one with foreign_keys should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            rel = RelationshipSpec(
                name="parent",
                type=RelationshipType.many_to_one,
                target="Parent",
                foreign_keys=["parent_id"],
            )
            assert rel.type == RelationshipType.many_to_one
            # Should not warn
            fk_warns = [x for x in w if "foreign_keys" in str(x.message)]
            assert len(fk_warns) == 0

    def test_many_to_one_without_foreign_keys_warns(self) -> None:
        """many_to_one without foreign_keys should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            rel = RelationshipSpec(
                name="parent",
                type=RelationshipType.many_to_one,
                target="Parent",
            )
            assert rel.type == RelationshipType.many_to_one
            # Should warn
            fk_warns = [x for x in w if "foreign_keys" in str(x.message)]
            assert len(fk_warns) == 1


# =============================================================================
# Testing Extension Validators
# =============================================================================


class TestFactoryFieldSpecExclusivity:
    """Test FactoryFieldSpec subfactory/default exclusivity validator."""

    def test_subfactory_without_default_valid(self) -> None:
        """subfactory without default should be valid."""
        field = FactoryFieldSpec(name="user", subfactory="UserFactory")
        assert field.subfactory == "UserFactory"
        assert field.default is None

    def test_default_without_subfactory_valid(self) -> None:
        """default without subfactory should be valid."""
        field = FactoryFieldSpec(name="status", default="active")
        assert field.default == "active"
        assert field.subfactory is None

    def test_subfactory_and_default_error(self) -> None:
        """subfactory with default should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            FactoryFieldSpec(name="user", subfactory="UserFactory", default="default_user")
        assert "subfactory" in str(exc_info.value)
        assert "default" in str(exc_info.value)


class TestParametrizeSpecIndirectParams:
    """Test ParametrizeSpec indirect params validator."""

    def test_indirect_params_in_params_valid(self) -> None:
        """indirect params that exist in params should be valid."""
        spec = ParametrizeSpec(
            name="auth_test",
            params=["user", "password", "expected"],
            indirect=["user"],
        )
        assert "user" in spec.indirect
        assert "user" in spec.params

    def test_indirect_params_not_in_params_error(self) -> None:
        """indirect params not in params should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            ParametrizeSpec(
                name="auth_test",
                params=["user", "password"],
                indirect=["nonexistent"],
            )
        assert "indirect params not in params list" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_empty_indirect_valid(self) -> None:
        """empty indirect should be valid."""
        spec = ParametrizeSpec(
            name="simple_test",
            params=["x", "y"],
            indirect=[],
        )
        assert spec.indirect == []


# =============================================================================
# Data Extension Validators
# =============================================================================


class TestEvaluationStrategySpecDisjoint:
    """Test EvaluationStrategySpec lazy/eager disjoint validator."""

    def test_lazy_and_eager_disjoint_valid(self) -> None:
        """lazy_operations and eager_triggers with no overlap should be valid."""
        spec = EvaluationStrategySpec(
            lazy_operations=["filter", "map"],
            eager_triggers=["collect", "count"],
        )
        assert "filter" in spec.lazy_operations
        assert "collect" in spec.eager_triggers

    def test_lazy_and_eager_overlap_error(self) -> None:
        """lazy_operations and eager_triggers with overlap should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            EvaluationStrategySpec(
                lazy_operations=["filter", "map", "sort"],
                eager_triggers=["collect", "sort"],  # 'sort' overlaps
            )
        assert "cannot be both lazy and eager" in str(exc_info.value)
        assert "sort" in str(exc_info.value)

    def test_lazy_only_valid(self) -> None:
        """only lazy_operations should be valid."""
        spec = EvaluationStrategySpec(lazy_operations=["filter", "map"])
        assert spec.eager_triggers is None

    def test_eager_only_valid(self) -> None:
        """only eager_triggers should be valid."""
        spec = EvaluationStrategySpec(eager_triggers=["collect", "count"])
        assert spec.lazy_operations is None


# =============================================================================
# Async Extension Validators
# =============================================================================


class TestCancellationSpecPropagates:
    """Test CancellationSpec propagates/mode validator."""

    def test_propagates_with_cooperative_mode_valid(self) -> None:
        """propagates=True with cooperative mode should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spec = CancellationSpec(mode=CancellationMode.cooperative, propagates=True)
            assert spec.propagates is True
            prop_warns = [x for x in w if "propagates" in str(x.message)]
            assert len(prop_warns) == 0

    def test_propagates_with_none_mode_warns(self) -> None:
        """propagates=True with mode='none' should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spec = CancellationSpec(mode=CancellationMode.none, propagates=True)
            assert spec.mode == CancellationMode.none
            prop_warns = [x for x in w if "propagates" in str(x.message)]
            assert len(prop_warns) == 1
            assert "no effect" in str(prop_warns[0].message)

    def test_propagates_false_with_none_mode_no_warning(self) -> None:
        """propagates=False with mode='none' should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spec = CancellationSpec(mode=CancellationMode.none, propagates=False)
            assert spec.propagates is False
            prop_warns = [x for x in w if "propagates" in str(x.message)]
            assert len(prop_warns) == 0


class TestSchedulingSpecRealtimePreemptible:
    """Test SchedulingSpec realtime/preemptible validator."""

    def test_realtime_with_preemptible_false_valid(self) -> None:
        """realtime priority with preemptible=False should be valid."""
        spec = SchedulingSpec(priority=Priority.realtime, preemptible=False)
        assert spec.priority == Priority.realtime
        assert spec.preemptible is False

    def test_realtime_with_preemptible_true_error(self) -> None:
        """realtime priority with preemptible=True should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            SchedulingSpec(priority=Priority.realtime, preemptible=True)
        assert "realtime priority" in str(exc_info.value)
        assert "preemptible=True" in str(exc_info.value)

    def test_high_priority_with_preemptible_true_valid(self) -> None:
        """non-realtime priority with preemptible=True should be valid."""
        spec = SchedulingSpec(priority=Priority.high, preemptible=True)
        assert spec.priority == Priority.high
        assert spec.preemptible is True


# =============================================================================
# Versioning Extension Validators
# =============================================================================


class TestVersioningTypeFieldsOrdering:
    """Test VersioningTypeFields version ordering validator."""

    def test_valid_ordering_no_warning(self) -> None:
        """Valid version ordering should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fields = VersioningTypeFields(
                since="1.0",
                deprecated_since="2.0",
                removed_in="3.0",
            )
            assert fields.since == "1.0"
            version_warns = [x for x in w if "should be earlier" in str(x.message)]
            assert len(version_warns) == 0

    def test_since_after_deprecated_warns(self) -> None:
        """since >= deprecated_since should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            VersioningTypeFields(
                since="2.0",
                deprecated_since="1.0",
            )
            version_warns = [x for x in w if "should be earlier" in str(x.message)]
            assert len(version_warns) == 1

    def test_deprecated_after_removed_warns(self) -> None:
        """deprecated_since >= removed_in should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            VersioningTypeFields(
                deprecated_since="3.0",
                removed_in="2.0",
            )
            version_warns = [x for x in w if "should be earlier" in str(x.message)]
            assert len(version_warns) == 1


class TestVersioningMethodFieldsOrdering:
    """Test VersioningMethodFields version ordering validator."""

    def test_valid_ordering_no_warning(self) -> None:
        """Valid version ordering should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fields = VersioningMethodFields(
                since="1.0.0",
                deprecated_since="1.5.0",
                removed_in="2.0.0",
            )
            assert fields.since == "1.0.0"
            version_warns = [x for x in w if "should be earlier" in str(x.message)]
            assert len(version_warns) == 0


class TestDeprecationSpecOrdering:
    """Test DeprecationSpec version ordering validator."""

    def test_valid_ordering_no_warning(self) -> None:
        """Valid version ordering should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spec = DeprecationSpec(
                target="#/functions/old_function",
                since="1.0",
                removed_in="2.0",
            )
            assert spec.since == "1.0"
            version_warns = [x for x in w if "should be earlier" in str(x.message)]
            assert len(version_warns) == 0

    def test_since_after_removed_warns(self) -> None:
        """since >= removed_in should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            DeprecationSpec(
                target="#/functions/old_function",
                since="2.0",
                removed_in="1.0",
            )
            version_warns = [x for x in w if "should be earlier" in str(x.message)]
            assert len(version_warns) == 1
