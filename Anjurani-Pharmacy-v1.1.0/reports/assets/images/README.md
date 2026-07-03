# Receipt Header Image

Replace `receipt_header.png` in this folder with the real pharmacy header
(name, contact numbers, locations — everything down to but not including
the "Name / Date" line, since that part is drawn dynamically per bill).

**Recommended size:** ~1500 x 400 px (aspect ratio ~3.75 : 1), PNG, white
or transparent background.

The exact pixel size isn't critical — the code scales the image to fit a
97mm-wide x 26mm-tall box at the top of each quarter-page receipt,
preserving aspect ratio. Just try to keep roughly this width:height ratio
so the image fills the box nicely without a lot of empty space on the
sides or top/bottom.

No code changes needed — just replace this file and regenerate a bill.
