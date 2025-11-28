import sys
import os
import asyncio
# ----------------- PATH FIX START -----------------
# 1. Get the path to the current directory (tests)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Go up one level to the project root (deposit-saver)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..')) 

# 3. Add the project root to the path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------- PATH FIX END -----------------



from src.tools.WebSearch import outcode_checker, nearby_outcodes
from src.agent.FinancialInstrument import call_vsearch_agent_async


def main():
    response = outcode_checker("HP12")
    print(response)

    response = nearby_outcodes("HP12")
    print("Nearby Outcodes:")
    print(response)

async def search_web():
    query = """
    I want to save 250 GBP every months. Give me top 3 savings accounts for savings this amount monthly"
    """
    response = await call_vsearch_agent_async(query)


if __name__ == "__main__":
    asyncio.run(search_web())