# docs

Images for the project README. The main one is `demo.gif`, shown at the top of [../README.md](../README.md).

## Recording demo.gif

Tool: [ScreenToGif](https://www.screentogif.com/) (free, Windows). It records a region of the screen, lets you cut frames, and exports a small GIF.

1. Start the app with a clean state: `python -m app.serve`, then open http://localhost:8000 in a browser window about 1280 x 800, zoom 100%. Close other tabs and hide the bookmarks bar.
2. In ScreenToGif, open the Recorder, set 15 fps, and fit the frame to the page content (no browser bar).
3. Record about 25 seconds:
   - click the example "what's the weather in paris tomorrow" and wait for the forecast card;
   - hover a few cells of the attention heatmap, so the row and column highlight;
   - switch to AR, click "صحيني الساعة ستة الصبح" to show the right-to-left chat and the alarm card;
   - type "set an alarm", press Enter, answer "seven am" to show the follow-up question.
4. In the editor, delete the pauses at the start and end, and remove frames where nothing moves (Edit, Remove duplicates).
5. Export as GIF (Gifski encoder, quality around 80), width 1000 to 1200 px. Aim for under 8 MB so GitHub shows it inline. If it is bigger, lower the fps to 10 or cut the recording.
6. Save it as `docs/demo.gif`, then in the README remove the `<!--` and `-->` lines around the image, so it shows.

To start straight on a command, the app accepts share links: `http://localhost:8000/?q=what's the weather in paris tomorrow&lang=en` (`lang` is `en`, `fr` or `ar`; add `&theme=dark` for dark mode).
