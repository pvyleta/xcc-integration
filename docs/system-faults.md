# Controller system faults

`binary_sensor.xcc_system_fault` reports the controller's **Current errors**
diagnostics, separately from HA communication/command failures. Its
`active_faults` attribute maps controller fault codes to the labels supplied by
the controller, respecting the integration's English/Czech language preference.
`fault_count` is the number of currently active entries.

The integration reads `diag.xml?tab=1` for labels and polls `DIAG1.XML` using the
existing authenticated session. It decodes both individual `P` fields and packed
`PS` fields (least-significant bit first, preserving empty bit positions).
Only the current-error rows are considered: history navigation, configuration
flags and acknowledgement/reset controls are not exposed or executed.

Each newly observed fault and each observed clearance is logged once at WARNING
level, including its label and code. Already-active faults are logged at startup;
unchanged polls do not repeat the message. HA records the sensor and attribute
changes according to the user's Recorder configuration and retention policy.

A missing, invalid or incomplete diagnostic snapshot makes the sensor
unavailable, **not clear**. The last good fault list is retained for context and
transition comparison. Controllers without a supported diagnostics descriptor
keep this sensor unavailable; the optional diagnostics page is not added to the
required polling set until its descriptor is understood.

## Alerts

Notifications are user-configured automations, not hardcoded integration actions.
Watch both state and `active_faults` changes: a second fault can appear while the
aggregate sensor is already on. Compare fault codes to avoid notifying repeatedly
for an unchanged fault, and ignore unavailable/unknown snapshots. Check active
faults at HA startup too if an alert after a restart is desired.

## Limits

This monitors current diagnostics at the configured polling interval. A fault
that appears and clears entirely between polls can be missed. It does not import
the controller's historical fault log, acknowledge faults, or replace the
controller's own protections. The Current errors list can include maintenance
reminders and warnings as well as faults; labels follow the controller's UI.
