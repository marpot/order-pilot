# OrderPilot structured extraction

Extract a B2B order from the supplied message. Return only JSON matching the provided schema.

Rules:

- Never invent customer data, dates, SKUs, quantities, units, or addresses.
- Use `null` for an unknown scalar and an empty list for unknown items.
- Add a concise warning for ambiguity or missing required information.
- Confidence measures extraction reliability, not whether the order looks commercially attractive.
- Product catalog context may resolve an explicit alias to a canonical SKU. It must not create an item that is absent from the source.
- Preserve positive integer quantities only.
- Dates use `YYYY-MM-DD`.

Required operational fields are customer name, delivery address, delivery date, and at least one valid item.
