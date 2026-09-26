"""Show reference: the greybox copies in the locked `reference` collection, on
or off, so the maquette can be compared with the model and then put away.

Only the greybox goes: the floor and the seat markers (`seat_l`, `seat_r`)
stay visible whichever way it is set, because Check measures against them and
the model stands on the floor. It is the eye in the outliner (hide in
viewport), set on each object, so the switch and the outliner always agree and
the file remembers it like any other visibility.
"""

import bpy

from . import checks


def _kept(obj):
    return obj.name.split(".")[0] == "floor" or obj.name in checks.SEAT_MARKERS


def greybox():
    """The objects the switch shows and hides (the import's empties go with
    the meshes, but only the meshes count as showing)."""
    coll = bpy.data.collections.get(checks.REFERENCE_COLLECTION)
    return [o for o in coll.all_objects if not _kept(o)] if coll else []


def has_greybox():
    return any(o.type == "MESH" for o in greybox())


def _in_view_layer(obj, view_layer):
    return view_layer.objects.get(obj.name) is obj


def _get(scene):
    view_layer = bpy.context.view_layer
    return any(not o.hide_get(view_layer=view_layer) for o in greybox()
               if o.type == "MESH" and _in_view_layer(o, view_layer))


def _set(scene, value):
    view_layer = bpy.context.view_layer
    if value:
        # A hidden collection would keep them hidden whatever the objects say.
        lc = view_layer.layer_collection.children.get(checks.REFERENCE_COLLECTION)
        if lc is not None and lc.hide_viewport:
            lc.hide_viewport = False
    for o in greybox():
        if _in_view_layer(o, view_layer):
            o.hide_set(not value, view_layer=view_layer)


def register():
    bpy.types.Scene.kyt_show_reference = bpy.props.BoolProperty(
        name="Show reference", get=_get, set=_set,
        description="Show or hide the greybox copies in the locked 'reference' collection. "
                    "The floor and the seat markers stay visible")


def unregister():
    del bpy.types.Scene.kyt_show_reference
