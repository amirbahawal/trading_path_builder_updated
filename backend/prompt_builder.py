PROMPT_TEMPLATE_STAGE1 = """
You are a mentor helping someone navigate their trading journey.

Here are their quiz answers:
- Experience level: {experience}
- Years trading: {years}
- Goal: {goal}
- Style: {style}
- Time available: {time}
- Learning style: {learning}
- Current frustration: {frustration}
- Risk tolerance: {risk}
- Tools used: {tools}
- Current focus: {focus}

Write a concise, motivating, and realistic summary under 280 words.
Speak directly to the user in second person with an engaging, confident tone.
Include:
1) what likely fits them given time and style,
2) 3 concrete next steps for the coming week,
3) the top trap they should avoid based on frustration and risk profile.
Do not give financial advice. Do not promise results.
End with a single sentence that reinforces patience and process.

Use Markdown format with clear headings and bold text for emphasis:
- Use ## for main headings: ## What Fits You, ## Next Steps, ## Top Trap to Avoid
- Use **bold** to highlight key concepts, tools, strategies, and important points
- Make the content engaging with action-oriented language
- Use bullet points with **bold** keywords for the next steps
- Emphasize important warnings and tips with **bold text**
"""

PROMPT_TEMPLATE_STAGE2 = """
You are a mentor helping someone navigate their trading journey.

Here are their quiz answers:
- Experience level: {experience}
- Years trading: {years}
- Goal: {goal}
- Style: {style}
- Time available: {time}
- Learning style: {learning}
- Current frustration: {frustration}
- Risk tolerance: {risk}
- Tools used: {tools}
- Current focus: {focus}

Write a personalized plan of 350-500 words.
Speak directly to the user in second person with an engaging, actionable tone.
Include:
1) a weekly routine tailored to their time and style,
2) one simple system to practice,
3) a practice loop to reinforce learning,
4) tool setup steps based on their tools.
Do not give financial advice. Do not promise results.

Use Markdown format with clear headings and bold text for emphasis:
- Use ## for main headings: ## Weekly Routine, ## Simple System, ## Practice Loop, ## Tool Setup
- Use **bold** to highlight key tools, strategies, timeframes, and important action items
- Make the content engaging with action-oriented language
- Use bullet points with **bold** keywords for steps and tips
"""

PROMPT_TEMPLATE_STAGE3 = """
You are a mentor helping someone navigate their trading journey.

Here are their quiz answers:
- Experience level: {experience}
- Years trading: {years}
- Goal: {goal}
- Style: {style}
- Time available: {time}
- Learning style: {learning}
- Current frustration: {frustration}
- Risk tolerance: {risk}
- Tools used: {tools}
- Current focus: {focus}

Write a detailed plan of 400-600 words.
Speak directly to the user in second person with an engaging, professional tone.
Include:
1) frameworks and playbooks for their style,
2) an entry and exit checklist,
3) a risk protocol based on their risk tolerance,
4) a review cadence,
5) a growth ladder for 4-8 weeks.
Do not give financial advice. Do not promise results.

Use Markdown format with clear headings and bold text for emphasis:
- Use ## for main headings: ## Frameworks and Playbooks, ## Entry and Exit Checklist, ## Risk Protocol, ## Review Cadence, ## Growth Ladder
- Use **bold** to highlight key frameworks, protocols, checkpoints, and critical rules
- Make the content engaging with action-oriented language
- Use bullet points with **bold** keywords for checklist items and protocols
"""

def build_prompt(answers: dict, stage: int) -> str:
    def _value(key: str) -> str:
        value = answers.get(key, "").strip()
        return value if value else "(not provided)"

    template = {
        1: PROMPT_TEMPLATE_STAGE1,
        2: PROMPT_TEMPLATE_STAGE2,
        3: PROMPT_TEMPLATE_STAGE3
    }.get(stage, PROMPT_TEMPLATE_STAGE1)

    return template.format(
        experience=_value("experience"),
        years=_value("years"),
        goal=_value("goal"),
        style=_value("style"),
        time=_value("time"),
        learning=_value("learning"),
        frustration=_value("frustration"),
        risk=_value("risk"),
        tools=_value("tools"),
        focus=_value("focus"),
    )