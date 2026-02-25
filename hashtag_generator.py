"""
DIDGERI-BOOM Hashtag & Caption Generator
AI-powered hashtag strategy and engaging caption generation.
"""

import asyncio
import json
import re
from datetime import datetime

from config import CORE_HASHTAGS, VIRAL_HASHTAGS
from google.adk.runners import InMemoryRunner

# Assuming the agents package is importable from where this runs
import agents.viral_content_agent.agent as viral_agent


class HashtagGenerator:
    """Generates optimized hashtags and captions for TikTok posts."""

    def __init__(self):
        self.used_combos = []

    def generate_hashtags(
        self,
        trend_tags: list[str] = None,
        max_tags: int = 12,
    ) -> list[str]:
        """Generate an optimized set of hashtags."""
        tags = set()

        # Always include 3-4 core niche hashtags
        core_sample = random.sample(CORE_HASHTAGS, min(4, len(CORE_HASHTAGS)))
        tags.update(core_sample)

        # Add 3-4 viral/discovery hashtags
        viral_sample = random.sample(VIRAL_HASHTAGS, min(4, len(VIRAL_HASHTAGS)))
        tags.update(viral_sample)

        # Add trend-specific tags
        if trend_tags:
            for tag in trend_tags[:4]:
                clean = f"#{tag.lstrip('#')}"
                tags.add(clean)

        # Cap at max_tags
        result = list(tags)[:max_tags]
        return result

        return result

    def _parse_agent_response(self, text: str) -> dict:
        """Extracts JSON from the agent's response text."""
        try:
            # Try to find a JSON block if the agent wrapped it in markdown
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback if no valid JSON is returned
            return {
                "caption": "Check out this new didgeridoo video! 🔥🎵",
                "hashtags": "#didgeridoo #music #live",
            }

    async def _async_generate_full_post(self, content_type: str, trend_name: str, trend_tags: list[str]) -> dict:
        runner = InMemoryRunner(agent=viral_agent.root_agent, app_name="didge_moodz")
        
        # We use a static system user for automation
        session = await runner.session_service.create_session(
            app_name="didge_moodz", user_id="system"
        )
        
        prompt = (
            f"Please generate a TikTok caption and hashtags for a new video.\n"
            f"Content Type: {content_type}\n"
        )
        if trend_name:
            prompt += f"Related Trend: {trend_name}\n"
        if trend_tags:
            prompt += f"Suggested Trend Tags: {', '.join(trend_tags)}\n"

        # The runner returns an async generator for live streaming, 
        # or we can collect events. 
        # But `run` or `run_async` API might be slightly different.
        # Let's collect the final text response.
        final_text = ""
        async for event in runner.run_async(session.id, prompt):
            if event.type == "model_response" and event.data.text:
                final_text += event.data.text

        agent_output = final_text.strip()
        parsed_data = self._parse_agent_response(agent_output)
        
        caption = parsed_data.get("caption", "Incredible didgeridoo vibes 🦘🔥")
        hashtags_str = parsed_data.get("hashtags", "")
        # Get baseline hashtags as fallback/addition
        baseline_hashtags = self.generate_hashtags(trend_tags)
        
        if not hashtags_str:
            hashtags_str = " ".join(baseline_hashtags)
            
        full_text = f"{caption}\n\n{hashtags_str}"
        
        return {
            "caption": caption,
            "hashtags": hashtags_str.split(),
            "full_text": full_text,
            "content_type": content_type,
            "generated_at": datetime.now().isoformat(),
        }

    def generate_full_post(
        self,
        content_type: str = "general",
        trend_name: str = "",
        trend_tags: list[str] = None,
    ) -> dict:
        """Generate a complete post package: caption + hashtags."""
        return asyncio.run(
            self._async_generate_full_post(content_type, trend_name, trend_tags)
        )

