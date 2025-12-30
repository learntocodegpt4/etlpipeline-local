import asyncio
import os
from src.orchestrator.state_manager import StateManager

async def main():
    # Use a test DB path to avoid touching real DB
    os.makedirs('data', exist_ok=True)
    sm = StateManager(db_path='data/test_etl_state.db')
    await sm.initialize()
    try:
        stats = await sm.get_recent_job_stats(days=7)
        print('STATS:', stats)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
