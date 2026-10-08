"""Human eligibility and split invariants, used at publication and consumption."""
from __future__ import annotations

from datetime import date
from importlib.resources import files

from .common import DatasetError, identity, parse_json
from .schema import Decision, Groups, MAPPING, Review, Sample


KNOWN_SOURCE = "bc362e5e774e63cd62e677522abbf2bc632422cadd7b5e9642bbfa3ca97eede3"


def group_evidence(source_sha256, supplied=None):
    known = Groups(schema_version=1, source_sha256=source_sha256, pairs=[])
    if source_sha256 == KNOWN_SOURCE:
        known = Groups.model_validate(parse_json(
            files(__package__).joinpath("schemas/wi03-groups.json").read_bytes()))
    if supplied is None:
        return known
    groups = Groups.model_validate(supplied)
    if groups.source_sha256 != source_sha256:
        raise DatasetError("Group evidence belongs to another source")
    pairs = {tuple(sorted((p.left, p.right))): p for p in known.pairs}
    for pair in groups.pairs:
        pairs.setdefault(tuple(sorted((pair.left, pair.right))), pair)
    return Groups(schema_version=1, source_sha256=source_sha256,
                  pairs=[pairs[key] for key in sorted(pairs)])


def template(records, source_sha256):
    return Review(schema_version=1, source_sha256=source_sha256,
                  samples=[Decision(sample_id=s.sample_id, source_path=s.source_path) for s in records])


def validate_review(review: Review, records: list[Sample], groups: Groups) -> list[str]:
    blockers = []

    def block(message):
        blockers.append(message)

    if review.source_sha256 != groups.source_sha256:
        block("Review/source digest mismatch; bind review to the actual source ZIP")
    if not all((review.reference, review.reviewer, review.date)):
        block("Review requires reference, reviewer and date")
    elif review.date:
        try:
            date.fromisoformat(review.date)
        except ValueError:
            block("Review date is invalid")
    if review.mapping != MAPPING or any(type(v) is not int for v in (review.mapping or {}).values()):
        block("Explicit canonical name mapping is required")
    if review.class_semantics_approved is not True:
        block("Physical-category semantics require explicit review approval")
    if review.evaluation is None:
        block("Evaluation status/evidence/limitations require review")
    elif review.evaluation.status == "exploratory" and not review.evaluation.limitations:
        block("Exploratory evaluation requires explicit independence limitations")
    decisions = {d.sample_id: d for d in review.samples}
    samples = {s.sample_id: s for s in records}
    if len(decisions) != len(review.samples) or set(decisions) != set(samples):
        block("Review must contain exactly one decision for every source sample")
    active = {}
    for sid, sample in samples.items():
        d = decisions.get(sid)
        if d is None:
            continue
        if d.source_path != sample.source_path:
            block(f"{sid}: stale source path in review")
        if d.role is None:
            block(f"{sid}: effective role requires review")
        elif d.role == "excluded":
            if not d.exclusion_reason:
                block(f"{sid}: exclusion requires a reason")
        else:
            active[sid] = d
            if d.exclusion_reason:
                block(f"{sid}: active sample has contradictory exclusion reason")
            if d.origin != "human" or d.eligibility_approved is not True or not d.origin_evidence:
                block(f"{sid}: only reviewed human annotations are eligible; predictions/unknown origins are excluded")
            if d.completeness not in ("exhaustive", "verified-background"):
                block(f"{sid}: exhaustive annotation or verified background review required")
            if sample.annotation_count == 0 and d.completeness != "verified-background":
                block(f"{sid}: annotation-free image requires verified background review")
            if sample.annotation_count > 0 and d.completeness == "verified-background":
                block(f"{sid}: foreground annotations contradict background-only review")
            if sample.class_pixels.get("255", 0):
                if d.conflict_policy != "ignore" or not d.conflict_rationale:
                    block(f"{sid}: conflicting labels require correction/exclusion or reviewed ignore rationale")
            if sum(sample.class_pixels.get(str(i), 0) for i in (0, 1, 2)) == 0:
                block(f"{sid}: all-ignore mask is ineligible")
            if d.group_status is None or not d.group_evidence:
                block(f"{sid}: group status/evidence require review")
            elif d.group_status == "known" and not d.group:
                block(f"{sid}: known group requires group identity")
            elif d.group_status == "unknown" and d.group is not None:
                block(f"{sid}: unknown group cannot claim a known identity")
            if review.evaluation and review.evaluation.status == "independence-reviewed" and d.group_status != "known":
                block(f"{sid}: independent evaluation needs affirmative acquisition group evidence")
    for role in ("train", "validation"):
        if not any(d.role == role for d in active.values()):
            block(f"Nonempty {role} split is required")
    # Compare every active exact-content identity and known group, not source names.
    for attribute in ("source_sha256", "rgb_sha256", "group"):
        seen = {}
        for sid, d in active.items():
            value = d.group if attribute == "group" else getattr(samples[sid], attribute)
            if value is None:
                continue
            previous = seen.get(value)
            if previous:
                old_sid, old_role = previous
                if old_role != d.role:
                    block(f"{sid}/{old_sid}: {attribute} spans active roles")
                if attribute != "group" and samples[old_sid].mask_pixels_sha256 != samples[sid].mask_pixels_sha256:
                    block(f"{sid}/{old_sid}: exact duplicate has conflicting annotations")
            else:
                seen[value] = (sid, d.role)
    pairs = {tuple(sorted((p.left, p.right))) for p in groups.pairs}
    if len(pairs) != len(groups.pairs):
        block("Duplicate candidate pair evidence")
    dispositions = {tuple(sorted((d.left, d.right))): d for d in review.dispositions}
    if len(dispositions) != len(review.dispositions) or set(dispositions) - pairs:
        block("Duplicate or unknown candidate disposition")
    for pair in sorted(pairs):
        left, right = pair
        if left == right or left not in samples or right not in samples:
            block(f"Invalid candidate identities: {left}/{right}")
            continue
        d = dispositions.get(pair)
        if d is None:
            block(f"{left}/{right}: candidate grouping disposition requires review")
            continue
        a, b = active.get(left), active.get(right)
        if d.decision == "excluded":
            if a and b:
                block(f"{left}/{right}: excluded disposition requires an excluded sample")
        elif a and b:
            if d.decision == "co-group" and (not a.group or a.group != b.group or a.role != b.role):
                block(f"{left}/{right}: co-group disposition requires the same group and role")
            if d.decision == "uncertain" and review.evaluation and review.evaluation.status != "exploratory":
                block(f"{left}/{right}: uncertain group cannot support independent evaluation")
    return sorted(set(blockers))


def split_fingerprint(records, review):
    decisions = {d.sample_id: d for d in review.samples}
    return identity([{
        "sample_id": s.sample_id, "image": s.rgb_sha256, "role": decisions[s.sample_id].role,
        "exclusion_reason": decisions[s.sample_id].exclusion_reason,
        "group": decisions[s.sample_id].group, "group_status": decisions[s.sample_id].group_status,
        "dispositions": [d.model_dump() for d in sorted(review.dispositions, key=lambda d: (d.left, d.right))
                         if s.sample_id in (d.left, d.right)],
    } for s in sorted(records, key=lambda s: s.sample_id)])
