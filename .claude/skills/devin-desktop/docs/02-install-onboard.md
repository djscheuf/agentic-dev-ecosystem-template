# Install and onboarding

## Download

- Visit https://devin.ai to download Devin Desktop for macOS, Windows, or Linux.
- The `devin-desktop` command can be added to PATH during onboarding:

```bash
devin-desktop ~/Developer/my-project
```

## Platform requirements

| Platform | Minimum requirement |
|----------|---------------------|
| macOS | OS X Yosemite or later |
| Windows | Windows 10 or later |
| Linux (tar) | glibc >= 2.28, glibcxx >= 3.4.25 |
| Linux (deb) | Ubuntu 20.04+, Debian 10+ |
| Linux (rpm) | Fedora 36+, CentOS 8+, RHEL 8+ |

## Linux package repositories

Devin Desktop packages are named `devin-desktop`. The repositories may still use the legacy `windsurf` name for the URL, but the package is `devin-desktop`.

### Debian / Ubuntu

```bash
sudo apt-get install wget gpg
wget -qO- "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/windsurf.gpg" | gpg --dearmor > windsurf-stable.gpg
sudo install -D -o root -g root -m 644 windsurf-stable.gpg /etc/apt/keyrings/windsurf-stable.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/windsurf-stable.gpg] https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/apt stable main" | sudo tee /etc/apt/sources.list.d/windsurf.list > /dev/null
rm -f windsurf-stable.gpg

sudo apt install apt-transport-https
sudo apt update
sudo apt install devin-desktop
```

### Fedora / RHEL / CentOS

```bash
sudo rpm --import https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf
sudo tee /etc/yum.repos.d/windsurf.repo > /dev/null <<'EOF'
[windsurf]
name=Windsurf Repository
baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/
enabled=1
autorefresh=1
gpgcheck=1
metadata_expire=1h
gpgkey=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf
EOF

sudo dnf check-update
sudo dnf install -y devin-desktop
```

## Onboarding

1. Select a theme and choose whether to install the `devin-desktop` terminal command.
2. Import keybindings from VS Code or Cursor if desired.
3. Log in with a Devin account. If login fails, use a Devin API key manually.
4. Start a project or open a folder.
