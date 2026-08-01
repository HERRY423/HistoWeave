# Failed synthetic v2.1 execution retained

The corrected v2.1 null generator showed that the original three-nearest-
neighbour selector was unsafe under a no-signal condition.  The run remains a
negative result rather than being reclassified.

- selected threshold: 0.50;
- signal coverage: 0.5750;
- covered-action accuracy: 0.8406;
- non-global opportunity recall: 0.9063;
- signal regret difference: -0.1200 (95% bootstrap CI -0.1544 to -0.0839);
- null coverage: 0.4667;
- null regret difference: +0.1984 (95% bootstrap CI +0.1606 to +0.2370).

Thus v2.1 improved selection when the switch was present but failed the locked
null non-inferiority condition.  v2.2 replaces noisy-neighbour lookup with a
fixed-alpha ridge method-score model and requires independent signal and null
calibration panels before the threshold is frozen.  New generator and
bootstrap seeds are used for v2.2.
