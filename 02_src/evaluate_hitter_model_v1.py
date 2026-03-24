import os
import pandas as pd

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Paths ---
    input_path = os.path.join(base_dir, "../03_output/hitter_backtest_results_v1.csv")
    output_path = os.path.join(base_dir, "../03_output/hitter_model_scorecard_v1.csv")

    df = pd.read_csv(input_path)

    # --- Function to calculate metrics ---
    def calc_metrics(actual, predicted):
        error = predicted - actual
        mae = error.abs().mean()
        bias = error.mean()
        return mae, bias

    # --- Calculate metrics for each stat ---
    metrics = []

    stats = [
        ("home_run", "proj_home_run", "actual_home_run"),
        ("rbi", "proj_b_rbi", "actual_b_rbi"),
        ("runs", "proj_r_run", "actual_r_run"),
        ("sb", "proj_r_total_stolen_base", "actual_sb")
    ]

    for stat_name, proj_col, actual_col in stats:
        mae, bias = calc_metrics(df[actual_col], df[proj_col])

        metrics.append({
            "stat": stat_name,
            "mae": mae,
            "bias": bias
        })

    # --- Convert to DataFrame ---
    results_df = pd.DataFrame(metrics)

    # --- Save output ---
    results_df.to_csv(output_path, index=False)

    print(f"Model scorecard saved to: {output_path}")


if __name__ == "__main__":
    main()