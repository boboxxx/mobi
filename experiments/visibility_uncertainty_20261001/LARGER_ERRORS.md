# Finite sensitivity to larger supplied coordinate boxes

The main heterogeneous comparison uses 0.002 m componentwise input bounds, which are stringent and are not calibrated physical-sensor specifications. Before viewing that comparison's completed results, add two fixed larger bounds, 0.01 m and 0.02 m. Use exactly the same twelve input clouds, 20/50 ms hypothetical scan periods, four phases, two classes and grid resolutions. No new favorable scan phase or obstacle shape is selected.

Run the exact local-search implementation only after its output has been compared against the completed exhaustive 0.002 m reference. Compare heterogeneous errors to the best common error threshold using the same bins. Check that a larger input box never improves either expiry under the unchanged geometry. Near-obstacle cases must remain rejected. This is a sensitivity study, not a sensor calibration or a new CARLA acquisition, and it includes no end-to-end packet timing claim.
