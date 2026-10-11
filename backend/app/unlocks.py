"""Practice unlocks: finish every challenge in earlier nonempty levels."""
LEVELS = ["beginner", "easy", "medium", "hard", "advanced"]

def lock_reason(challenge, challenges, attempts):
    solved = {row["challenge_id"] for row in attempts if row["passed"]}
    for level in LEVELS[:LEVELS.index(challenge["difficulty"])]:
        remaining = [row for row in challenges if row["difficulty"] == level and row["id"] not in solved]
        if remaining:
            return f"Complete all {level} challenges to unlock this level."
    return None
