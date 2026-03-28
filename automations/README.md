# AC Automations

Backup of Home Assistant automations for AC_02 (Bungalow 02) and AC_04 (Bungalow 04).

## 24h AC Automation Timeline

```
───────────────────────── 24h AC Automation Timeline ─────────────────────────

 00:00    03:00    06:00    09:00    12:00    15:00    18:00    21:00    00:00
   |        |        |        |        |        |        |        |        |

   ◄──────────── NIGHT (21:00 → 09:00) ────────────►◄──── DAY (09:00 → 21:00) ──►

   ┌─────────────────────────────────────────────────────────────────────────┐
   │ 💤 NIGHT MODE (21:00 → 09:00)                                           │
   │    Trigger: AC turns on, or fan changes                                 │
   │    Skip if: fan is already Low or Quiet                                 │
   │    Action:  Wait 5 min → set Fan=Auto, Temp=26°C                        │
   └────────────────────────────────┬────────────────────────────────────────┘
                                    │
   ┌────────────────────────────────┘────────────────────────────────────────┐
   │ ☀️  DAY MODE - Fan Medium Low (09:00 → 21:00)                            │
   │    Trigger: AC turns on, or fan changes                                 │
   │    Action:  Wait 5 min → set Fan=Medium Low                             │
   └─────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────────┐
   │ ⏱️  DAY MODE - Auto-off (09:00 → 21:00)                                  │
   │    Trigger: AC turns on                                                 │
   │    Action:  Wait 2h → turn off                                          │
   └─────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────────┐
   │ ⚡ ALWAYS - 50% Power (no time restriction)                              │
   │    Trigger: AC turns on, or preset changes away from Power 50           │
   │    Action:  Immediately set Preset=Power 50                             │
   └─────────────────────────────────────────────────────────────────────────┘


── What happens when AC turns on ─────────────────────────────────────────────

  00:00 ──────────────────── 09:00 ──────────────────────── 21:00 ─── 00:00
                               │                              │
  [AC turned on]               │        [AC turned on]        │   [AC turned on]
       │                       │              │               │         │
       ▼                       │              ▼               │         ▼
  ⚡ Power 50% immediately     │   ⚡ Power 50% immediately   │  ⚡ Power 50% immed.
  💤 Fan→Auto 26°C (5 min)    │   ☀️  Fan→Med.Low (5 min)   │  💤 Fan→Auto 26°C
  (no auto-off)                │   ⏱️  Auto-off after 2h     │  (no auto-off)
```

## Automation Files

| File | Alias | Active |
|------|-------|--------|
| `ac02_auto_off_2h.json` | AC_02 Auto-off after 2h | 09:00–21:00 |
| `ac04_auto_off_2h.json` | AC_04 Auto-off after 2h | 09:00–21:00 |
| `ac02_set_to_50_power.json` | AC_02 Set to 50% Power | Always |
| `ac04_set_to_50_power.json` | AC_04 Set to 50% Power | Always |
| `ac02_set_fan_medium_low.json` | AC_02 Set Fan to Medium Low | 09:00–21:00 |
| `ac04_set_fan_medium_low.json` | AC_04 Set Fan to Medium Low | 09:00–21:00 |
| `ac02_night_auto_26.json` | AC_02 Night Mode - Auto 26°C | 21:00–09:00 |
| `ac04_night_auto_26.json` | AC_04 Night Mode - Auto 26°C | 21:00–09:00 |
