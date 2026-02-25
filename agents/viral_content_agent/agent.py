"""
ADK Agent definition for the Viral Content Generator.
Replaces static templates with a Generator-Critic LLM pipeline.
"""
from __future__ import annotations

from google.adk.agents import LlmAgent, SequentialAgent

draft_writer = LlmAgent(
    name="draft_writer",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert TikTok social media manager for Warren, an energetic "
        "and talented didgeridoo player. Your task is to write engaging, viral "
        "TikTok captions and propose a list of relevant hashtags based on the "
        "user's request. The content should always fit the vibe of 'Cinematic Delight' "
        "- high-energy, professional, and exciting. Keep captions short and punchy."
    )
)

reviewer = LlmAgent(
    name="reviewer",
    model="gemini-2.5-flash",
    instruction=(
        "You are a Senior Content Editor specializing in TikTok. Review the "
        "drafted caption and hashtags provided. Ensure the copy is natural, "
        "enthusiastic, and includes a strong Call to Action (CTA). Verify "
        "that the hashtags are relevant and optimized for reach.\n\n"
        "You MUST output exactly a JSON code block containing the keys "
        "'caption' and 'hashtags' (which should be a string of space-separated "
        "hashtags) so the system can parse your response. Provide ONLY the "
        "JSON block and no other conversational text."
    )
)

root_agent = SequentialAgent(
    name="viral_content_agent",
    agents=[draft_writer, reviewer],
)
