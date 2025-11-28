"""
Unit tests for the housing_goal_agent.

This test suite tests the agent's ability to respond to user inputs like:
"I want to buy a 2-bed flat in HP12"

The agent should:
1. Extract the postcode and property type from the user input
2. Call property_price_search to get the house price
3. Call deposit_calculator to calculate the deposit
4. Return a JSON response with postcode, property_type, house_price, and deposit
"""

import unittest
import json
from google.adk.runners import InMemoryRunner
from google.genai import types
from src.agent.housinggoal import housing_goalagent


class TestHousingGoalAgent(unittest.TestCase):
    """Test the housing goal agent with realistic user inputs"""

    def setUp(self):
        """Set up the agent runner for testing"""
        self.agent = housing_goalagent

    def parse_agent_response(self, response):
        """Parse the agent's response to extract JSON"""
        # The response might be a string or have a text attribute
        response_text = str(response) if not hasattr(response, 'text') else response.text

        try:
            # If response is already a dict
            if isinstance(response, dict):
                return response

            # Try to parse as JSON directly
            return json.loads(response_text)
        except:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return None

    def run_agent_test(self, user_input):
        """Helper method to run agent with user input"""
        import uuid

        # Create runner with explicit app_name to avoid mismatch
        runner = InMemoryRunner(agent=self.agent, app_name="test_app")

        # Generate unique session ID for each test
        session_id = f"test_session_{uuid.uuid4()}"
        user_id = "test_user"

        # Create a message content
        message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )

        # Run the agent and collect events
        try:
            events = list(runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=message
            ))

            # Get the last response event with content
            for event in reversed(events):
                if hasattr(event, 'content') and event.content:
                    # Try to get text from the content
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                return self.parse_agent_response(part.text)
                    # Fallback to string conversion
                    return self.parse_agent_response(event.content)
        finally:
            runner.close()

        return None

    def test_user_wants_2bed_flat_hp12(self):
        """Test: 'I want to buy a 2-bed flat in HP12'"""
        user_input = "I want to buy a 2-bed flat in HP12"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "HP12")
        self.assertEqual(result["property_type"], "2-bed flat")
        self.assertEqual(result["house_price"], 200000)
        self.assertEqual(result["deposit"], 20000)

    def test_user_wants_1bed_flat_sw1(self):
        """Test: 'I want to buy a 1-bed flat in SW1'"""
        user_input = "I want to buy a 1-bed flat in SW1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "SW1")
        self.assertEqual(result["property_type"], "1-bed flat")
        self.assertEqual(result["house_price"], 100000)
        self.assertEqual(result["deposit"], 10000)

    def test_user_wants_3bed_house_m1(self):
        """Test: 'I'm looking for a 3-bed house in M1'"""
        user_input = "I'm looking for a 3-bed house in M1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "M1")
        self.assertEqual(result["property_type"], "3-bed house")
        self.assertEqual(result["house_price"], 400000)
        self.assertEqual(result["deposit"], 40000)

    def test_user_wants_2bed_house_ec1(self):
        """Test: 'Looking to buy a 2-bed house in EC1'"""
        user_input = "Looking to buy a 2-bed house in EC1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "EC1")
        self.assertEqual(result["property_type"], "2-bed house")
        self.assertEqual(result["house_price"], 300000)
        self.assertEqual(result["deposit"], 30000)

    def test_user_wants_2bed_flat_nw1(self):
        """Test: 'I want a 2 bed flat in NW1'"""
        user_input = "I want a 2 bed flat in NW1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "NW1")
        self.assertEqual(result["property_type"], "2-bed flat")
        self.assertEqual(result["house_price"], 200000)
        self.assertEqual(result["deposit"], 20000)

    def test_user_wants_1bed_flat_w1(self):
        """Test: 'Can I afford a 1-bed flat in W1?'"""
        user_input = "Can I afford a 1-bed flat in W1?"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "W1")
        self.assertEqual(result["property_type"], "1-bed flat")
        self.assertEqual(result["house_price"], 100000)
        self.assertEqual(result["deposit"], 10000)

    def test_user_wants_3bed_house_hp12(self):
        """Test: 'What would a 3-bed house cost in HP12?'"""
        user_input = "What would a 3-bed house cost in HP12?"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "HP12")
        self.assertEqual(result["property_type"], "3-bed house")
        self.assertEqual(result["house_price"], 400000)
        self.assertEqual(result["deposit"], 40000)

    def test_user_wants_2bed_house_sw1(self):
        """Test: 'I'm interested in a 2-bed house in SW1'"""
        user_input = "I'm interested in a 2-bed house in SW1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "SW1")
        self.assertEqual(result["property_type"], "2-bed house")
        self.assertEqual(result["house_price"], 300000)
        self.assertEqual(result["deposit"], 30000)

    def test_user_wants_2bed_flat_different_phrasing(self):
        """Test: 'Help me find a 2-bed flat in HP12'"""
        user_input = "Help me find a 2-bed flat in HP12"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "HP12")
        self.assertEqual(result["property_type"], "2-bed flat")
        self.assertEqual(result["house_price"], 200000)
        self.assertEqual(result["deposit"], 20000)

    def test_user_wants_1bed_flat_question_format(self):
        """Test: 'How much for a 1-bed flat in SW1?'"""
        user_input = "How much for a 1-bed flat in SW1?"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "SW1")
        self.assertEqual(result["property_type"], "1-bed flat")
        self.assertEqual(result["house_price"], 100000)
        self.assertEqual(result["deposit"], 10000)

    def test_user_wants_3bed_house_ec1(self):
        """Test: 'Show me a 3-bed house in EC1'"""
        user_input = "Show me a 3-bed house in EC1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "EC1")
        self.assertEqual(result["property_type"], "3-bed house")
        self.assertEqual(result["house_price"], 400000)
        self.assertEqual(result["deposit"], 40000)

    def test_user_wants_2bed_house_hp12(self):
        """Test: 'I need a 2-bed house in HP12'"""
        user_input = "I need a 2-bed house in HP12"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "HP12")
        self.assertEqual(result["property_type"], "2-bed house")
        self.assertEqual(result["house_price"], 300000)
        self.assertEqual(result["deposit"], 30000)

    def test_user_wants_1bed_flat_m1(self):
        """Test: 'What's the price for a 1-bed flat in M1?'"""
        user_input = "What's the price for a 1-bed flat in M1?"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "M1")
        self.assertEqual(result["property_type"], "1-bed flat")
        self.assertEqual(result["house_price"], 100000)
        self.assertEqual(result["deposit"], 10000)

    def test_user_wants_2bed_flat_w1(self):
        """Test: 'Looking at a 2-bed flat in W1'"""
        user_input = "Looking at a 2-bed flat in W1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "W1")
        self.assertEqual(result["property_type"], "2-bed flat")
        self.assertEqual(result["house_price"], 200000)
        self.assertEqual(result["deposit"], 20000)

    def test_user_wants_3bed_house_nw1(self):
        """Test: 'Tell me about a 3-bed house in NW1'"""
        user_input = "Tell me about a 3-bed house in NW1"
        result = self.run_agent_test(user_input)

        self.assertIsNotNone(result)
        self.assertEqual(result["postcode"], "NW1")
        self.assertEqual(result["property_type"], "3-bed house")
        self.assertEqual(result["house_price"], 400000)
        self.assertEqual(result["deposit"], 40000)


if __name__ == '__main__':
    unittest.main()
