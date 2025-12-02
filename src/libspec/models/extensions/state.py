"""State extension models for libspec specifications.

This module defines models for state management:
- State containers and stores
- State transitions and reducers
- Immutability and persistence
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from libspec.models.base import ExtensionModel
from pydantic import Field, RootModel, conint


class StateExtension(RootModel[Any]):
    root: Any = Field(
        ...,
        description='Extension for state management: state machines, reducers, selectors, stores.',
        title='State Extension',
    )


class Type(Enum):
    redux = 'redux'
    mobx = 'mobx'
    zustand = 'zustand'
    recoil = 'recoil'
    pinia = 'pinia'
    custom = 'custom'


class ReducerSpec(ExtensionModel):
    name: str = Field(..., description='Reducer name')
    function: str | None = Field(None, description='Reducer function reference')
    handles: list[str] | None = Field(
        None, description='Action types this reducer handles'
    )
    pure: bool | None = Field(None, description='Whether reducer is pure')
    description: str | None = None


class SliceSpec(ExtensionModel):
    name: str = Field(..., description='Slice name')
    path: str | None = Field(None, description='Path in state tree')
    state_type: str | None = Field(None, description='Slice state type')
    reducers: list[ReducerSpec] | None = Field(None, description='Slice reducers')
    actions: list[str] | None = Field(None, description='Auto-generated action names')
    selectors: list[str] | None = Field(None, description='Slice selectors')
    extra_reducers: list[str] | None = Field(
        None, description='External action handlers'
    )


class Type1(Enum):
    atomic = 'atomic'
    compound = 'compound'
    parallel = 'parallel'
    final = 'final'
    history = 'history'


class MachineStateSpec(ExtensionModel):
    name: str = Field(..., description='State name')
    type: Type1 | None = Field(None, description='State type')
    entry: list[str] | None = Field(None, description='Entry actions')
    exit: list[str] | None = Field(None, description='Exit actions')
    on: dict[str, str] | None = Field(
        None, description='Event handlers (event -> transition)'
    )
    invoke: list[str] | None = Field(None, description='Invoked services in this state')
    children: list[MachineStateSpec] | None = Field(
        None, description='Child states (for compound/parallel)'
    )
    initial: str | None = Field(None, description='Initial child state')
    tags: list[str] | None = Field(None, description='State tags for querying')
    description: str | None = None


class MachineEventSpec(ExtensionModel):
    name: str = Field(..., description='Event name')
    payload_type: str | None = Field(None, description='Event payload type')
    description: str | None = None


class TransitionSpec(ExtensionModel):
    from_: str | None = Field(None, alias='from', description='Source state')
    to: str | None = Field(None, description='Target state')
    event: str | None = Field(None, description='Triggering event')
    guard: str | None = Field(None, description='Guard condition')
    actions: list[str] | None = Field(None, description='Transition actions')
    internal: bool | None = Field(
        None, description='Whether transition is internal (no exit/entry)'
    )
    description: str | None = None


class GuardSpec(ExtensionModel):
    name: str = Field(..., description='Guard name')
    function: str | None = Field(None, description='Guard function reference')
    condition: str | None = Field(None, description='Condition description')


class Type2(Enum):
    assign = 'assign'
    raise_ = 'raise'
    send = 'send'
    log = 'log'
    custom = 'custom'


class MachineActionSpec(ExtensionModel):
    name: str = Field(..., description='Action name')
    function: str | None = Field(None, description='Action function reference')
    type: Type2 | None = Field(None, description='Action type')
    description: str | None = None


class Type3(Enum):
    promise = 'promise'
    callback = 'callback'
    observable = 'observable'
    machine = 'machine'


class ServiceSpec(ExtensionModel):
    name: str = Field(..., description='Service name')
    type: Type3 | None = Field(None, description='Service type')
    src: str | None = Field(None, description='Service source/function reference')
    on_done: str | None = Field(None, description='Transition on success')
    on_error: str | None = Field(None, description='Transition on error')


class ActionSpec(ExtensionModel):
    name: str = Field(..., description='Action type name')
    type: str | None = Field(None, description='Action creator type reference')
    payload_type: str | None = Field(None, description='Payload type')
    creator: str | None = Field(None, description='Action creator function reference')
    async_: bool | None = Field(
        None, alias='async', description='Whether this is an async action/thunk'
    )
    description: str | None = None


class SelectorSpec(ExtensionModel):
    name: str = Field(..., description='Selector name')
    function: str | None = Field(None, description='Selector function reference')
    input_selectors: list[str] | None = Field(
        None, description='Input selectors (for memoization)'
    )
    return_type: str | None = Field(None, description='Return type')
    memoized: bool | None = Field(None, description='Whether selector is memoized')
    description: str | None = None


class Intercept(Enum):
    actions = 'actions'
    state = 'state'
    dispatch = 'dispatch'
    subscribe = 'subscribe'


class StateMiddlewareSpec(ExtensionModel):
    name: str = Field(..., description='Middleware name')
    type: str | None = Field(None, description='Middleware type reference')
    order: conint(ge=0) | None = Field(None, description='Execution order')
    intercepts: list[Intercept] | None = Field(
        None, description='What this middleware intercepts'
    )
    description: str | None = None


class StateShapeSpec(ExtensionModel):
    normalized: bool | None = Field(None, description='Whether state is normalized')
    entities: list[str] | None = Field(None, description='Entity types in state')
    ids_key: str | None = Field('ids', description='Key for ID arrays')
    entities_key: str | None = Field('entities', description='Key for entity maps')


class Storage(Enum):
    localStorage = 'localStorage'
    sessionStorage = 'sessionStorage'
    indexedDB = 'indexedDB'
    asyncStorage = 'asyncStorage'
    custom = 'custom'


class PersistenceSpec(ExtensionModel):
    storage: Storage | None = Field(None, description='Storage type')
    key: str | None = Field(None, description='Storage key')
    whitelist: list[str] | None = Field(None, description='Paths to persist')
    blacklist: list[str] | None = Field(None, description='Paths to exclude')
    version: conint(ge=0) | None = Field(None, description='Persistence version')
    migrate: str | None = Field(None, description='Migration function reference')


class StateTypeFields(ExtensionModel):
    state_shape: StateShapeSpec | None = None
    immutable: bool | None = Field(None, description='Whether state is immutable')
    serializable: bool | None = Field(None, description='Whether state is serializable')


class StoreSpec(ExtensionModel):
    name: str = Field(..., description='Store name')
    type: Type | None = Field(None, description='Store implementation type')
    state_type: str | None = Field(None, description='State type reference')
    initial_state: str | None = Field(
        None, description='Initial state factory reference'
    )
    reducers: list[ReducerSpec] | None = Field(None, description='Reducer functions')
    slices: list[SliceSpec] | None = Field(None, description='State slices')
    persistence: PersistenceSpec | None = None
    devtools: bool | None = Field(
        None, description='Whether devtools integration is supported'
    )
    description: str | None = None


class StateMachineSpec(ExtensionModel):
    name: str = Field(..., description='State machine name')
    type: str | None = Field(None, description='State machine class reference')
    states: list[MachineStateSpec] = Field(..., description='State definitions')
    initial: str = Field(..., description='Initial state name')
    context_type: str | None = Field(None, description='Context/extended state type')
    events: list[MachineEventSpec] | None = Field(None, description='Event definitions')
    transitions: list[TransitionSpec] | None = Field(
        None, description='Transition definitions'
    )
    guards: list[GuardSpec] | None = Field(None, description='Guard conditions')
    actions: list[MachineActionSpec] | None = Field(
        None, description='Side effect actions'
    )
    services: list[ServiceSpec] | None = Field(None, description='Invoked services')
    hierarchical: bool | None = Field(
        None, description='Whether machine has nested states'
    )
    parallel: bool | None = Field(
        None, description='Whether machine has parallel states'
    )
    description: str | None = None


class StateLibraryFields(ExtensionModel):
    stores: list[StoreSpec] | None = Field(None, description='State store definitions')
    state_machines: list[StateMachineSpec] | None = Field(
        None, description='State machine definitions'
    )
    actions: list[ActionSpec] | None = Field(None, description='Action definitions')
    selectors: list[SelectorSpec] | None = Field(
        None, description='Selector definitions'
    )
    middleware: list[StateMiddlewareSpec] | None = Field(
        None, description='State middleware'
    )


MachineStateSpec.model_rebuild()
