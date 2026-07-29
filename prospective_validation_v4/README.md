# Prospective CRC patient-level validation v4

This directory locks a second prospective, outcome-sealed validation of
HistoWeave before any expression matrix, image, spot annotation, or derived
outcome from the Valdeolivas colorectal-cancer cohort is downloaded or opened.

The study contains 14 Visium sections from seven patients. The two serial
sections per patient are technical replicates; the patient is the independent
unit for scoring, uncertainty, and policy comparison.

The development meta-panel is restricted to studies whose outcomes were
already available before this lock: DLPFC, Wu 2021 breast cancer, and HER2ST.
All development studies must be rerun under the same nine-method, non-oracle-K
contract. The development score matrix, label-free meta-features, selected
policy, and every CRC action are frozen and hashed before CRC pathology labels
are opened.

The validation may support personalized selection only if the locked policy
has non-zero patient-level coverage and improves deployed regret relative to
the development-only always-global action. Otherwise the result remains a
negative external validation and HistoWeave retains its global fallback.

