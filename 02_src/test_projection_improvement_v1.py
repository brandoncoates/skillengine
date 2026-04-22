import pandas as pd
import os

# =========================
# PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_PATH = os.path.join(BASE_DIR, "../03_output/dfs_recap_master.csv")

# =========================
# LOAD
# =========================
df = pd.read_csv(TRACKER_PATH)

# =========================
# CLEAN
# =========================
df = df.dropna(subset=["actual_fd_points", "projected_fd_points", "adjusted_fd_points"])

# =========================
# CALCULATE ERRORS
# =========================
df["original_error"] = abs(df["actual_fd_points"] - df["projected_fd_points"])
df["adjusted_error"] = abs(df["actual_fd_points"] - df["adjusted_fd_points"])

# =========================
# OVERALL METRICS
# =========================
original_mae = df["original_error"].mean()
adjusted_mae = df["adjusted_error"].mean()

improvement = original_mae - adjusted_mae
improvement_pct = (improvement / original_mae) * 100 if original_mae != 0 else 0

# =========================
# TREND BREAKDOWN
# =========================
trend_summary = df.groupby("trend_tag")[["original_error", "adjusted_error"]].mean()

# =========================
# PRINT RESULTS
# =========================
print("\n=== OVERALL PERFORMANCE ===")
print(f"Original MAE:  {original_mae:.4f}")
print(f"Adjusted MAE:  {adjusted_mae:.4f}")
print(f"Improvement:   {improvement:.4f}")
print(f"Improvement %: {improvement_pct:.2f}%")

print("\n=== BY TREND TAG ===")
print(trend_summary)

print("\n=== SAMPLE SIZE ===")
print(f"Total Rows Used: {len(df)}")