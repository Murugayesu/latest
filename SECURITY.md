# Security

## Reporting a problem

Please report security problems privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Do not open a public issue.

Include what you ran, what happened, and the date. You should get a reply within 7 days.

## What counts

- The script sending data anywhere other than the public registries listed in the README.
- A crafted registry response, README or package name that makes the script run code, write files, or leak a token.
- The skill's instructions leading an agent to follow instructions embedded in fetched content.

## What this project does not claim

The skill reduces some risks when an agent chooses versions. It is not a security scanner.

- The 7-day release-age rule is a policy heuristic.
- A clean advisory check means no known advisory was found in the sources checked on that date.
- A wrong version pick is a bug, not a vulnerability. Please report it as a normal issue.

## Supported versions

Only the newest release is supported.
