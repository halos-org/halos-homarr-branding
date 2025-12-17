# Homarr Branding HaLOS

HaLOS branding and default configuration package for the Homarr dashboard.

## Overview

This package provides:

- **branding.toml** - Configuration file read by `homarr-container-adapter`
- **Static assets** - Logo, favicon, and background image for dashboard branding
- **Default settings** - Theme colors, background, admin credentials, pre-configured board

## Installation

The package is installed as part of HaLOS images. It depends on `halos-homarr-container`.

```bash
apt install halos-homarr-branding
```

## Configuration

The main configuration file is installed at:

```
/etc/halos-homarr-branding/branding.toml
```

### Configuration Sections

| Section | Purpose |
|---------|---------|
| `[identity]` | Product name, logo paths |
| `[theme]` | Color scheme, colors, background image, opacity, item radius |
| `[credentials]` | Default admin username and password |
| `[board]` | Default board name, layout, column count |
| `[settings]` | Analytics and crawling preferences |

## How It Works

1. `halos-homarr-container` starts the Homarr dashboard
2. `homarr-container-adapter` detects first boot
3. Adapter reads `/etc/halos-homarr-branding/branding.toml`
4. Adapter completes Homarr onboarding via API:
   - Creates admin user with configured credentials
   - Applies theme settings
   - Creates default board with Cockpit tile
   - Sets board as home page

## Building

```bash
# Build the Debian package
./run build-debtools  # First time only
./run build-deb

# Check package quality
./run lint-deb
```

## Files Installed

| Path | Description |
|------|-------------|
| `/etc/halos-homarr-branding/branding.toml` | Branding configuration |
| `/usr/share/halos-homarr-branding/logo.svg` | HaLOS logo (SVG) |
| `/usr/share/halos-homarr-branding/logo.png` | HaLOS logo (PNG) |
| `/usr/share/halos-homarr-branding/favicon.ico` | Favicon |
| `/usr/share/halos-homarr-branding/background.jpg` | Dashboard background image |

## Related Packages

- [halos-homarr-container](../halos-core-containers/apps/homarr/) - Homarr dashboard container
- [homarr-container-adapter](https://github.com/hatlabs/homarr-container-adapter) - First-boot setup and auto-discovery

## License

MIT License - see [LICENSE](LICENSE) file.
