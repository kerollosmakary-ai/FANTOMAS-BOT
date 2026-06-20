# CI/CD Setup Guide

## 1. Push the workflow to GitHub

```bash
git remote add origin https://github.com/kerollosmakary-ai/FANTOMAS-BOT.git
git add .github/workflows/deploy.yml
git commit -m "ci: add deploy workflow to fserver"
git push -u origin main
```

If `main` branch doesn't exist on remote, you may need to create it first:
```bash
git branch -M main
git push -u origin main --force
```

## 2. Add SSH Secret to GitHub

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value |
|-------------|-------|
| `FSERVER_SSH_KEY` | Contents of `~/.ssh/id_fserver` (your private key) |

### How to get your private key:
```bash
cat ~/.ssh/id_fserver
```
Copy the entire output (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`).

## 3. Ensure fserver has the public key

SSH into your server and add the public key to `~/.ssh/authorized_keys`:
```bash
ssh root@167.233.103.236
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys << 'KEY'
[paste your public key here]
KEY
chmod 600 ~/.ssh/authorized_keys
```

Your public key is at `~/.ssh/id_fserver.pub`.

## 4. Trigger Deployment

Push any commit to `main` branch:
```bash
git commit --allow-empty -m "trigger: deploy"
git push
```

Watch the deployment at:  
`https://github.com/kerollosmakary-ai/FANTOMAS-BOT/actions`
