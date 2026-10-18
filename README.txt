HOI4 MP Name Forge v3
=====================

Open index.html in a browser. It works offline and needs no install.

What's new since v2
- Every sprite in the game (32,090 IDs), not just texticons.gfx:
  vanilla + integrated_dlc + dlc folders, with a preview for each.
- Each sprite is tagged "always loaded" (legacy_lazy_load = no, ~4.8k IDs) or "lazy".
  Always-loaded sprites are the ones most likely to render in names. The library shows them by default.
- Real in-game size (w x h) on each card. Anything over 128 px is flagged as huge.
- Test tracking: mark sprites as works / broken / favorite (saved in your browser),
  copy numbered test batches, and export your results.
- Flags tab (untested): @TAG and control-character variants for all 364 country tags.
- Lab: wrap any text in any control character (DC2, DC4, ...) for testing.
- Simple layout: light/dark follows your system, and the header button toggles it.

Encoding
- Icon:  DC3 (U+0013) + ID without GFX_ + DC3
- Color: DC1 (U+0011) + code + text + DC1 + !

Confirmed: TC_heavy_tank_artillery_chassis_fra (the French heavy SPG blueprint, 508x248) works,
so the v2 claim that only texticons work was wrong.

Files
- index.html        the tool
- catalog-data.js   generated sprite catalog (id, file, source, frames, size, load flag)
- atlas/            WebP preview sheets (64 px cells) + flags.webp
- tools/            scripts to regenerate the catalog after a game patch (Python + Pillow):
                    scan.py <game> catalog.json -> thumbs.py <game> catalog.json atlas -> build_data.py

Disclaimer
Hearts of Iron IV and all game art in atlas/ (icons, blueprints, flags) belong to Paradox Interactive.
They are extracted from the game for preview purposes only. This is an unofficial, non-commercial fan tool.
