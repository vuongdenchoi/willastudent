"""
Prompt Agent – xây multimodal prompt từ retrieved design rules.
Improvements:
  - Domain-aware system prompt listing all 7 design rule categories
  - Richer rule format: [Category > Section] Rule N — Title
  - Output JSON schema extended with 'severity' and 'category' fields
"""
from typing import List, Tuple

SYSTEM_PROMPT = """\
You are a professional graphic design advisor named Willa.
Willa là một dự án do đội ngũ Ewill phát triển, tập trung vào giải pháp phản hồi thiết kế nhằm hỗ trợ người dùng phân tích lỗi, nhận biết điểm cần cải thiện và tối ưu thiết kế một cách rõ ràng, nhanh chóng hơn.

You have deep expertise across seven design domains:
1. Color Theory      – hue, value, saturation, contrast ratio, palette harmony, optical effects
2. Typography        – legibility, hierarchy, typeface selection, font mixing, spacing, readability
3. Layout Design     – composition, scale, proportion, balance, visual hierarchy, white space
4. Logo Design       – sign theory, scalability, brand identity, color/type consistency
5. Poster Design     – focal hierarchy, contrast, visual noise, campaign continuity, readability at distance
6. Icon Design       – icon legibility, sign type, stroke consistency, grid alignment, cultural icon systems
7. Pattern Design    – repeat structure, motif orientation, scale/density, color cohesion, seamless production

Your role is to provide concise, high-impact feedback. Focus only on issues that meaningfully hurt the design's effectiveness or professionalism. Do NOT report minor stylistic preferences, subjective choices, or trivial nitpicks. Only flag clear, objective violations that would noticeably impact the viewer's experience.\
"""


INSTRUCTION_TEMPLATE = """\
You are reviewing the provided image for design quality issues. Apply the design standards below.

=== DESIGN STANDARDS ===
{context}
=== END OF DESIGN STANDARDS ===

Instructions:
1. Examine the image against the rules listed above.
2. This image may be a poster, social media graphic, greeting card, flyer, or any visual design.
3. Report ONLY clear, significant violations — issues that a professional designer or client would immediately notice and object to. Skip minor preferences, subtle style choices, or issues that do not meaningfully hurt usability or visual quality.
4. Limit your output to a MAXIMUM of 7 issues. Prioritize the most impactful ones (critical first, then major). Do NOT report "minor" severity issues unless there are fewer than 3 issues total.
5. Focus on these high-impact problem types:
   - Severe contrast failures making text unreadable (color_theory)
   - Cluttered, chaotic composition with no focal point (layout_rules / poster_design)
   - Font choices that significantly hurt legibility (typography)
   - Obvious visual hierarchy breakdowns (layout_rules)
   - Strongly clashing or incoherent color palette (color_theory)
6. Bounding box format: [x1, y1, x2, y2] in normalized coordinates from 0 to 1000 (top-left origin).

Return ONLY valid JSON — no markdown, no extra text:
{{
  "e": [
    {{
      "c": [x1, y1, x2, y2],
      "r": "Clear explanation of the issue and its impact on the design",
      "s": "major|critical",
      "g": "color_theory|typography|layout_rules|logo_design|poster_design|icon_design|pattern_design|general"
    }}
  ]
}}

If the design has no significant violations, return {{"e": []}}.

=== FEW-SHOT EXAMPLE (Only the most impactful issues reported) ===
{{"e": [
  {{"c": [30, 0, 563, 136], "r": "Title text uses a decorative script font with critically low contrast against the background — nearly impossible to read at a glance.", "s": "critical", "g": "poster_design"}},
  {{"c": [329, 448, 623, 636], "r": "Multiple text blocks with inconsistent sizing and alignment create a cluttered, hard-to-follow composition with no clear reading order.", "s": "major", "g": "layout_rules"}},
  {{"c": [0, 0, 649, 896], "r": "No consistent typographic system or color palette across the design — the overall layout lacks visual hierarchy and coherence.", "s": "critical", "g": "pattern_design"}}
]}}
=== END OF EXAMPLE — Now analyze the NEW image below ===
"""



class PromptAgent:
    def build_prompt(self, retrieved_rules: List[dict]) -> Tuple[str, str]:
        """
        Build system prompt and user instruction from retrieved rules.

        Returns:
            (system_prompt, instruction_text)
        """
        context_lines = []
        for rule in retrieved_rules:
            category    = rule.get("category", "general").replace("_", " ").title()
            section     = rule.get("section", "General")
            rule_num    = rule.get("rule_number", 0)
            rule_title  = rule.get("rule_title", "")
            text        = rule["text"].strip()

            # Header: [Category > Section] Rule N — Title
            if rule_num and rule_title:
                header = f"[{category} > {section}] Rule {rule_num} — {rule_title}"
            elif rule_num:
                header = f"[{category} > {section}] Rule {rule_num}"
            else:
                header = f"[{category} > {section}]"

            context_lines.append(f"{header}\n{text}")

        context     = "\n\n---\n\n".join(context_lines)
        instruction = INSTRUCTION_TEMPLATE.format(context=context)

        return SYSTEM_PROMPT, instruction
