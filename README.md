# Forensic Spatial Auditor (Blender Addon)

A professional metrology and forensic tool for Blender designed to quantify the **Uncertainty Budget** of spatial measurements derived from aerial satellite imagery.

## Overview

The Forensic Spatial Auditor uses the **Root Sum Square (RSS)** method to calculate a statistically rigorous measurement result. It combines user-induced measurement variance with sensor-specific uncertainty (Ground Sample Distance) to provide a final audited result with clear confidence intervals.

---

## Key Features

- **Quantified Uncertainty**: Move beyond simple measurements to scientific results (e.g., `10.04m ± 0.02m`).
- **Standardized Source Data Tiers**:
  - **Aerial Photography**: 15-30 cm GSD.
  - **Commercial Satellite**: 30-60 cm GSD.
  - **Older Satellite**: 1.0-2.5 m GSD.
  - **Landsat/Sentinel**: 15-30 m GSD (Wilderness/Oceans).
- **Harrington Empirical Rates**: Built-in uncertainty rates for on-road (1.45%) and off-road (1.61%) forensic analysis.
- **Coverage Factors (k / σ)**: Expand results to 68.2%, 95.4%, or 99.7% confidence levels (Sigma 1, 2, and 3).
- **Methodology Export**: One-click "Copy for Methodology" button to generate research-ready text for technical reports.

---

## Installation

1. Download `rss_measure.py`.
2. Open Blender and go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select `rss_measure.py`.
4. Enable the addon by checking the box next to **3D View: Forensic Spatial Auditor**.

---

## How to Use

### 1. Primary Observation Data
1. Open the **N-Panel** in the 3D Viewport (press `N`) and select the **View** tab.
2. Locate the **Spatial Uncertainty Auditor** panel.
3. Click **Add Trial** to create input fields.
4. Input multiple measurements of the same feature (e.g., the length of a skid mark). The tool will automatically calculate the **User Induced Uncertainty (uo)** based on your variance.

### 2. Sensor-Induced Uncertainty
1. Select your **Source Data** system (e.g., "Commercial Satellite").
2. Choose a **Conservatism Profile**:
   - **Optimistic**: Uses the best-case GSD from the tier.
   - **Balanced**: Uses the average GSD.
   - **Defensive**: Uses the worst-case GSD (recommended for forensic auditing).

### 3. Combined Uncertainty Budget
1. Set your **Coverage Factor (k / σ)**. In most forensic contexts, $k=2$ (95.4% confidence) is the standard.
2. Review the **Audit Result**. This shows your mean measurement plus/minus the expanded uncertainty.

### 4. Export for Documentation
1. Click **Copy for Methodology**.
2. Paste the result into your research paper, affidavit, or technical report.

---

## Technical Details

The final uncertainty ($U$) is calculated as:
$$U = k \cdot \sqrt{u_{user}^2 + u_{sensor}^2}$$

Where:
- $k$ is the coverage factor.
- $u_{user}$ is the standard deviation of your trials.
- $u_{sensor}$ is the error derived from the pixel pitch (GSD) or empirical Harrington rates.

---

## Credits
Developed by **Blendervisualinvestigation.com**
