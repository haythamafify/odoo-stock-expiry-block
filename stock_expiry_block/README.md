# Block Expired Lots on Receipt

## Overview

`stock_expiry_block` prevents validation of **vendor receipts** (`incoming` pickings) when any lot/serial number is expired.

The check covers all expiry-related dates:

- `expiration_date` (Expiration Date)
- `use_date` (Best Before Date)
- `removal_date` (Removal Date)

If any of these dates is in the past, validation is blocked with a clear error message listing the affected lot/serial and product.

## Compatibility

- Odoo 18.0

## Dependencies

- `stock`
- `product_expiry`

## How It Works

The module inherits `stock.picking` and overrides `button_validate`:

1. Applies only to incoming shipments (`picking_type_code == 'incoming'`).
2. Iterates through `move_line_ids`.
3. Checks expiry dates on `stock.move.line` first (values entered during receipt).
4. Falls back to `stock.production.lot` dates when needed.
5. Raises `UserError` if any lot/serial is expired.

## Installation

1. Place this module in your custom addons path.
2. Update the apps list in Odoo.
3. Install **Block Expired Lots on Receipt**.

## Notes

- This is a hard block: users cannot validate the receipt until expired items are resolved.
- Non-incoming operations are not affected.
