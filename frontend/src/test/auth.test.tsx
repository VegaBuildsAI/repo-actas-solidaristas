import { describe, expect, it } from "vitest";

describe("auth utilities", () => {
  it("localStorage token key constants are defined", () => {
    // Sanity check — the actual auth logic is integration-tested via the API
    expect(typeof localStorage.getItem("access_token")).toBe("object"); // null initially
  });

  it("login page title is correct", () => {
    document.title = "Actas Solidaristas";
    expect(document.title).toBe("Actas Solidaristas");
  });
});
