"""Gamification system: Missions, XP Points, Achievement Badges, Daily Challenges, Milestones, and Progress Map."""

from datetime import datetime, timezone
import hashlib
from typing import Any
from .models import AchievementBadge, MissionMapNode


DIFFICULTY_BASE_XP: dict[str, int] = {
    "beginner": 100,
    "easy": 120,
    "medium": 150,
    "hard": 200,
    "advanced": 250,
}

SOLO_BONUS_XP = 50       # Extra points awarded for independent solving (0 hints used)
DAILY_BONUS_XP = 50      # Bonus points for completing today's daily mission

LEVEL_MILESTONES = [
    (1, "Novice Coder", 0, 150),
    (2, "Code Apprentice", 150, 350),
    (3, "Script Adventurer", 350, 700),
    (4, "Python Knight", 700, 1200),
    (5, "Algorithm Wizard", 1200, 2000),
    (6, "Grandmaster Coder", 2000, 999999),
]

MISSION_TITLES: dict[str, str] = {
    "add-numbers": "Mission 01: The Calculator Calamity",
    "is-even": "Mission 02: The Even Number Enigma",
    "reverse-text": "Mission 03: The String Inverter",
    "count-vowels": "Mission 04: The Vowel Vault",
    "fizz-buzz": "Mission 05: The FizzBuzz Protocol",
    "sum-list": "Mission 06: Fix the Broken Loop",
    "say-hello": "Mission 07: The Greeting Gateway",
    "double-number": "Mission 08: The Multiplier Engine",
    "rectangle-area": "Mission 09: The Geometry Blueprint",
    "last-character": "Mission 10: The Index Investigator",
    "larger-number": "Mission 11: The Duel of Numbers",
    "absolute-value": "Mission 12: Distance from Zero",
    "count-positive": "Mission 13: Positive Charge Sentinel",
    "palindrome": "Mission 14: The Mirror Dimension",
    "word-count": "Mission 15: The Lexicon Counter",
    "largest-item": "Mission 16: The Apex Seeker",
    "make-initials": "Mission 17: The Identity Cryptographer",
    "second-largest": "Mission 18: The Runner-Up Trial",
    "longest-word": "Mission 19: The Colossal Lexicon",
    "compress-runs": "Mission 20: The Stream Compressor",
    "balanced-parentheses": "Mission 21: The Symmetry Sanctuary",
    "is-prime": "Mission 22: The Prime Number Detective",
}

DEFAULT_MISSION_STEPS = [
    "Find the mistake & inspect requirements",
    "Request hints if needed (Zero hints earn +50 Solo XP!)",
    "Correct the program in the editor",
    "Pass all test cases",
    "Unlock the next mission & earn achievement badges",
]


def get_mission_number_and_title(challenge_id: str, index: int, title: str) -> tuple[int, str]:
    mission_num = index + 1
    if challenge_id in MISSION_TITLES:
        return mission_num, MISSION_TITLES[challenge_id]
    num_str = str(mission_num).padStart(2, "0") if hasattr(str(mission_num), "padStart") else f"{mission_num:02d}"
    return mission_num, f"Mission {num_str}: {title}"


def get_daily_challenge(challenges: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not challenges:
        return None
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = int(hashlib.sha256(today.encode("utf-8")).hexdigest(), 16)
    idx = seed % len(challenges)
    return challenges[idx]


def calculate_challenge_xp(
    difficulty: str,
    hints_used: int,
    is_daily: bool = False,
    already_solved: bool = False,
) -> tuple[int, bool, int]:
    """Calculate XP awarded for a solution attempt.
    
    Returns: (xp_awarded, is_solo_bonus, stars)
    Unique twist: Students who solve independently (0 hints) earn full base XP
    PLUS 50 Solo Bonus XP and 3 stars!
    Revealing hints scales down points to encourage independent problem solving.
    """
    base_xp = DIFFICULTY_BASE_XP.get(difficulty.lower(), 100)
    
    if hints_used == 0:
        multiplier = 1.0
        solo_bonus = True
        stars = 3
    elif hints_used == 1:
        multiplier = 0.8
        solo_bonus = False
        stars = 2
    elif hints_used == 2:
        multiplier = 0.65
        solo_bonus = False
        stars = 2
    else:
        multiplier = 0.5
        solo_bonus = False
        stars = 1

    earned = int(base_xp * multiplier)
    if solo_bonus:
        earned += SOLO_BONUS_XP

    if is_daily:
        earned += DAILY_BONUS_XP

    if already_solved:
        earned = max(15, int(earned * 0.25))

    return earned, solo_bonus, stars


def get_level_info(total_xp: int) -> tuple[int, str, int, int]:
    for level, name, min_xp, next_xp in LEVEL_MILESTONES:
        if min_xp <= total_xp < next_xp:
            progress_pct = int(((total_xp - min_xp) / max(1, next_xp - min_xp)) * 100)
            return level, name, next_xp, min(100, max(0, progress_pct))
    return 6, "Grandmaster Coder", 999999, 100


def calculate_gamification_state(
    learner_id: str,
    attempts: list[dict[str, Any]],
    all_challenges: list[dict[str, Any]],
    hint_positions: dict[str, int],
) -> dict[str, Any]:
    daily_challenge = get_daily_challenge(all_challenges)
    daily_id = daily_challenge["id"] if daily_challenge else None
    daily_title = daily_challenge["title"] if daily_challenge else None

    # Group attempts by challenge
    challenge_attempts: dict[str, list[dict[str, Any]]] = {}
    for a in attempts:
        ch_id = a["challenge_id"]
        challenge_attempts.setdefault(ch_id, []).append(a)

    solved_challenges: set[str] = set()
    solo_solves: set[str] = set()
    first_try_aces: set[str] = set()
    bug_hunter_solves: set[str] = set()
    
    total_xp = 0
    daily_completed = False
    mission_stars: dict[str, int] = {}
    mission_xp: dict[str, int] = {}

    challenges_by_id = {c["id"]: c for c in all_challenges}

    # Track submission dates for streak
    active_dates: set[str] = set()

    for ch_id, rows in challenge_attempts.items():
        ch = challenges_by_id.get(ch_id)
        if not ch:
            continue
        difficulty = ch.get("difficulty", "beginner")
        hints_used = hint_positions.get(ch_id, 0)
        
        # Sort rows chronologically
        sorted_rows = sorted(rows, key=lambda x: str(x.get("submitted_at", "")))
        has_passed = any(r.get("passed") for r in sorted_rows)
        
        if has_passed:
            solved_challenges.add(ch_id)
            if hints_used == 0:
                solo_solves.add(ch_id)
            
            # Check if solved on first attempt
            if sorted_rows[0].get("passed"):
                first_try_aces.add(ch_id)
            else:
                bug_hunter_solves.add(ch_id)

            is_daily_mission = (ch_id == daily_id)
            earned_xp, is_solo, stars = calculate_challenge_xp(difficulty, hints_used, is_daily=is_daily_mission)
            total_xp += earned_xp
            mission_stars[ch_id] = stars
            mission_xp[ch_id] = earned_xp

            if is_daily_mission:
                daily_completed = True

        for r in sorted_rows:
            if r.get("passed") and r.get("submitted_at"):
                dt_str = str(r["submitted_at"])[:10]
                active_dates.add(dt_str)

    # Calculate streak (consecutive days leading up to today)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_streak = 1 if today_str in active_dates else (len(active_dates) if active_dates else 0)

    current_level, level_name, next_level_xp, level_progress_pct = get_level_info(total_xp)

    # Build Badges
    badges_def = [
        {
            "id": "first_mission",
            "name": "First Mission Clear",
            "description": "Successfully completed your first Python mission.",
            "icon": "flag",
            "unlocked": len(solved_challenges) >= 1,
        },
        {
            "id": "solo_maverick",
            "name": "Solo Maverick",
            "description": "Solved a challenge with zero hints used (Pure independence +50 Bonus XP!).",
            "icon": "medal",
            "unlocked": len(solo_solves) >= 1,
        },
        {
            "id": "bug_hunter",
            "name": "Bug Hunter",
            "description": "Turned a failed attempt into a passing solution through perseverance.",
            "icon": "spark",
            "unlocked": len(bug_hunter_solves) >= 1,
        },
        {
            "id": "first_try_ace",
            "name": "First-Try Ace",
            "description": "Passed all test cases on your very first submission.",
            "icon": "diamond",
            "unlocked": len(first_try_aces) >= 1,
        },
        {
            "id": "triple_solo",
            "name": "Triple Threat",
            "description": "Solved 3 distinct challenges completely solo with zero hints.",
            "icon": "mountain",
            "unlocked": len(solo_solves) >= 3,
        },
        {
            "id": "daily_champion",
            "name": "Daily Champion",
            "description": "Conquered today's featured Daily Challenge.",
            "icon": "compass",
            "unlocked": daily_completed,
        },
        {
            "id": "python_veteran",
            "name": "Python Veteran",
            "description": "Conquered 5 or more coding missions across the Python realm.",
            "icon": "terminal",
            "unlocked": len(solved_challenges) >= 5,
        },
    ]

    badges = [AchievementBadge(**b) for b in badges_def]

    # Build Progress Map
    progress_map: list[MissionMapNode] = []
    from .unlocks import lock_reason

    current_found = False
    for idx, ch in enumerate(all_challenges):
        ch_id = ch["id"]
        mission_num = idx + 1
        is_solved = ch_id in solved_challenges
        reason = lock_reason(ch, all_challenges, attempts)
        is_locked = bool(reason)

        if is_solved:
            status = "completed"
        elif not is_locked and not current_found:
            status = "current"
            current_found = True
        elif not is_locked:
            status = "available"
        else:
            status = "locked"

        stars = mission_stars.get(ch_id, 0)
        xp_earned = mission_xp.get(ch_id, 0)
        is_daily_item = (ch_id == daily_id)

        progress_map.append(MissionMapNode(
            mission_number=mission_num,
            challenge_id=ch_id,
            title=ch["title"],
            difficulty=ch.get("difficulty", "beginner"),
            status=status,
            stars=stars,
            xp_earned=xp_earned,
            is_daily=is_daily_item,
        ))

    return {
        "total_xp": total_xp,
        "current_level": current_level,
        "level_name": level_name,
        "next_level_xp": next_level_xp,
        "level_progress_pct": level_progress_pct,
        "daily_challenge_id": daily_id,
        "daily_challenge_title": daily_title,
        "daily_challenge_completed": daily_completed,
        "daily_streak": daily_streak,
        "badges": badges,
        "progress_map": progress_map,
        "mission_stars": mission_stars,
    }
