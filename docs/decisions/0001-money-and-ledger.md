# ADR 0001: Integer money and append-only ledger

Money is stored as integer kopecks and litres as fixed precision decimal.
Financial facts are immutable and corrections use reversal entries. This avoids
binary floating-point drift and preserves an auditable history.

