"""Hillside terraces along Christina's red lines, PROPOSAL only (2026-10-02).

Her sketch on the beach town plan: two streets wrapping round the hill across
the coast highway from the town, meeting near (98, 591), and a leg down to the
highway's east side and under it to J3 on Beach Road's climb. Pass 13 drew the
streets 15-45 m downhill of her lines because the ground rises steeply across
them; she chose "go with 1, cut terraces along my lines". This tool designs
and measures that on a scratch copy of the world terrain master:

    A  her lines exactly, all three legs streets (<= 11 %): the leg down fixes the meeting point low
    B  her two lines streets meeting as high as both can reach, the leg down public steps, and the street
       to the underpass pass 13's lower street from line 1's north end
    C  her lines kept in plan: streets as far as one wall and a short slope allow, stepped lanes beyond,
       the leg down as steps; the same street to the underpass
    D1, D2  the hill REGRADED round A's (D1) or B's (D2) streets: no ground steeper than 1:3 where it can be
       helped, lots on low terraces, blended into today's ground; the hill comes down as far as that needs

Each street gets a bench (9 m of carriageway and sidewalks, 8 x 7 m lots with
garages under on the uphill side, downhill lots on natural ground), a wall of
at most 4 m at the back of the lots and a planted 1:1 slope above it (1:1.5
compared), fill at 1:2 below. Heights are metres over the sea (Godot + 7.5).

    # 1. copy the master into <folder> and sample the copy (Blender; the real master is only copied)
    Blender --background --factory-startup --python tools/blender/world_terrain_proposals_hillside_terraces.py -- --sample <folder>
    # 2. design the variants, measure them, write the JSON (system Python)
    python3 tools/blender/world_terrain_proposals_hillside_terraces.py --design <folder>
    # 3. top view, sections, skylines, summary table (system Python, PIL)
    python3 tools/blender/world_terrain_proposals_hillside_terraces.py --plots <folder>
    # 4. the patches on the scratch copy, hash checks, obliques from the town (Blender)
    Blender --background --factory-startup --python tools/blender/world_terrain_proposals_hillside_terraces.py -- --build <folder>

Outputs go to documentation/terrain/renders/proposal_hillside_terraces_*.
Nothing touches the master, ParkPlan, the generator, the game or the maps;
the scratch folder must not be under assets/.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "hillside_terraces"))

from ht_site import MASTER, RENDERS, refuse_assets  # noqa: E402

SCRATCH_NAME = "hillside_terraces_scratch.blend"


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if len(argv) != 2 or argv[0] not in ("--sample", "--design", "--plots", "--build"):
        raise SystemExit(__doc__)
    folder = os.path.abspath(argv[1])
    refuse_assets(os.path.join(folder, SCRATCH_NAME))
    os.makedirs(folder, exist_ok=True)
    return argv[0], folder


def open_scratch(folder, fresh):
    import bpy
    scratch = os.path.join(folder, SCRATCH_NAME)
    if fresh or not os.path.exists(scratch):
        shutil.copyfile(MASTER, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    assert os.path.realpath(bpy.data.filepath) == os.path.realpath(scratch), "not on the scratch copy"
    return scratch


def main():
    mode, folder = args()
    os.makedirs(RENDERS, exist_ok=True)
    if mode == "--sample":
        open_scratch(folder, fresh=True)
        import ht_sample
        ht_sample.run(folder)
    elif mode == "--design":
        import ht_report
        ht_report.run(folder)
    elif mode == "--plots":
        import ht_draw_plan
        import ht_draw_charts
        ht_draw_plan.run(folder)
        ht_draw_charts.run(folder)
    elif mode == "--build":
        open_scratch(folder, fresh=True)
        import ht_build
        ht_build.run(folder)


if __name__ == "__main__":
    main()
