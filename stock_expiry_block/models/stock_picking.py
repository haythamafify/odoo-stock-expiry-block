# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Override button_validate to block receipt validation
        if any lot/serial number has an expired date.

        Compatible with Odoo 18.

        In Odoo 18, expiry dates are stored on BOTH the move.line and the lot.
        We check move_line first (what the user entered in the dialog),
        then fall back to lot record fields.

        Checks:
          - expiration_date  (Expiration Date)
          - use_date         (Best Before Date)
          - removal_date     (Removal Date)

        If ANY of these dates is past today → raise UserError (hard block).
        Only applies to incoming shipments (receipts from vendors).
        """
        self.ensure_one()

        # Only block incoming shipments (receipts)
        if self.picking_type_code == 'incoming':
            now = fields.Datetime.now()
            expired_lots = []

            for move_line in self.move_line_ids:
                lot = move_line.lot_id
                lot_name = lot.name if lot else move_line.lot_name or '—'
                product_name = move_line.product_id.display_name

                expired_field = None

                # --- Check move_line fields first (entered in the Lots dialog) ---
                # expiration_date on move_line (Odoo 18: stock.move.line has this field)
                ml_exp = getattr(move_line, 'expiration_date', None)
                ml_use = getattr(move_line, 'use_date', None)
                ml_rem = getattr(move_line, 'removal_date', None)

                if ml_exp and ml_exp < now:
                    expired_field = _('Expiration Date (%s)') % fields.Datetime.to_string(ml_exp)

                elif ml_use and ml_use < now:
                    expired_field = _('Best Before Date (%s)') % fields.Datetime.to_string(ml_use)

                elif ml_rem and ml_rem < now:
                    expired_field = _('Removal Date (%s)') % fields.Datetime.to_string(ml_rem)

                # --- Fallback: check lot record if move_line had no dates ---
                if not expired_field and lot:
                    if lot.expiration_date and lot.expiration_date < now:
                        expired_field = _('Expiration Date (%s)') % fields.Datetime.to_string(lot.expiration_date)

                    elif lot.use_date and lot.use_date < now:
                        expired_field = _('Best Before Date (%s)') % fields.Datetime.to_string(lot.use_date)

                    elif lot.removal_date and lot.removal_date < now:
                        expired_field = _('Removal Date (%s)') % fields.Datetime.to_string(lot.removal_date)

                if expired_field:
                    expired_lots.append(
                        '• %s  |  %s  |  %s' % (
                            lot_name,
                            product_name,
                            expired_field,
                        )
                    )

            if expired_lots:
                detail_lines = '\n'.join(expired_lots)
                raise UserError(
                    _('❌ Cannot validate receipt — the following lots/serial numbers are EXPIRED:\n\n'
                      '%s\n\n'
                      'Please contact the vendor to replace the expired goods '
                      'before proceeding.')
                    % detail_lines
                )

        return super().button_validate()