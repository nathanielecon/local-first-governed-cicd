# Evidence storage

Each release uses `evidence/<release-id>/manifest.json`. Generated reports and runtime captures are ignored by default because they may be large; selectively commit sanitized reviewer evidence. Never store credentials, tokens, private request bodies, or personal data here.

