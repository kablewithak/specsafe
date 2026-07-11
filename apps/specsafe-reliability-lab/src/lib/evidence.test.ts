import evidenceJson from "../../public/evidence/evidence_index.json";

import { evidenceIndexSchema } from "./evidence";

describe("frozen evidence contract", () => {
  it("parses the exact read-only index", () => {
    const evidence = evidenceIndexSchema.parse(evidenceJson);

    expect(evidence.read_only).toBe(true);
    expect(evidence.live_inference).toBe(false);
    expect(evidence.user_input_collection).toBe(false);
    expect(evidence.cases).toHaveLength(6);
  });

  it("retains the mixed policy result", () => {
    const evidence = evidenceIndexSchema.parse(evidenceJson);

    expect(evidence.adaptive_vs_fixed).toEqual({
      adaptive_higher: 2,
      neutral: 3,
      adaptive_lower: 1,
    });
    expect(evidence.adaptive_vs_threshold).toEqual({
      adaptive_higher: 3,
      neutral: 2,
      adaptive_lower: 1,
    });
  });

  it("retains the governed loss, wins, and blocked activation", () => {
    const evidence = evidenceIndexSchema.parse(evidenceJson);
    const byId = new Map(evidence.cases.map((item) => [item.case_id, item]));

    expect(byId.get("MPC5-103")?.adaptive_vs_fixed).toBe("adaptive_lower_utility");
    expect(byId.get("MPC5-104")?.adaptive_vs_fixed).toBe("adaptive_higher_utility");
    expect(byId.get("MPC5-105")?.adaptive_vs_fixed).toBe("adaptive_higher_utility");
    expect(evidence.calibration_gate.decision_outcome).toBe("KEEP_DIAGNOSTIC_ONLY");
    expect(evidence.calibration_gate.failure_label).toBe("ranking_safety_regression");
    expect(evidence.calibration_gate.degradation_multiple_of_limit).toBeCloseTo(24.3566, 4);
  });

  it("fails closed on unknown evidence fields", () => {
    const drifted = { ...evidenceJson, invented_result: "adaptive_wins_everywhere" };

    expect(() => evidenceIndexSchema.parse(drifted)).toThrow();
  });
});
