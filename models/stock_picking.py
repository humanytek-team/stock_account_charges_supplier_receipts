# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    charge_supplier_receipt_ids = fields.Many2many(
        'charge.supplier.receipt',
        column1='picking_id',
        column2='charge_supplier_receipt_id',
        string='Charges to supplier'
    )
    charge_product_box_ids = fields.One2many(
        'stock.picking.charge.product.box',
        'picking_id',
        'Charges by incorrect box')
