# HaLOS Branding for Homarr - Agentic Coding Guide

**LAST MODIFIED**: 2025-12-10

**Document Purpose**: Guide for AI assistants working on halos-homarr-branding.

## For Agentic Coding: Use the HaLOS Workspace

**IMPORTANT**: When using Claude Code or other AI assistants, work from the halos-distro workspace repository for full context across all HaLOS repositories.

```bash
# Work from workspace
cd halos-distro/
# This repo is available as: halos-homarr-branding/
```

**Development Workflows**: See `halos-distro/docs/` folder:
- `halos-distro/docs/DEVELOPMENT_WORKFLOW.md` - Detailed Claude Code workflows
- `halos-distro/docs/PROJECT_PLANNING_GUIDE.md` - Project planning process
- `halos-distro/docs/IMPLEMENTATION_CHECKLIST.md` - Implementation checklist

## About This Project

HaLOS branding and default configuration package for the Homarr dashboard. This package provides:

- **branding.toml** - Configuration read by homarr-container-adapter
- **Static assets** - Logo, favicon for dashboard branding
- **Default settings** - Theme colors, admin credentials, board layout

The `homarr-container-adapter` reads `/etc/halos-homarr-branding/branding.toml` during first-boot setup to initialize Homarr with HaLOS branding.

## Git Workflow Policy

**MANDATORY**: PRs must ALWAYS have all checks passing before merging. No exceptions.

**Branch Workflow:** Never push to main directly - always use feature branches and PRs.

## Quick Start

```bash
# Build package
./run build-debtools  # First time only
./run build-deb

# Check quality
./run lint-deb

# Clean build artifacts
./run clean
```

## Project Structure

```
halos-homarr-branding/
├── docs/
│   └── SPEC.md              # Technical specification
├── debian/                  # Debian package files
│   ├── control             # Package metadata
│   ├── changelog           # Package changelog
│   ├── copyright           # License information
│   ├── install             # File installation rules
│   ├── rules               # Build rules
│   └── source/format       # Source format
├── docker/                  # Build container
│   ├── Dockerfile.debtools
│   └── docker-compose.debtools.yml
├── etc/halos-homarr-branding/
│   └── branding.toml       # Branding configuration
├── usr/share/halos-homarr-branding/
│   ├── logo.svg            # HaLOS logo
│   ├── logo.png            # HaLOS logo (PNG)
│   └── favicon.ico         # Favicon
└── run                      # Build script
```

## Configuration File

The `branding.toml` file contains:

- **[identity]** - Product name, logo paths
- **[theme]** - Color scheme, primary/secondary colors
- **[credentials]** - Default admin username/password
- **[board]** - Default board name, layout, Cockpit tile
- **[settings]** - Analytics and crawling settings

## Related Packages

- **homarr-container** - The Homarr dashboard container
- **homarr-container-adapter** - Reads this config and applies it via Homarr API
