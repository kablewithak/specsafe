export type DefinitionId =
  | "verification"
  | "adaptive-verification"
  | "confidence"
  | "calibration"
  | "capacity"
  | "causal-information"
  | "matched-replay"
  | "ranking-safety"
  | "promotion-gate";

export type Definition = Readonly<{
  term: string;
  short: string;
  technical: string;
  whyItMatters?: string;
}>;

export const definitions = {
  verification: {
    term: "Verification",
    short:
      "Extra checking work used to decide whether an AI system should trust or continue with a candidate output.",
    technical:
      "Additional compute spent evaluating candidate behavior before accepting or continuing execution.",
    whyItMatters:
      "Verification can improve reliability, but it also consumes limited compute. The system therefore needs a disciplined rule for deciding when that extra work is worthwhile.",
  },

  "adaptive-verification": {
    term: "Adaptive verification",
    short:
      "Changing how much verification work is performed based on the situation at decision time.",
    technical:
      "A causal scheduling policy that can vary verification effort using permitted runtime information such as current confidence and available capacity.",
    whyItMatters:
      "If extra verification is most valuable in some situations and wasteful in others, a policy that adapts responsibly could use limited compute more intelligently than a fixed rule.",
  },

  confidence: {
    term: "Confidence",
    short:
      "A score representing how strongly the system believes a candidate outcome will be acceptable.",
    technical:
      "A decision-time signal used as an input to probability-driven evaluation and scheduling logic.",
    whyItMatters:
      "A scheduler should not depend on confidence unless that signal is reliable enough for the decision it is being asked to make.",
  },

  calibration: {
    term: "Calibration",
    short:
      "How closely confidence scores correspond to what actually happens.",
    technical:
      "The relationship between predicted confidence and observed outcome frequency, evaluated with held-out evidence before confidence is allowed to drive automation.",
    whyItMatters:
      "A confidence score can look precise while still being systematically misleading. Calibration testing checks whether the probabilities deserve to influence decisions.",
  },

  capacity: {
    term: "Capacity",
    short:
      "How much verification compute is available when the policy must make its decision.",
    technical:
      "A decision-time resource signal representing the current verification budget or load condition available to the scheduling policy.",
    whyItMatters:
      "The value of spending extra compute changes when the system is lightly loaded, constrained, or saturated.",
  },

  "causal-information": {
    term: "Causal information",
    short:
      "Information that genuinely exists when the decision must be made.",
    technical:
      "Runtime information available at decision time, excluding future outcomes, retrospective labels, or other post-hoc evidence.",
    whyItMatters:
      "A policy that uses future information can appear excellent in replay while being impossible to run honestly in a real system.",
  },

  "matched-replay": {
    term: "Matched replay",
    short:
      "Comparing policies on the same underlying cases instead of giving each policy a different test.",
    technical:
      "Deterministic replay in which fixed, threshold, and adaptive policies are evaluated against identical traces and capacity conditions.",
    whyItMatters:
      "Keeping the underlying evidence fixed makes differences between policies easier to attribute to the policy itself rather than to different inputs.",
  },

  "ranking-safety": {
    term: "Ranking safety",
    short:
      "Whether higher confidence still means a candidate is more likely to be correct than a lower-confidence one.",
    technical:
      "The discriminative ordering quality of the confidence signal, evaluated independently before that signal is permitted to drive automated scheduling.",
    whyItMatters:
      "A model can improve average probability metrics while becoming worse at separating stronger predictions from weaker ones.",
  },

  "promotion-gate": {
    term: "Promotion gate",
    short:
      "A rule that must pass before a candidate is allowed to control the system.",
    technical:
      "A predeclared acceptance boundary that separates diagnostic evidence from authorization for runtime use.",
    whyItMatters:
      "An improvement on one metric should not automatically become permission to automate. Independent gates make required safety properties explicit.",
  },
} satisfies Record<DefinitionId, Definition>;

export function getDefinition(id: DefinitionId): Definition {
  return definitions[id];
}
