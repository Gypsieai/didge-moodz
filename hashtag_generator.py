"""
DIDGERI-BOOM Hashtag & Caption Generator
AI-powered hashtag strategy and engaging caption generation.
"""

import random
from datetime import datetime

from config import CORE_HASHTAGS, VIRAL_HASHTAGS


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

    def generate_caption(
        self,
        content_type: str = "general",
        trend_name: str = "",
        include_cta: bool = True,
    ) -> str:
        """Generate an engaging caption for a TikTok video."""
        templates = {
            "cover": [
                f"Didgeridoo cover of '{trend_name}' 🎵🔥 Did NOT expect this to work so well!",
                f"Playing '{trend_name}' on the didgeridoo and it SLAPS 💥",
                f"When the didgeridoo meets '{trend_name}' 🤯 This combo is insane",
                f"'{trend_name}' but make it didgeridoo 🎶 Turn your volume UP 🔊",
            ],
            "reaction": [
                "Wait for the didgeridoo drop 🔥 This is what 20 years of practice sounds like",
                "People didn't expect THIS when I pulled out the didgeridoo 😱",
                "The look on their faces when the drone hit 💀🎵",
            ],
            "tutorial": [
                "How to play didgeridoo in 60 seconds ⏰ Save this!",
                "Secret technique that took me years to learn 🤫 #tutorial",
                "You've been breathing wrong this whole time 🫁 Circular breathing explained",
            ],
            "mashup": [
                f"Didgeridoo × '{trend_name}' mashup you didn't know you needed 🎧",
                "Ancient instrument meets modern beats 🌍🎶 The result is INSANE",
                "This mashup broke my brain 🤯 Didgeridoo bass hits different",
            ],
            "asmr": [
                "Close your eyes and let the drone take you somewhere 🌙✨ #ASMR",
                "The most relaxing didgeridoo session you'll hear today 😴🎵",
                "Pure didgeridoo ASMR — this is what peace sounds like 🕊️",
            ],
            "street_performance": [
                "Their reactions when they hear the didgeridoo for the first time 😂🔥",
                "Busking with a didgeridoo — people literally stopped in their tracks 👀",
                "Street music that makes people forget where they're going 🎶",
            ],
            "challenge": [
                f"Can I play '{trend_name}' on a DIDGERIDOO? Challenge accepted 💪",
                "They said it couldn't be done on a didgeridoo. Watch this 😤🔥",
            ],
            "general": [
                "This sound is 40,000 years old and it still goes HARD 🔥",
                "POV: You discover the didgeridoo isn't just a tube 🤯",
                "The world's oldest instrument and it still slaps harder than anything 🎵💥",
                "One breath, one drone, infinite vibes 🌊🎶",
                "They weren't ready for this 😮‍💨🔥",
            ],
        }

        options = templates.get(content_type, templates["general"])
        caption = random.choice(options)

        if include_cta:
            ctas = [
                "\n\nFollow for more didgeridoo magic ✨",
                "\n\n🔔 Follow to never miss a session!",
                "\n\nDrop a 🔥 if you felt that!",
                "\n\nShare this with someone who needs to hear this 🎶",
                "\n\nWho should I collab with next? 👇",
            ]
            caption += random.choice(ctas)

        return caption

    def generate_full_post(
        self,
        content_type: str = "general",
        trend_name: str = "",
        trend_tags: list[str] = None,
    ) -> dict:
        """Generate a complete post package: caption + hashtags."""
        caption = self.generate_caption(content_type, trend_name)
        hashtags = self.generate_hashtags(trend_tags)

        return {
            "caption": caption,
            "hashtags": hashtags,
            "full_text": f"{caption}\n\n{' '.join(hashtags)}",
            "content_type": content_type,
            "generated_at": datetime.now().isoformat(),
        }
