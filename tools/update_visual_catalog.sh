#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
park_root=$(dirname "$script_dir")

python3 "$script_dir/visual_catalog.py" prepare
open -W -n -a /Applications/Godot.app --args --path "$park_root" tools/run.tscn -- visual_catalog_capture
python3 "$script_dir/visual_catalog.py" finalize
python3 "$script_dir/visual_catalog.py" check
