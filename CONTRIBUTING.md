# Contributing to ND-2

Thanks for helping. This is a hobby-scale open hardware project, so keep it friendly and practical.

## Ways to help

- **Hardware review:** open the KiCad project and point out problems (issue template: *Hardware issue*).
- **Bring-up reports:** built a dongle? Post your rail voltages, `dmesg`, link and cable-test results (issue template: *Bring-up report*).
- **Software:** cable-test tooling, LAN7801 EEPROM scripts, and eventually the handheld GUI.
- **Docs:** anything that confused you is worth fixing.

## Hardware changes

- Use **KiCad 10** or newer. Project libraries (`ND2.kicad_sym`, `ND2.pretty`) live next to each board.
- Run ERC and DRC before opening a PR, and say in the PR what changed and why.
- Pick parts that are **in stock at LCSC/JLCPCB** where possible, and put the LCSC number in the symbol's `LCSC` field.
- Don't commit regenerated Gerbers for work-in-progress changes. Fab files get regenerated when a revision is released.
- Bump the board revision in the silkscreen and README when a change affects a fabricated board.

## Software changes

- Python 3.9+, standard library where possible.
- Say in the PR what hardware (or none) you tested on.

## License

By contributing you agree that your contributions are licensed under the [MIT license](LICENSE).
