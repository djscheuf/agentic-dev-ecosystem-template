---
trigger: model_decision
description: when setting up new projects or installing packages
---

# Use Latest Package Versions and Configurations

## Core Principle
Always use the latest stable versions of packages and their current configuration patterns when setting up new projects or adding dependencies.

## Package Installation Rules

### 1. Check Current Best Practices
Before installing any package:
- Use Context7 to get the latest setup instructions
- Check official documentation for current version
- Verify the correct configuration format for the current major version
- Don't rely on outdated patterns from training data

### 2. Version-Specific Configurations
Many packages change their configuration between major versions:
- **TailwindCSS v4**: Requires `@tailwindcss/postcss` (not just `tailwindcss`)
- **Vite**: Configuration syntax evolves between versions
- **React**: Hooks and patterns change across versions
- **Testing libraries**: Setup and API changes

### 3. Installation Pattern
```bash
# CORRECT: Install with latest compatible versions
npm install -D package-name

# WRONG: Don't specify old versions unless required
npm install -D package-name@old-version
```

### 4. Configuration Files
When creating configuration files:
- Use the format for the CURRENT major version
- Check if separate companion packages are needed (e.g., @tailwindcss/postcss)
- Verify plugin syntax matches current version
- Use ES modules syntax when supported

## Common Package Gotchas

### TailwindCSS
- **v3**: Used `tailwindcss: {}` in postcss.config.js
- **v4**: Requires `@tailwindcss/postcss` package and `'@tailwindcss/postcss': {}` in config
- **Action**: Always check which version and use correct setup

### PostCSS Plugins
- Some plugins move to separate packages between versions
- Always verify the current plugin name and package
- Check if autoprefixer is bundled or separate

### Build Tools (Vite, Webpack, etc.)
- Configuration syntax changes between major versions
- Plugin APIs evolve
- Check current documentation for setup

### Testing Frameworks
- Setup files and configuration location changes
- Global test utilities may require different imports
- Verify current best practices for the version being used

## Decision Process

When setting up a new dependency:

1. **Identify the package needed**
   - What functionality is required?
   - What's the standard package for this in the ecosystem?

2. **Get current documentation**
   - Use Context7 to fetch latest setup instructions
   - Check official docs for current version
   - Look for migration guides if coming from older version

3. **Install with correct packages**
   - Install main package
   - Install any required companion packages
   - Install peer dependencies

4. **Configure using current patterns**
   - Use the configuration format for current version
   - Don't use deprecated patterns
   - Follow current best practices

5. **Verify setup works**
   - Test that configuration is correct
   - Check for deprecation warnings
   - Ensure dev server/build works

## Examples

### Good: TailwindCSS v4 Setup
```bash
# Install both required packages
npm install -D tailwindcss @tailwindcss/postcss

# postcss.config.js - CURRENT v4 format
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
```

### Bad: TailwindCSS v3 Setup (outdated)
```bash
# Missing @tailwindcss/postcss
npm install -D tailwindcss postcss autoprefixer

# postcss.config.js - OLD v3 format
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

## When to Use Older Versions

Only use older package versions when:
- Working with an existing codebase that requires it
- Specific compatibility requirements exist
- Documented technical constraint requires it

**Document the reason** when using older versions.

## Workflow Integration

This rule applies during:
- New project initialization
- Adding new dependencies
- Setting up build tools
- Configuring testing frameworks
- Installing UI libraries
- Adding any third-party packages

## Related Workflows
- `/setup-tailwindcss` - Correct TailwindCSS v4 setup
- Project initialization workflows
- Dependency management workflows
