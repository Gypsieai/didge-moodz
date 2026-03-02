import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from trend_monitor import TrendMonitor

async def test_trends():
    print("Initializing TrendMonitor...")
    monitor = TrendMonitor()
    
    print("\nFetching all trends (merging Apify, Firecrawl, and Demo)...")
    try:
        trends = await monitor.get_all_trends()
        
        print(f"\nFetched {len(trends['sounds'])} sounds and {len(trends['hashtags'])} hashtags.")
        print(f"Fetched at: {trends['fetched_at']}")
        
        if trends['recommendations']:
            print(f"\nTop Recommendation: {trends['recommendations'][0]['action']}")
            
        print("\nSuccess! Trend monitoring pipeline is operational.")
        
    except Exception as e:
        print(f"\n[ERROR] Trend monitoring failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_trends())
