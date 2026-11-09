# Troubleshooting

## GUI does not start

- Ensure Python 3.11+ is installed: `python --version`
- Ensure PySide6 is installed: `python -m pip install PySide6`
- On Linux, run inside a desktop session (X11/Wayland) so `DISPLAY`/`WAYLAND_DISPLAY` is set.
- For automated checks, try: `QT_QPA_PLATFORM=offscreen python -m winmedia --smoke-test` (if supported).

## Missing system tools reported in Settings

This is expected in Phase 1 on non-Linux systems or minimal Linux installs. Install the suggested packages before using future USB/download features.

## Logs

Logs are written to the user cache/log directory (see `winmedia.utils.paths.log_file()`). Review logs for diagnostics; do not share logs if they may contain sensitive paths you consider private.
