# Security policy

Do not commit credentials, API tokens, private datasets, serial identifiers tied to private deployments, or secrets to this repository.

Report suspected vulnerabilities through GitHub's private security reporting/security advisory flow when available. Avoid opening a public issue with exploit details before a fix is available.

Security-sensitive changes should include a regression test and must pass the repository CI before merge.


## Untrusted data inputs

OSW ZIP files are treated as untrusted input. Validation reads members in place without extracting them and rejects parent-directory paths, encrypted members, oversized files, excessive aggregate uncompressed size, and extreme compression ratios. The OSW schema is supplied explicitly by the caller rather than fetched at runtime.

Optional dependency profiles (`core`, `osm`, and `osw`) are audited independently with pip-audit on pull requests and weekly.
