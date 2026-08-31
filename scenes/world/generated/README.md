# Generated world sources

Everything in this directory is derived output. `tools/gen_props.gd` may replace
these files at any time.

The scenes one level up are stable editor-owned wrappers with the familiar
names. Open and save those wrapper scenes in Godot. Add hand-authored work under
their `authored_additions` node, or make property/transform overrides on stable
generated children. Regeneration updates the inherited source here while
leaving the wrapper and its overrides alone.

Do not point gameplay code at this directory. Runtime composition always uses
the wrappers in `scenes/world/`.
