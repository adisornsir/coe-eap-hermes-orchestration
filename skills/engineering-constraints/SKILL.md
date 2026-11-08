---
name: engineering-constraints
description: Choose small verifiable technical boundaries for DESIGN and BUILD.
---
# Bounded engineering work

Start with the smallest change that satisfies the accepted spec. Identify callers, input and output contracts, failure conditions and required tests before broad abstractions. Prefer deterministic tests with hand-written fakes. Never alter security controls, tests or scope solely to obtain a passing result.
