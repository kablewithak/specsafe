export type Explanation = Readonly<{
  title: string;
  summary: string;
  detail?: string;
}>;

export const projectExplanation = {
  title: "Can an AI system spend verification compute more intelligently?",
  summary:
    "SpecSafe evaluates whether a confidence-aware, capacity-aware verification policy can outperform simpler fixed rules while using only information available at decision time.",
  detail:
    "The goal is not to manufacture a winning policy. The goal is to build an evaluation process capable of rejecting attractive but invalid improvements.",
} satisfies Explanation;

export const falseWinExplanation = {
  title: "The failure SpecSafe was built to catch",
  summary:
    "An AI change can improve a headline metric and still make the overall system less safe to automate.",
  detail:
    "Weak evaluation processes often treat an average improvement as permission to deploy. SpecSafe instead separates model improvement from authorization by requiring independent reliability gates.",
} satisfies Explanation;

export const causalBoundaryExplanation = {
  title: "The policy cannot know the future",
  summary:
    "Every valid policy must make its decision using only information that exists at that moment.",
  detail:
    "Future correctness, retrospective outcomes, and other post-hoc signals are excluded from the valid runtime boundary. A retrospective policy may be useful as a diagnostic control, but it cannot count as a deployable comparison.",
} satisfies Explanation;

export const comparisonExplanation = {
  title: "Three policies, the same evidence",
  summary:
    "Fixed, threshold, and adaptive policies are compared on identical traces and capacity conditions.",
  detail:
    "Matched replay reduces ambiguity: when the underlying cases remain fixed, observed differences are easier to attribute to policy behavior rather than different test inputs.",
} satisfies Explanation;

export const confidenceGateExplanation = {
  title: "Better probability metrics are not enough",
  summary:
    "A confidence candidate must satisfy the properties required for automation, not merely improve an aggregate score.",
  detail:
    "SpecSafe evaluates calibration and ranking behavior separately because a candidate can become better at estimating probabilities while becoming worse at ordering stronger predictions above weaker ones.",
} satisfies Explanation;

export const evidenceExplanation = {
  title: "The explanation is optional. The evidence is inspectable.",
  summary:
    "The interface should make the experiment understandable without hiding the exact artifacts behind the story.",
  detail:
    "Plain-language explanations help a visitor build the mental model. Exact case values, decisions, hashes, provenance, supported claims, and non-claims remain available for independent inspection.",
} satisfies Explanation;
