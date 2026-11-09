# Arch Linux packaging (template)

This directory contains a **template** `PKGBUILD` for packaging WinMedia Linux on Arch Linux.

## Important

- `sudo pacman -S winmedia-linux` works **only** if `winmedia-linux` is available in an **official Arch repository** you have enabled (or in a custom repo you configured). A package being on GitHub does **not** automatically make it installable via `pacman -S`.
- The usual path is: publish/maintain the package on the **AUR** first (`winmedia-linux`), let users build/install it with an AUR helper (e.g., `yay -S winmedia-linux`) or manually with `makepkg`. Inclusion in official repos is a separate process decided by Arch maintainers.

## Before publishing to AUR

1. Update `pkgver`/`pkgrel` for each release.
2. Replace `sha256sums=('SKIP')` with the real SHA-256 of the source tarball:
   ```bash
   updpkgsums
   # or manually: sha256sum winmedia-linux-<ver>.tar.gz
   ```
3. Generate `.SRCINFO`:
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```
4. Test locally:
   ```bash
   makepkg -si
   ```
5. Follow [AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines).

## Safety status

WinMedia Linux is currently **safety-gated** (destructive USB write execution is fail-closed/disabled in this build; bootability not claimed). Packaging should preserve that honesty in descriptions/release notes.
