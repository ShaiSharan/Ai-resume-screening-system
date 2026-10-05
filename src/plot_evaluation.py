import matplotlib.pyplot as plt

# Results from evaluate.py
labels = ["TF-IDF Baseline\n(basic approach)", "Hybrid Model\n(this project)"]
scores = [0.812, 0.926]
colors = ["#E74C3C", "#2ECC71"]

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(labels, scores, color=colors, width=0.5)

# Add the value on top of each bar
for bar, score in zip(bars, scores):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + 0.02,
             f"{score:.3f}", ha="center", fontsize=13, fontweight="bold")

ax.set_ylim(0, 1.05)
ax.set_ylabel("Spearman Correlation with Human Judgment", fontsize=11)
ax.set_title("Model Ranking Quality vs. Human Evaluation\n(higher = ranks candidates more like a human would)",
              fontsize=12, fontweight="bold")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.3)

plt.tight_layout()
plt.savefig("../data/evaluation_comparison.png", dpi=200)
print("Chart saved to data/evaluation_comparison.png")
plt.show()