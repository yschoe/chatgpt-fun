import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import halfnorm

# Set parameters
num_samples = 10000
alpha = 10.0  # Power-law exponent (typically > 1)
min_value = 0.001  # Lower bound for the power-law distribution

# Generate samples from the half-normal distribution
half_normal_samples = halfnorm.rvs(size=num_samples)

# Generate samples from the decreasing power-law distribution using the inverse transform
u = np.random.uniform(size=num_samples)
power_law_samples = min_value * (u ** (-1 / (alpha - 1)))

# Calculate mean and variance for both distributions
half_normal_mean = np.mean(half_normal_samples)
half_normal_variance = np.var(half_normal_samples)
half_normal_std = np.std(half_normal_samples)

power_law_mean = np.mean(power_law_samples)
power_law_variance = np.var(power_law_samples)
power_law_std = np.std(power_law_samples)

# Scale and shift the half-normal samples to match the power-law distribution
scaling_factor = np.sqrt(power_law_variance / half_normal_variance)
half_normal_samples_scaled = half_normal_samples * scaling_factor

# Shift half-normal samples to match the mean of the power-law distribution
mean_shift = power_law_mean - np.mean(half_normal_samples_scaled)
half_normal_samples_scaled_shifted = half_normal_samples_scaled + mean_shift

# Define linear bins based on the combined range of both distributions
all_samples = np.concatenate((power_law_samples, half_normal_samples_scaled_shifted))
num_bins = 300
bins = np.linspace(np.min(all_samples), np.max(all_samples), num_bins)

# Compute histogram densities (in linear scale) for both distributions
power_law_hist, bin_edges = np.histogram(power_law_samples, bins=bins, density=True)
half_normal_hist, _ = np.histogram(half_normal_samples_scaled_shifted, bins=bins, density=True)

# Define bin centers for plotting
bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

# Plot the histograms in log-log scale
plt.figure(figsize=(12, 6))
plt.plot(bin_centers, power_law_hist, color='red', label='Power-Law Distribution', alpha=0.7)
plt.plot(bin_centers, half_normal_hist, color='blue', label='Scaled & Shifted Half-Normal Distribution', alpha=0.7)

# Set both axes to log scale
plt.xscale('log')
plt.yscale('log')

# Limit x-axis to relevant range where density is above 0.1
mask = (power_law_hist > 0.1) | (half_normal_hist > 0.1)
plot_min, plot_max = bin_centers[mask][0], bin_centers[mask][-1]
plt.xlim(plot_min, plot_max)

# Add title with empirical standard deviations
plt.xlabel('Value')
plt.ylabel('Density')
plt.legend()
plt.title(f'Empirical Distributions: Power-Law vs. Scaled & Shifted Half-Normal (Log-Log Plot)\n'
          f'Std Dev (Power-Law): {power_law_std:.3f} | Std Dev (Scaled Half-Normal): {half_normal_std:.3f}')
plt.show()

