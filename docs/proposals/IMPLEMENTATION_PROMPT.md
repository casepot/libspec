# Libspec Schema Extension Implementation

## Context

While hardening `weave.json` (a comprehensive library spec for an actor-based async runtime), I discovered that the libspec schema is too restrictive for real-world use. Rather than strip valuable information to make the spec validate, I've documented the gaps and written extension proposals.

## Files to Review

1. **Proposals**: `/Users/case/projects/libspec/docs/proposals/`
   - `README.md` - Overview and priority ranking
   - `001-principle-metadata.md` - Add `category`, `refs`, `source` to Principle
   - `002-method-decorators.md` - Add `decorators` field to Method/FunctionDef
   - `003-parameterized-cross-references.md` - Support `#/types/Handle[T]` syntax
   - `004-external-type-references.md` - Support `pydantic:BaseModel` syntax
   - `005-generic-param-descriptions.md` - Add `description` to GenericParam
   - `006-maturity-proposed-stage.md` - Add `proposed` to EntityMaturity enum

2. **Test case**: `/Users/case/projects/threads/specs/weave.json`
   - 17,755 lines, comprehensive real-world spec
   - Contains all the patterns that currently fail validation

3. **Schema source**: `/Users/case/projects/libspec/src/libspec/models/`
   - `core.py` - Principle, GenericParam, Method, FunctionDef, TypeDef
   - `types.py` - EntityMaturity enum, CrossReference pattern

## What I Learned

### High-Value Extensions (implement first)

1. **Principle metadata** (001) - Every principle in weave.json has `category`, `refs`, `source`. These provide:
   - Organization (group by domain)
   - Traceability (link to governed entities)
   - Provenance (where the principle came from)

2. **External type references** (004) - Many types inherit from `pydantic.BaseModel` or implement `typing.Protocol`. Removing these loses critical inheritance information.

3. **Generic param descriptions** (005) - Type parameters like `P` and `T` have semantic meaning ("parameter spec", "return type") that's valuable documentation.

### Medium-Value Extensions

4. **Method decorators** (002) - `@asynccontextmanager` and `@contextmanager` are semantic, not syntactic. A method being a context manager changes how you use it.

5. **Parameterized cross-refs** (003) - `GeneratorHandle` extends `Handle[ReturnT]`, not just `Handle`. The type parameter binding matters for understanding the inheritance.

### Low-Value Extensions

6. **Proposed maturity** (006) - Workaround exists (use `specified`), but having `proposed` better matches real development workflows.

## Design Recommendations

1. **Keep schemas permissive by default** - Use `extra = "allow"` or explicit optional fields rather than rejecting unknown fields. Specs evolve faster than schemas.

2. **Cross-reference pattern needs rethinking**:
   - Current: `^([a-z_][a-z0-9_.]*)?#/(types|functions|features|principles|modules)/[a-zA-Z_][a-zA-Z0-9_-]*$`
   - Needs: Support for type parameters `[T]` and external refs `package:Type`
   - Consider a more flexible pattern or separate field types

3. **Signature field is overloaded** - Currently expected to be `(params) -> return` but real specs include `async`, `def name`, decorators. Either:
   - Accept full Python syntax in signature, OR
   - Add separate `decorators`, `async` (already exists), and ensure `name` is used

## Task

Plan and implement the libspec schema updates to support weave.json. Approach:

1. **Read the proposals** in `/Users/case/projects/libspec/docs/proposals/`
2. **Run validation** on weave.json to see current errors: `libspec --spec /Users/case/projects/threads/specs/weave.json validate`
3. **Implement in priority order**:
   - 001 (Principle metadata) - unblocks 180 errors
   - 004 (External type refs) - unblocks ~14 errors
   - 005 (Generic param descriptions) - unblocks ~11 errors
   - 002 (Method decorators) - semantic improvement
   - 003 (Parameterized cross-refs) - precision improvement
   - 006 (Proposed maturity) - minor addition
4. **Test iteratively** - After each change, validate weave.json and run tests
5. **Update JSON schemas** if they exist alongside Pydantic models

The goal is for `libspec --spec /Users/case/projects/threads/specs/weave.json validate` to pass with zero errors while preserving all the rich information in the spec.
