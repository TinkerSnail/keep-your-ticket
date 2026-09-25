# Dressing decals

Small things that sit on one prop and not the next: gum, stains, litter marks.
They are placed per prop as Godot Decals (the story-dressing layer in the
studio chapter plan's texture standards), never painted into a shared texture,
so six identical benches can each tell a different story.

| File | Size on the prop | From |
|---|---|---|
| `gum_green.png` | 7.5 × 6.2 cm, including its soft shadow (43 × 36 px at 576 px per metre) | Christina's painted gum, cut from the plaza bench texture on 2026-09-25; transparency from its difference against the clean wood beside it |
| `gum_pink.png` | 6.8 × 5.0 cm, with its shadow (39 × 29 px) | Christina's painted pink gum, cut from the front seat board of the plaza bench texture on 2026-09-25 |
| `gum_tan.png` | 5.0 × 5.4 cm, with its shadow (29 × 31 px) | Christina's painted old tan gum, cut from the front seat board on 2026-09-25 |

**In the game (2026-09-25):** the plaza bench's `gum` node
(`scenes/world/park_furniture/bench_gum.gd`) gives each bench its own gum when
the game starts: none to three pieces, under the seat, on the backrest's front
or on the seat top away from the seats, in a random gum colour, turned and
sized a little, seeded by where the bench stands so it stays put between
visits. It uses neutral versions of these shapes, made by
`tools/gum_shapes.py` into `assets/props/dressing/`; run that after changing
anything here.
