---
trigger: glob
globs: .github/**/*.yml
---
# GitHub Actions Usage Guidelines

## Action Sources
**Only use actions from these sources:**
1. **Repository-local actions** - Actions defined in `.github/actions/` within this repository
2. **Enterprise-defined actions** - Actions published to your enterprise's GitHub instance
3. **GitHub official actions** - Actions maintained by GitHub (e.g., `actions/checkout@v5`, `actions/setup-dotnet@v4`)
4. **NO third-party marketplace actions** - Actions from non-GitHub publishers are not permitted

## Action Selection
- Use repository-local actions when possible for maximum control and security
- For enterprise actions, verify they're approved for your organization's use
- GitHub official actions are safe to use (e.g., `actions/checkout@v5`, `actions/setup-dotnet@v4`)
- Always use the latest supported version of enterprise/local/official actions
- Verify action versions using context7, enterprise documentation, or GitHub's official docs

## Script Management
- Don't use inline scripts in workflow files
- Put scripts into repository-local actions instead
- This improves reusability and maintainability

## Workflow Reuse
- Use a shared workflow when two or more workflows perform the same steps
- Shared workflows should also follow the action source restrictions above