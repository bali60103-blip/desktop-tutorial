# Work branches and evidence levels

Common baseline: d40dc1c3ed013c02851b080e4e7024ca4804217b. Existing history, main and severance-pipeline are preserved.

| Branch | Scope | Current work |
|---|---|---|
| reconstruction/stage-00-scope-audit | Source audit and prior calibration baseline | Existing commits retained |
| reconstruction/stage-01-building-facades | Building massing, lower storeys and facades | TNH 17 records; 63 min-level/shelter corrections |
| reconstruction/stage-02-entrances-equipment | Entrances, ramps and median equipment | Yanji photo-informed comparison; equipment sizes pending |
| reconstruction/stage-03-integration-validation | Integration and verification | 80-record mesh/vertical-range checks; unresolved issues |

## Evidence levels

- L0: Source collected, no registration.
- L1: Image/plan supports form; positions or dimensions still estimated.
- L2: Control points and source dimensions registered, error documented.
- L3: Geometry, circulation and camera-reference checks complete.

Levels apply to individual features, not automatically to branch names. TNH remains L1, not a measured elevation. The Yanji alternative has not been adopted in the assembly. Integration is a working branch, not a release.

Scripts/text checkpoints are backed up to GitHub. Blend files, photographs and raw inputs remain local. New scripts omit personal absolute paths and use CIVIC_MODEL_ROOT; they still depend on baseline scripts, prepared data and a Blender execution environment, and are not a standalone portable package.
