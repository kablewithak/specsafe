import { z } from "zod";

const comparisonResultSchema = z.enum([
  "utility_neutral",
  "adaptive_lower_utility",
  "adaptive_higher_utility",
]);

const outcomeCountSchema = z
  .object({
    adaptive_higher: z.number().int().nonnegative(),
    adaptive_lower: z.number().int().nonnegative(),
    neutral: z.number().int().nonnegative(),
  })
  .strict();

const metricSchema = z
  .object({
    calibrated_value: z.number(),
    display_name: z.string().min(1),
    gate_result: z.enum(["improved", "failed_ranking_safety"]),
    lower_is_better: z.boolean(),
    metric_key: z.enum(["brier_score", "fixed_bin_ece", "auroc"]),
    movement: z.number(),
    raw_value: z.number(),
  })
  .strict();

const caseSchema = z
  .object({
    adaptive_utility: z.number(),
    adaptive_vs_fixed: comparisonResultSchema,
    adaptive_vs_threshold: comparisonResultSchema,
    capacity_profile: z.string().min(1),
    case_id: z.string().regex(/^MPC5-\d{3}$/),
    fixed_utility: z.number(),
    plain_language_result: z.string().min(1),
    split: z.enum(["development", "adversarial_regression"]),
    threshold_utility: z.number(),
  })
  .strict();

const policySchema = z
  .object({
    capacity_aware: z.boolean(),
    display_name: z.string().min(1),
    plain_language_description: z.string().min(1),
    policy_key: z.enum(["fixed_length", "static_threshold", "adaptive"]),
  })
  .strict();

const sectionSchema = z
  .object({
    purpose: z.string().min(1),
    section_id: z.enum([
      "overview",
      "what_was_tested",
      "policy_results",
      "capacity_conditions",
      "confidence_gate",
      "what_it_means",
      "evidence",
    ]),
    title: z.string().min(1),
  })
  .strict();

const sourceArtifactSchema = z
  .object({
    relative_path: z.string().min(1),
    sha256: z.string().regex(/^[a-f0-9]{64}$/),
  })
  .strict();

export const evidenceIndexSchema = z
  .object({
    adaptive_vs_fixed: outcomeCountSchema,
    adaptive_vs_threshold: outcomeCountSchema,
    calibration_gate: z
      .object({
        confidence_status: z.literal("unfit_use_conservative_fallback"),
        decision_outcome: z.literal("KEEP_DIAGNOSTIC_ONLY"),
        degradation_multiple_of_limit: z.number().positive(),
        failure_label: z.literal("ranking_safety_regression"),
        holdout_negative_count: z.number().int().nonnegative(),
        holdout_positive_count: z.number().int().nonnegative(),
        holdout_record_count: z.number().int().positive(),
        maximum_allowed_auroc_degradation: z.number().positive(),
        metrics: z.array(metricSchema).length(3),
        observed_auroc_delta: z.number().negative(),
        plain_language_result: z.string().min(1),
        promotion_attempt_status: z.literal("closed_not_promoted"),
      })
      .strict(),
    cases: z.array(caseSchema).length(6),
    dataset_publication: z
      .object({
        anonymous_verification_passed: z.literal(true),
        exact_file_count: z.literal(9),
        gated: z.literal(false),
        public: z.literal(true),
        publication_manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/),
        published_revision: z.string().regex(/^[a-f0-9]{40}$/),
        repository_id: z.string().min(1),
        repository_url: z.string().url(),
      })
      .strict(),
    final_interpretation: z.string().min(1),
    live_inference: z.literal(false),
    maturity_labels: z.array(z.string().min(1)).min(1),
    non_claims: z.array(z.string().min(1)).min(1),
    policies: z.array(policySchema).length(3),
    quick_summary: z.string().min(1),
    read_only: z.literal(true),
    schema_version: z.literal("specsafe_hugging_face_space_evidence_index_v1"),
    sections: z.array(sectionSchema).length(7),
    short_description: z.string().min(1),
    source_artifacts: z.array(sourceArtifactSchema).length(3),
    source_commit: z.string().min(7),
    space_id: z.literal("specsafe-reliability-lab-v1"),
    space_repository_name: z.literal("specsafe-reliability-lab"),
    supported_claims: z.array(z.string().min(1)).min(1),
    tested_question: z.string().min(1),
    title: z.string().min(1),
    unsafe_controls_failed_causal_safety: z.literal(true),
    unsafe_retrospective_controls_excluded: z.literal(6),
    user_input_collection: z.literal(false),
    valid_causal_comparisons: z.literal(6),
  })
  .strict()
  .superRefine((evidence, context) => {
    const caseIds = new Set(evidence.cases.map((item) => item.case_id));
    if (caseIds.size !== 6) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: "Case IDs must be unique." });
    }
    const totalHoldout =
      evidence.calibration_gate.holdout_positive_count +
      evidence.calibration_gate.holdout_negative_count;
    if (totalHoldout !== evidence.calibration_gate.holdout_record_count) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Holdout class counts must equal the holdout record count.",
      });
    }
  });

export type EvidenceIndex = z.infer<typeof evidenceIndexSchema>;
export type EvidenceCase = EvidenceIndex["cases"][number];
export type EvidenceMetric = EvidenceIndex["calibration_gate"]["metrics"][number];

export async function loadEvidence(signal?: AbortSignal): Promise<EvidenceIndex> {
  const response = await fetch("./evidence/evidence_index.json", {
    cache: "no-store",
    signal,
  });
  if (!response.ok) {
    throw new Error(`Evidence request failed with status ${response.status}.`);
  }
  return evidenceIndexSchema.parse(await response.json());
}
