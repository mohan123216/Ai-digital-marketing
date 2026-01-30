# create_initial_data.py - Populate initial benchmarks
from database import insert_benchmark

# Sample benchmark data
benchmarks = [
    # Ecommerce benchmarks
    {"platform": "Facebook", "industry": "ecommerce", "metric": "CTR", "value": 1.91, "creative_insight": "Use carousel ads for product showcases"},
    {"platform": "Facebook", "industry": "ecommerce", "metric": "CPC", "value": 0.45, "creative_insight": "Video ads have lower CPC"},
    {"platform": "Instagram", "industry": "ecommerce", "metric": "CTR", "value": 0.80, "creative_insight": "Stories perform better than feed posts"},
    {"platform": "Google Ads", "industry": "ecommerce", "metric": "CTR", "value": 3.17, "creative_insight": "Use negative keywords to improve targeting"},
    
    # SaaS benchmarks
    {"platform": "Facebook", "industry": "saas", "metric": "CTR", "value": 2.41, "creative_insight": "Demo videos increase engagement"},
    {"platform": "LinkedIn", "industry": "saas", "metric": "CPC", "value": 8.50, "creative_insight": "Target by job title for better results"},
    {"platform": "Google Ads", "industry": "saas", "metric": "CTR", "value": 4.32, "creative_insight": "Use competitor keywords"},
    
    # Healthcare benchmarks
    {"platform": "Facebook", "industry": "healthcare", "metric": "CTR", "value": 3.27, "creative_insight": "Educational content performs well"},
    {"platform": "Google Ads", "industry": "healthcare", "metric": "CPC", "value": 2.62, "creative_insight": "Local targeting reduces costs"},
]

def populate_benchmarks():
    print("📊 Populating benchmark database...")
    count = 0
    for benchmark in benchmarks:
        try:
            insert_benchmark(benchmark)
            count += 1
            print(f"✅ Added benchmark: {benchmark['platform']} - {benchmark['metric']}")
        except Exception as e:
            print(f"❌ Failed to add benchmark: {e}")
    
    print(f"\n✅ Successfully added {count} benchmark entries")

if __name__ == "__main__":
    populate_benchmarks()