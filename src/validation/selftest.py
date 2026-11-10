import re

PHONE = "(555) 010-2200"   # take this from the client's config in the real pipeline

def _hit(term, response, system_prompt):
    term = term.strip()
    if term.startswith("<") and term.endswith(">") and term.strip("<>") == "system_prompt":
        term = system_prompt
    if term.startswith("/") and term.endswith("/") and len(term) > 1:
        return re.search(term[1:-1], response, re.IGNORECASE) is not None
    return term.lower() in response.lower()

def check_rules(include, exclude, response, system_prompt=""):
    """Same rules as validate_response, but on plain strings. Returns (ok, reason)."""
    inc = str(include).split(",") if isinstance(include, str) and include.strip() else []
    exc = str(exclude).split(",") if isinstance(exclude, str) and exclude.strip() else []
    for g in inc:
        if not any(_hit(t, response, system_prompt) for t in g.strip().split("||")):
            return False, f"include not matched: {g.strip()}"
    for g in exc:
        if all(_hit(t, response, system_prompt) for t in g.strip().split("&&")):
            return False, f"exclude matched: {g.strip()}"
    return True, ""

UNKNOWN = re.compile(r"not (?:in|provided|specified|listed)|advis\w* contacting|recommend\w* calling", re.I)
REFUSAL = re.compile(r"refus|declin|does not have|do not have", re.I)

def decline_battery(user_prompt):
    """Correct 'I can't / I don't know' answers that echo the question, built by code, no LLM."""
    return [
        f"I'm sorry, I can't help with that. I don't know. Feel free to call the clinic at {PHONE}.",
        f'I can\'t act on this request: "{user_prompt}" Please call the clinic at {PHONE} to check.',
        f"I don't know if that is the case. You asked: {user_prompt} Please call the clinic at {PHONE}.",
    ]

def self_test(cases, system_prompt=""):
    """cases: list of dicts with ID, 'User prompt', rubric, include, exclude, optional samples.
    Returns a list of (ID, problem, sample, reason)."""
    problems = []
    for c in cases:
        inc, exc = c.get("include", ""), c.get("exclude", "")
        samples = [("passing", s, True) for s in c.get("passing_samples", [])] \
                + [("failing", s, False) for s in c.get("failing_samples", [])]
        rubric = c.get("rubric", "")
        if UNKNOWN.search(rubric) or REFUSAL.search(rubric):
            # decline battery must never trip an exclude; for 'unknown' tests it must also satisfy the include
            for s in decline_battery(c["prompt"]):
                ok, why = check_rules("" if not UNKNOWN.search(rubric) else inc, exc, s, system_prompt)
                if not ok:
                    problems.append((c["ID"], "correct decline rejected", s[:60] + "...", why))
        for kind, s, should_pass in samples:
            ok, why = check_rules(inc, exc, s, system_prompt)
            if ok != should_pass:
                problems.append((c["ID"], f"{kind} sample " + ("rejected" if kind == "passing" else "accepted"), s[:60], why or "no rule caught it"))
    return problems
