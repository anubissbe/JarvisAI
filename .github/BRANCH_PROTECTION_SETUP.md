# Branch Protection Setup Guide

## 🛡️ Manual Branch Protection Configuration

Since GitHub CLI has limitations with complex branch protection rules, here's how to set up branch protection manually through the GitHub web interface.

## 📋 Step-by-Step Instructions

### 1. Navigate to Branch Protection Settings

1. Go to: https://github.com/anubissbe/JarvisAI/settings/branches
2. Click **"Add rule"** or **"Add classic protection rule"**
3. Enter `main` as the branch name pattern

### 2. Configure Protection Rules

#### ✅ **Required Status Checks**
- [x] Require status checks to pass before merging
- [x] Require branches to be up to date before merging
- Select these required status checks:
  - `ci-cd` (CI/CD Pipeline)
  - `security` (Security Scan)
  - `code-quality` (Code Quality)
  - `CodeQL` (GitHub CodeQL Analysis)

#### ✅ **Pull Request Requirements**
- [x] Require a pull request before merging
- [x] Require approvals: **1** approval required
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require review from code owners (if CODEOWNERS file exists)
- [x] Require approval of the most recent reviewable push
- [x] Require conversation resolution before merging

#### ✅ **Additional Restrictions**
- [x] Restrict pushes that create files larger than 100 MB
- [x] Do not allow bypassing the above settings
- [ ] Allow force pushes (KEEP UNCHECKED)
- [ ] Allow deletions (KEEP UNCHECKED)

#### ⚙️ **Administrative Settings**
- [ ] Include administrators (allow repo admins to bypass)

### 3. Save Protection Rule

Click **"Create"** to save the branch protection rule.

## 🔧 Alternative: GitHub CLI Command

If you prefer to use CLI (requires proper JSON formatting):

```bash
gh api repos/anubissbe/JarvisAI/branches/main/protection \
  --method PUT \
  --input protection-config.json
```

Where `protection-config.json` contains:

```json
{
  "required_status_checks": {
    "strict": true,
    "checks": []
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
```

## 📊 Recommended Protection Settings

### For Production Repository:
- **Pull Request Reviews**: 1-2 required approvals
- **Status Checks**: All CI/CD workflows must pass
- **Force Push Protection**: Disabled (prevents history rewriting)
- **Deletion Protection**: Disabled (prevents accidental branch deletion)
- **Admin Bypass**: Disabled for maximum security

### For Development Repository:
- **Pull Request Reviews**: 1 required approval
- **Status Checks**: Core workflows (CI/CD, Security)
- **Admin Bypass**: Can be enabled for flexibility

## 🔍 Verification

After setting up branch protection:

1. Go to: https://github.com/anubissbe/JarvisAI/settings/branches
2. Verify the `main` branch shows protection rules
3. Try to push directly to main - should be blocked
4. Create a test PR to verify the workflow

## 🚨 Status Check Requirements

The following GitHub Actions workflows should be configured as required status checks:

1. **ci-cd** (`/.github/workflows/ci-cd.yml`)
   - Runs tests, builds, and deployment checks
   
2. **security** (`/.github/workflows/security.yml`)
   - CodeQL analysis, dependency scanning, secret detection
   
3. **code-quality** (`/.github/workflows/code-quality.yml`)
   - Code formatting, linting, complexity analysis

4. **dependency-update** (`/.github/workflows/dependency-update.yml`)
   - Dependency security audits

## 📞 Support

If you encounter issues:
- Check the [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- Verify your repository admin permissions
- Ensure the required workflows exist and are enabled

## ✅ Verification Checklist

After setup, verify:
- [ ] Direct pushes to main are blocked
- [ ] Pull requests require approval
- [ ] Status checks must pass before merge
- [ ] Force pushes are blocked
- [ ] Branch deletion is blocked
- [ ] Conversation resolution is required

---

**Note**: These settings ensure enterprise-grade branch protection for the JarvisAI repository.