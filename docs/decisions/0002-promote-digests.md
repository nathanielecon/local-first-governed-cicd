# ADR 0002: Promote immutable image digests

Status: accepted

The pipeline builds one image and records its registry digest. Staging and production consume that digest. Human-readable tags are aliases only. Rollback selects the previous verified digest and never rebuilds old source, preventing dependency drift between environments and releases.

