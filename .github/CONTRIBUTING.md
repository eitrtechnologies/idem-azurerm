# Contributing Guidelines

Thanks for your interest in contributing to `idem-azurerm`. The following is a set of guidelines for contributing to
this project. The `idem-azurerm` project is open and encouraging to code contributions.

### License Notice

Please be advised that all code contributions will be licensed under the Apache 2.0
License. We cannot accept contributions that already hold a License other
than Apache 2.0 without explicit exception.

# Reporting Issues

## Bugs

A bug is a *demonstrable problem* that is caused by the code in the repository.

Please read the following guidelines and check the
[list of known issues](https://github.com/eitrtechnologies/idem-azurerm/issues) before you
[report an issue](https://github.com/eitrtechnologies/idem-azurerm/issues/new/choose).

1. **Use the GitHub issue search** -- check if the issue has
   already been reported. If it has been, please comment on the existing issue.

2. **Check if the issue has been fixed** — Various point-release branches may already contain
   a fix. Please try to reproduce the bug against the latest git ``HEAD`` or
   the latest release.

3. **Isolate the demonstrable problem** -- make sure that the
   code in the project's repository is *definitely* responsible for the issue.

4. **Include a reproducible example** -- Provide the steps which
   led you to the problem.

Please try to be as detailed as possible in your report, too. What is your
environment? What steps will reproduce the issue? What Operating System? What
would you expect to be the outcome? All these details will help people to
assess and fix any potential bugs.

Valid bugs will be categorized for the next release and worked on as quickly
as resources can be reasonably allocated.

## Features

The `idem-azurerm` project is always working to be more powerful. Feature additions and requests are
welcomed. When requesting a feature it will be categorized for a release or
placed under the "Feature" label.

If a new feature is desired, the fastest way to get it into `idem-azurerm` is to
contribute the code. Before starting on a new feature, an issue should be filed
for it. The one requesting the feature will be able to then discuss the feature
with the `idem-azurerm` team and discover the best way to get the feature into `idem-azurerm` and
if the feature makes sense.

It is extremely common that the desired feature has already been completed.
Look for it in the docs before filing the request. It is also common that the problem which would be
solved by the new feature can be easily solved another way, which is a great
reason to ask first.

# Fixing issues

If you wish to help us fix the issue you're reporting, please see the sections below regarding development environment
setup, testing, and standards. This information will ensure code and branches are maintained in the expected manner.

The development team will review each fix and if everything is accepted, the fix will be merged into the `idem-azurerm`
codebase.

# Development

## Contribution Workflow

Code contributions—bug fixes, new development, test improvement—all follow a GitHub-centered workflow. To participate
in `idem-azurerm` development, set up a GitHub account. Then:

1. Fork the repo you plan to work on. Go to the project repo page and use the Fork button. This will create a copy of
   the repo, under your username. (For more details on how to fork a repository see this guide.)
2. Clone down the repo to your local system.
```
git clone git@github.com:<your-user-name>/idem-azurerm.git
```
3. Create a new branch to hold your work.
```
git checkout -b <branch-name>
```
4. Work on your new code. Write and run tests.
5. Commit your changes.
```
git add <files>
git commit -m "<commit message here>"
```
6. Push your changes to your GitHub repo.
```
git push origin <branch-name>
```
7. Open a Pull Request (PR). Go to the original project repo on GitHub. There will be a message about your recently
   pushed branch, asking if you would like to open a pull request. Follow the prompts, compare across repositories, and
   submit the PR. This will send an email to the committers. You may want to consider sending an email to the mailing
   list for more visibility. (For more details, see the
   [GitHub guide on PRs.](https://help.github.com/articles/creating-a-pull-request-from-a-fork))

**Before working on your next contribution, make sure your local repository is up to date.**

1. Set the upstream remote. (You only have to do this once per project, not every time.)
```
git remote add upstream git@github.com:eitrtechnologies/idem-azurerm
```
2. Switch to the local master branch.
```
git checkout master
```
3. Pull down the changes from upstream.
```
git pull upstream master
```
4. Push the changes to **your** GitHub account regularly. (Optional, but a good practice.)
```
git push origin master
```
5. Create a new branch if you are starting new work.
```
git checkout -b <branch-name>
```

## Pull Requests (PR)

When code is complete and ready for review follow the steps below to ensure code is properly formatted and functioning
as expected. Remember to rebase against updated `master` branch **before** creating a PR to have linear git history.

1. Run [black code formatter](https://github.com/psf/black) to make sure our code is
   [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant.
2. Use [pre-commit](https://pre-commit.com) which is managed via the `.pre-commit-config.yaml` config file.
   For additional information see [usage instructions for pre-commit](https://pre-commit.com/#usage)
3. Cover new code with a test case (new or existing one).
4. Ensure all tests pass during build

Maintainers and other contributors will review your PR. Please participate in the conversation, and try to make any
requested changes. Once the PR is approved, the code will be merged.
