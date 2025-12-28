# Champion splash focus analysis

A quick browser-based canvas script sampled every `splash_centered` champion portrait in `frontend/tft-images`.
The script measured the horizontal column with the highest pixel variance after normalizing the width to 200px.

Summary of the run:

- Champions inspected: 99 images.
- Average focal column (0.0 = far left, 1.0 = far right): **0.695**.
- Distribution: 77 right-heavy (>0.55), 9 center (0.45–0.55), 13 left-heavy (<0.45).
- Example focuses: Aatrox 0.91, Ahri 0.77, Ambessa 0.57, Anivia 0.58, Annie 0.46.

These values show most portraits concentrate detail on the right side, meaning default center-cropped avatars tend to miss the champion's face.
