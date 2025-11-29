from src.Prompts.HousingGoalPrompt import housing_goal_output_format

output_format = f"""
------------------------------------------------------------
OUTPUT FORMATTING INSTRUCTIONS
------------------------------------------------------------

For the final step (5) or any time you need to present a complete result to the user, you MUST use the 
following Markdown templates to structure the information, replacing the bracketed placeholders with the 
actual data from the corresponding state/tool output.

### 1. Housing Goal Summary (After HousingGoalAgent is run and saved)
- Use this only when presenting alternatives or the final plan.
- Format Example:
    {housing_goal_output_format}

### 2. Saving Capacity Summary (After BankDataAgent is run and validated)
- Use this when asking for the CRITICAL CONVERSATIONAL STEP confirmation.
- Format:
    ```markdown
    #### 💰 Savings Analysis Results
    Based on your uploaded bank statements:
    * **Calculated Monthly Surplus:** £[net_surplus]
    * **Suggested Monthly Saving/Investment:** **£[suggested_investment]**
    * **Conclusion:** This shows you have a calculated capacity to save/invest this amount each month.
    ```

### 3. Risk Profile Summary (For internal state tracking, rarely presented directly)
- If you need to summarize the user's risk answers, use:
    ```markdown
    #### 📊 Your Risk Profile
    * **Income Stability (1-5):** [income_stability]
    * **Investment Horizon (Years):** [time_horizon_years]
    * **Loss Reaction (1-5):** [loss_reaction]
    ```

### 4. Final Plan Presentation (After PlanGeneratorAgent)
- Use this exclusively for Step 5: PRESENT RESULTS.
- Format:
    ```markdown
    # ✅ Your Personalized Financial Plan
    
    | Detail | Figure |
    | :--- | :--- |
    | **Feasibility** | [Feasible/Tight/Infeasible] |
    | **Target Deposit** | £[deposit_target] |
    | **Target Time Horizon** | [time_horizon_years] Years |
    | **Recommended Monthly Saving** | **£[suggested_investment]** |
    | **Investment Split** | [investment_percentage]% Investment / [cash_percentage]% Cash |

    **Next Steps & Recommendation:**
    [user-facing explanation from plan_generator_agent]
    ```

"""