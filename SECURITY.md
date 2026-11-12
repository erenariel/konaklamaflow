# Security policy

## Reporting

**Do not post vulnerabilities, private reservation data, access tokens or screenshots containing customer data to public GitHub issues.** Contact the repository owner privately through GitHub and request a private reporting channel; do not assume one exists until the owner confirms it.

## Threat model (prototype)

- Public source code must have **no** customer data, passports, names, emails, hotel passwords, OTA/API secrets or internal production endpoints.
- Input IDs must be pseudonymized before they reach this engine; alphanumeric-only input restrictions are insufficient alone to anonymize a dataset.
- This software is an offline **decision-support** component. Its output can be wrong or incomplete and is not a booking action.
- A production connector would require documented consent/legal basis, minimum permissions, explicit human approval, signed or audited event logging, secret management, tenant boundaries and vendor authorization.
- Do not use this tool to alter official accommodation notifications or substitute identification data.

## Supported versions

Only the newest tagged release, once published, will be maintained. At present, the project has **no published release or security SLA**.
