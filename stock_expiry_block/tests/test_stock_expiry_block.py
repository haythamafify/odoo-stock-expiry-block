# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockExpiryBlock(TransactionCase):
    """
    Tests for stock_expiry_block module.
    Verifies that incoming receipts are blocked when lots are expired.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Company & warehouse
        cls.company = cls.env.ref('base.main_company')
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )

        # Picking type: incoming (receipt)
        cls.picking_type_in = cls.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', cls.warehouse.id),
        ], limit=1)

        # Locations
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')

        # Product with tracking by lot
        cls.product = cls.env['product.product'].create({
            'name': 'Test Perishable Product',
            'type': 'consu',
            'tracking': 'lot',
            'use_expiration_date': True,
        })

        cls.now = fields.Datetime.now()

    def _create_receipt(self, lot_expiration_date):
        """Helper: create a receipt with one move line and a lot."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })

        lot = self.env['stock.lot'].create({
            'name': 'LOT-TEST-001',
            'product_id': self.product.id,
            'company_id': self.company.id,
            'expiration_date': lot_expiration_date,
        })

        self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })

        picking.action_confirm()
        picking.action_assign()

        for ml in picking.move_line_ids:
            ml.lot_id = lot
            ml.qty_done = 10

        return picking

    # ------------------------------------------------------------------
    # Test 1: Expired lot → should be BLOCKED
    # ------------------------------------------------------------------
    def test_expired_lot_blocks_validation(self):
        """Receipt with an expired lot must raise UserError."""
        expired_date = self.now - timedelta(days=5)
        picking = self._create_receipt(expired_date)

        with self.assertRaises(UserError) as ctx:
            picking.button_validate()

        self.assertIn('EXPIRED', str(ctx.exception))

    # ------------------------------------------------------------------
    # Test 2: Valid (future) lot → should PASS
    # ------------------------------------------------------------------
    def test_valid_lot_allows_validation(self):
        """Receipt with a future expiry date must validate successfully."""
        future_date = self.now + timedelta(days=30)
        picking = self._create_receipt(future_date)

        # Should NOT raise — validation proceeds normally
        try:
            picking.button_validate()
        except UserError as e:
            if 'EXPIRED' in str(e):
                self.fail(f"Validation was blocked unexpectedly: {e}")

    # ------------------------------------------------------------------
    # Test 3: No expiry date set → should PASS (no block)
    # ------------------------------------------------------------------
    def test_no_expiry_date_allows_validation(self):
        """Receipt with no expiry date set must not be blocked."""
        picking = self._create_receipt(lot_expiration_date=False)

        try:
            picking.button_validate()
        except UserError as e:
            if 'EXPIRED' in str(e):
                self.fail(f"Validation was blocked unexpectedly for lot with no date: {e}")

    # ------------------------------------------------------------------
    # Test 4: Outgoing transfer with expired lot → should NOT block
    # ------------------------------------------------------------------
    def test_outgoing_not_blocked(self):
        """Outgoing transfers must never be blocked by this module."""
        picking_type_out = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', self.warehouse.id),
        ], limit=1)

        expired_date = self.now - timedelta(days=10)
        lot = self.env['stock.lot'].create({
            'name': 'LOT-OUT-001',
            'product_id': self.product.id,
            'company_id': self.company.id,
            'expiration_date': expired_date,
        })

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

        self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

        picking.action_confirm()
        picking.action_assign()

        for ml in picking.move_line_ids:
            ml.lot_id = lot
            ml.qty_done = 5

        # Outgoing → should not raise EXPIRED error from our module
        try:
            picking.button_validate()
        except UserError as e:
            if 'EXPIRED' in str(e):
                self.fail(f"Outgoing transfer was wrongly blocked: {e}")
