#!/usr/bin/env python3
"""Test script to verify penalties API integration"""

import asyncio
import json
from src.config.settings import get_settings
from src.extract.api_client import APIClient


async def test_penalties_api():
    """Test penalties extraction directly from FWC API"""
    settings = get_settings()
    
    print("=" * 80)
    print("Testing Penalties API Extraction")
    print("=" * 80)
    
    # Test with multiple awards
    test_awards = ["MA000120", "MA000004", "MA000029", "MA000001"]
    
    async with APIClient(
        base_url=settings.fwc_api_base_url,
        api_key=settings.fwc_api_key
    ) as client:
        for award_code in test_awards:
            print(f"\n Testing {award_code}...")
            try:
                response = await client.get_penalties(award_code, page=1, limit=10)
                
                result_count = response.get('_meta', {}).get('result_count', 0)
                page_count = response.get('_meta', {}).get('page_count', 0)
                has_more = response.get('_meta', {}).get('has_more_results', False)
                results = response.get('results', [])
                
                print(f"   Result count: {result_count}, Pages: {page_count}, Has more: {has_more}")
                print(f"   Returned {len(results)} records in this page")
                
                if result_count > 0:
                    print(f"   ✓ {award_code} HAS penalties data!")
                    if results:
                        print(f"   First record keys: {list(results[0].keys())}")
                else:
                    print(f"   ⚠ {award_code} has NO penalties in FWC API")
                    
            except Exception as e:
                print(f"   ✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_penalties_api())

