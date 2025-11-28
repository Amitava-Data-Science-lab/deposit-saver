# Housing Goal Agent Tests

Unit tests for the `housing_goalagent`.

## Files

- `test_housinggoal.py` - Tests the housing goal agent with 15 different user input scenarios

## Test Coverage

The tests validate the agent's ability to:
1. Extract postcodes from user input (HP12, SW1, M1, EC1, W1, NW1)
2. Identify property types (1-bed flat, 2-bed flat, 2-bed house, 3-bed house)
3. Call `property_price_search` to get house prices
4. Call `deposit_calculator` to calculate 10% deposit
5. Return properly formatted JSON responses

## Test Examples

- "I want to buy a 2-bed flat in HP12"
- "I'm looking for a 3-bed house in M1"
- "Can I afford a 1-bed flat in W1?"
- "What would a 3-bed house cost in HP12?"
- "Help me find a 2-bed flat in NW1"
- And 10 more variations...

## Running the Tests

### Current Status

The tests are **ready but require Google ADK configuration** to run properly.

The Google ADK `InMemoryRunner` requires:
1. Proper session management
2. App name configuration that matches agent directory structure
3. The agent to be saved/loaded from the correct app directory

### To Run Tests

Once you have properly configured the Google ADK environment and saved your agent:

```bash
cd "c:\Users\debam\OneDrive\Documents\GitHub\Data Science\deposit-saver"
".venv/Scripts/python.exe" -m unittest tests.test_housinggoal -v
```

Or run a single test:

```bash
".venv/Scripts/python.exe" -m unittest tests.test_housinggoal.TestHousingGoalAgent.test_user_wants_2bed_flat_hp12 -v
```

## Alternative: Direct Agent Testing

If you want to test the agent directly without the runner framework, you can:

1. Import the agent
2. Call the tools directly with test data
3. Validate the tool outputs

Example:

```python
from src.tools.WebSearch import property_price_search
from src.tools.FinancialTools import deposit_calculator

# Test the tools
price = property_price_search("HP12", "2-bed flat")
assert price == 200000

deposit = deposit_calculator(price)
assert deposit == 20000
```

## Expected Output Format

Each test expects the agent to return JSON like:

```json
{
  "postcode": "HP12",
  "property_type": "2-bed flat",
  "house_price": 200000,
  "deposit": 20000
}
```

## Notes

- The test file uses `InMemoryRunner` from `google.adk.runners`
- Tests create unique session IDs for each run
- The agent is configured with temperature=0 for deterministic outputs
- All 15 tests cover different combinations of postcodes and property types with various input phrasings
