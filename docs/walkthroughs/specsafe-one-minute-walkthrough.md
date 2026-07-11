# SpecSafe One-Minute Walkthrough

SpecSafe asks a simple question: when an AI system has limited compute, can it spend more effort on
the parts most likely to be useful without cheating by looking at future information?

I built a typed evaluation harness that compares three policies on the same frozen traces and
capacity conditions: a fixed rule, a confidence threshold, and a causal adaptive policy. The
adaptive policy won some cases, tied several, and lost one. That matters because the project keeps
bad and neutral outcomes instead of hiding them.

The strongest result came from a calibrator that looked better on two average metrics. The
independent safety gate showed its ranking became much worse, so SpecSafe blocked promotion and
forced a conservative fallback.

The evidence is public as a sanitized Hugging Face Dataset and a read-only static Space. The release
is tied to exact hashes, publication receipts, and anonymous reconciliation.

The point is not that adaptive scheduling always wins. The point is that reliable AI engineering
needs contracts and gates strong enough to reject a false win before it becomes an automated
system decision.
