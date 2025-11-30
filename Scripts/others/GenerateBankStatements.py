import pandas as pd
import numpy as np
import os # Import os for checking file existence and better file handling

BANK_STATEMENT_DIR = "./data"

import pandas as pd
import numpy as np
import os

def createBankStatment(input_filename, annual_income, monthlyTakeHome, savingsMin, savingsMax):
    """
    Generates a new bank statement CSV file based on an input file, simulating a 
    new monthly take-home income and a variable monthly savings amount.
    
    The 'SAVINGS TRANSFER' transaction is OMITTED from the final output, allowing 
    the monthly savings to accumulate in the account balance.

    Args:
        input_filename (str): The name of the existing bank statement CSV file.
        monthlyTakeHome (float): The new target monthly take-home income (net pay).
        savingsMin (float): The minimum monthly savings to be generated.
        savingsMax (float): The maximum monthly savings to be generated.

    Returns:
        str: The filename of the newly created CSV file.
    """
    
    # --- 1. Load, Clean, and Prepare Data ---
    
    if not os.path.exists(input_filename):
        raise FileNotFoundError(f"The input file '{input_filename}' was not found.")
        
    df = pd.read_csv(input_filename)
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
    df['Credit amount'] = df['Credit amount'].fillna(0)
    df['Debit amount'] = df['Debit amount'].fillna(0)
    df['Month'] = df['Transaction Date'].dt.to_period('M')

    # Calculate the total original debit for each month (used for scaling)
    monthly_debits_original = df.groupby('Month')['Debit amount'].sum().round(2)
    month_periods = monthly_debits_original.index.tolist()
    
    if not month_periods:
        raise ValueError("The input file contains no monthly data to process.")

    # --- 2. Generate Savings via Distribution and Calculate Scaling Factors ---

    np.random.seed(42) 
    random_savings = np.round(
        np.random.uniform(savingsMin, savingsMax, size=len(month_periods)), 2
    )

    # Create the target dictionary with calculated factors
    monthly_targets_period = {}
    for i, month_period in enumerate(month_periods):
        savings = random_savings[i]
        original_debit = monthly_debits_original.get(month_period, 0)
        
        # Target Spending = Income - Savings
        target_spending = monthlyTakeHome - savings
        
        # Scaling Factor = Target Spending / Original Total Debit
        scaling_factor = target_spending / original_debit if original_debit > 0 else 0
        
        monthly_targets_period[month_period] = {
            'Savings': savings,
            'Scaling_Factor': scaling_factor,
            'Target_Spending': target_spending
        }

    df_final = df.copy() # Start with the base dataframe for modification

    # --- 3. Apply Scaling and Income Update ---

    # a) Update Credit/Income transactions
    credit_mask = (df_final['Credit amount'] > 0) & (df_final['Description'].str.contains('PAYROLL'))
    df_final.loc[credit_mask, 'Credit amount'] = monthlyTakeHome
    df_final.loc[credit_mask, 'Debit amount'] = 0.0

    # b) Scale Debit transactions
    def scale_debit(row):
        if row['Debit amount'] > 0 and 'PAYROLL' not in row['Description']:
            month_target = monthly_targets_period.get(row['Month'])
            if month_target:
                return (row['Debit amount'] * month_target['Scaling_Factor']).round(2)
        return row['Debit amount']

    df_final['Debit amount'] = df_final.apply(scale_debit, axis=1)
    df_final.loc[~credit_mask, 'Credit amount'] = 0.0

    # --- 4. Skip SAVINGS TRANSFER transactions (as requested) ---
    # The monthly savings is now the net cash flow difference.

    # --- 5. Final Cleanup and Save ---

    # Sort and clean up final dataframe for saving
    df_final = df_final.sort_values(by=['Transaction Date', 'Description']).reset_index(drop=True)
    df_final = df_final[['Transaction Date', 'Description', 'Credit amount', 'Debit amount']]
    df_final['Credit amount'] = df_final['Credit amount'].replace(0.0, np.nan)
    df_final['Debit amount'] = df_final['Debit amount'].replace(0.0, np.nan)
    
    # Final Output Filename
    output_filename = f'{BANK_STATEMENT_DIR}/bankstatement_{annual_income}.csv'

    # Save the new file
    df_final.to_csv(output_filename, index=False)
    
    return output_filename

# -----------------------------------------------------------------------------
# Example Usage (calling the function with the parameters from the previous steps):
# The previous gross salary was £50,000, which resulted in a £3,293 monthly take-home.

# new_file = createBankStatment(
#     input_filename='bankstatement.csv', 
#     monthlyTakeHome=3293.00, 
#     savingsMin=500.00, 
#     savingsMax=600.00
# )
# print(f"\nGenerated file name: {new_file}")

def main():
    input_file = f"{BANK_STATEMENT_DIR}/bankstatement.csv"
    ################  50 K Income ###################
    annualIncome="50k" 
    monthlyTakeHome = 3293
    minSavings = 500
    maxSavings = 625
    new_file = createBankStatment(input_file, 
                       annual_income=annualIncome,
                       monthlyTakeHome=monthlyTakeHome,
                       savingsMin=minSavings,
                       savingsMax=maxSavings
                       )
    print(f"Created new bankfile: {new_file}")

    ################  60 K Income ###################
    annualIncome="60k" 
    monthlyTakeHome = 3780
    minSavings = 800
    maxSavings = 1000
    new_file = createBankStatment(input_file, 
                       annual_income=annualIncome,
                       monthlyTakeHome=monthlyTakeHome,
                       savingsMin=minSavings,
                       savingsMax=maxSavings
                       )
    print(f"Created new bankfile: {new_file}")

    ################  75 K Income ###################
    annualIncome="75k" 
    monthlyTakeHome = 4505
    minSavings = 1300
    maxSavings = 1600
    new_file = createBankStatment(input_file, 
                       annual_income=annualIncome,
                       monthlyTakeHome=monthlyTakeHome,
                       savingsMin=minSavings,
                       savingsMax=maxSavings
                       )
    print(f"Created new bankfile: {new_file}")

    ################  100 K Income ###################
    annualIncome="100k" 
    monthlyTakeHome = 5200
    minSavings = 2100
    maxSavings = 3000
    new_file = createBankStatment(input_file, 
                       annual_income=annualIncome,
                       monthlyTakeHome=monthlyTakeHome,
                       savingsMin=minSavings,
                       savingsMax=maxSavings
                       )
    print(f"Created new bankfile: {new_file}")

if __name__ == "__main__":
    main()