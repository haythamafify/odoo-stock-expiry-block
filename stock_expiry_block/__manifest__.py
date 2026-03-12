# -*- coding: utf-8 -*-
{
    'name': 'Block Expired Lots on Receipt',
    'version': '18.0.1.0.0',
    'summary': 'Prevents validating receipts that contain expired lots/serial numbers',
    'description': """
        This module blocks the validation of vendor receipts (incoming shipments)
        if any lot/serial number has an expired date.

        Checks ALL expiry-related dates:
        - Expiration Date
        - Best Before Date
        - Removal Date

        If ANY of these dates is in the past, validation is fully blocked with a clear error message.
    """,
    'category': 'Inventory',
    'author': 'Haytham Afify',
    'website': 'https://github.com/haythamafify/custom_addons',
    'linkedin': 'https://www.linkedin.com/in/haytham-gamal-4165797a/',
    'depends': ['stock', 'product_expiry'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
