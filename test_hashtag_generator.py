"""
Test script for verifying the new ADK-powered HashtagGenerator.
"""

from hashtag_generator import HashtagGenerator

def main():
    generator = HashtagGenerator()
    
    print("Testing ADK ViralContentAgent Pipeline...\n")
    print("Requesting content for a street_performance video...")
    
    try:
        # Note: This will make a real LLM call if GOOGLE_API_KEY is properly set
        result = generator.generate_full_post(
            content_type="street_performance",
            trend_name="Epic Didgeridoo Busking",
            trend_tags=["busking", "didgeridoo", "livemusic"]
        )
        
        print("\n=== GENERATED POST ===")
        print(f"Caption:\n{result['caption']}")
        print(f"\nHashtags:\n{result['hashtags']}")
        print(f"\nFull Text:\n{result['full_text']}")
        print("======================\n")
        print("Success! The ADK agent responded correctly.")
        
    except Exception as e:
        print(f"\n[ERROR] The test failed: {e}")
        print("Ensure GOOGLE_API_KEY and GOOGLE_GENAI_USE_VERTEXAI are configured correctly.")

if __name__ == "__main__":
    main()
