"""Safety extension models for libspec specifications.

This module defines models for thread safety and concurrency:
- Thread safety guarantees
- Locking and synchronization requirements
- Reentrancy and concurrency constraints
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from libspec.models.base import ExtensionModel


class SafetyMethodFields(ExtensionModel):
    thread_safe: bool | None = Field(
        None, description='Whether this method is thread-safe'
    )
    reentrant: bool | None = Field(None, description='Whether this method is reentrant')
    signal_safe: bool | None = Field(
        None, description='Whether safe to call from signal handlers'
    )
    atomic: bool | None = Field(None, description='Whether this operation is atomic')


class SafetyFunctionFields(ExtensionModel):
    thread_safe: bool | None = Field(
        None, description='Whether this function is thread-safe'
    )
    reentrant: bool | None = Field(
        None, description='Whether this function is reentrant'
    )
    signal_safe: bool | None = Field(
        None, description='Whether safe to call from signal handlers'
    )
    atomic: bool | None = Field(None, description='Whether this operation is atomic')


class ThreadSafetyMode(Enum):
    """How thread safety is achieved for a type.

    - immutable: Thread-safe through immutability
    - synchronized: Uses locks/mutexes for synchronization
    - thread_local: Each thread has its own instance
    - lock_free: Uses atomic operations without locks
    - wait_free: Lock-free with guaranteed progress
    - none: No thread safety guarantees
    """

    immutable = 'immutable'
    synchronized = 'synchronized'
    thread_local = 'thread_local'
    lock_free = 'lock_free'
    wait_free = 'wait_free'
    none = 'none'


class LockType(Enum):
    """Type of lock used for synchronization.

    - Lock: Basic mutual exclusion lock
    - RLock: Reentrant lock (same thread can acquire multiple times)
    - RWLock: Read-write lock (multiple readers, single writer)
    - Semaphore: Counting semaphore for resource pooling
    - none: No locking mechanism
    """

    Lock = 'Lock'
    RLock = 'RLock'
    RWLock = 'RWLock'
    Semaphore = 'Semaphore'
    none = 'none'


class LockGranularity(Enum):
    """Granularity level of locking mechanisms.

    - global_: Single lock for all instances (coarse-grained)
    - per_instance: Each instance has its own lock
    - per_method: Locks are scoped to individual methods
    - fine_grained: Multiple locks for different data segments
    """

    global_ = 'global'
    per_instance = 'per_instance'
    per_method = 'per_method'
    fine_grained = 'fine_grained'


class ThreadSafetySpec(ExtensionModel):
    safe: bool | None = Field(None, description='Whether the type is thread-safe')
    mode: ThreadSafetyMode | None = Field(None, description='How thread safety is achieved')
    lock_type: LockType | None = Field(
        None, description='Type of lock used (if synchronized)'
    )
    lock_granularity: LockGranularity | None = Field(
        None, description='Granularity of locking'
    )
    notes: str | None = Field(None, description='Additional thread safety notes')


class ReentrancySpec(ExtensionModel):
    reentrant: bool | None = Field(
        None, description='Whether the type/method is reentrant'
    )
    reason: str | None = Field(
        None, description="Why it's not reentrant (if applicable)"
    )
    safe_methods: list[str] | None = Field(
        None, description="Methods that are reentrant even if type isn't"
    )
    unsafe_methods: list[str] | None = Field(
        None, description='Methods that are not reentrant even if type is'
    )


class Leaks(Enum):
    """Memory leak potential classification.

    - none: No memory leaks possible
    - possible: Memory leaks may occur in certain conditions
    - managed: Leaks are tracked and managed (e.g., pools)
    - external: Leaks depend on external resource handling
    """

    none = 'none'
    possible = 'possible'
    managed = 'managed'
    external = 'external'


class Cleanup(Enum):
    """How resources are cleaned up.

    - automatic: Garbage collector handles cleanup
    - manual: User must explicitly call cleanup method
    - context_manager: Uses __enter__/__exit__ protocol
    - destructor: Cleanup in __del__ method
    - ref_counted: Reference counting triggers cleanup
    """

    automatic = 'automatic'
    manual = 'manual'
    context_manager = 'context_manager'
    destructor = 'destructor'
    ref_counted = 'ref_counted'


class MemorySafetySpec(ExtensionModel):
    leaks: Leaks | None = Field(None, description='Memory leak potential')
    cleanup: Cleanup | None = Field(None, description='How resources are cleaned up')
    weak_refs_supported: bool | None = Field(
        None, description='Whether weak references are supported'
    )
    cyclic_refs_safe: bool | None = Field(
        None, description='Whether cyclic references are handled safely'
    )


class Model(Enum):
    """Concurrency model used by the type.

    - shared_nothing: No shared state between threads/processes
    - actor: Actor model with message passing
    - csp: Communicating Sequential Processes
    - shared_memory: Shared memory with synchronization
    - stm: Software Transactional Memory
    - none: No specific concurrency model
    """

    shared_nothing = 'shared_nothing'
    actor = 'actor'
    csp = 'csp'
    shared_memory = 'shared_memory'
    stm = 'stm'
    none = 'none'


class ConcurrencyModelSpec(ExtensionModel):
    model: Model | None = Field(None, description='Concurrency model used')
    races_possible: bool | None = Field(
        None, description='Whether data races are possible'
    )
    deadlock_free: bool | None = Field(
        None, description='Whether deadlocks are impossible by design'
    )
    starvation_free: bool | None = Field(
        None, description='Whether starvation is impossible by design'
    )


class SignalSafetySpec(ExtensionModel):
    safe: bool | None = Field(None, description='Whether safe in signal handlers')
    unsafe_operations: list[str] | None = Field(
        None, description='Operations that make it unsafe'
    )


class SafetyTypeFields(ExtensionModel):
    thread_safety: ThreadSafetySpec | None = None
    reentrancy: ReentrancySpec | None = None
    memory_safety: MemorySafetySpec | None = None
    concurrency_model: ConcurrencyModelSpec | None = None
