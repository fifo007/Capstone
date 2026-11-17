# Future event-driven model

This directory reserves an isolated home for a future model that consumes pulse events or pulse counts from the hardware path. It currently contains no implementation, training data, decoder, or inference code.

The existing BioWire notebook and saved EXP-56B decoder are voltage-derived historical software work. They do not establish that the model processes timestamped pulses from hardware. Keep future event-model code and results here (or in explicitly documented subdirectories) so the existing model and historical artifacts remain unchanged.

Before implementing a decoder, document the event representation, measurement window, target quantity (for example, average or endpoint voltage), and source of V-to-frequency calibration data. Use synthetic encoder parameters only when clearly labeled synthetic; replace them with measured calibration after the physical converter is characterized.

No additional dependency is required for this documentation-only placeholder. Dependencies should be specified alongside the future implementation when its runtime and board target are selected.
