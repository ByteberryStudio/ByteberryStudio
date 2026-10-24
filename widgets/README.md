# Profile widgets

`build_profile.py` draws the animated SVGs in `../assets` and the avatar PNG.

- Fonts: Unbounded, Manrope and Silkscreen (SIL Open Font License), the latin files from the Byteberry site build.
- Icons: [Simple Icons](https://simpleicons.org) (CC0).
- The Lovelysmiles images are read from the Byteberry site folder, `D:/ByteBerry/www/public/images/work`.

Run it with Python 3 and `pip install fonttools brotli pillow`:

```bash
python widgets/build_profile.py
```

The contribution snake is drawn by `.github/workflows/snake.yml` every day and published to the `output` branch.
