# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models
import logging
_logger = logging.getLogger(__name__)

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
    show_charge_product_box_ids = fields.Boolean(
        'Show field charge_product_box_ids',
        help='Technical field',
        default=False)
    total_charge_product_box_ids = fields.Float(
        'Total of charges by incorrect box',
        compute='_compute_total_charges'
    )
    charge_other_supplier_box_ids = fields.One2many(
        'stock.picking.charge.other.supplier.box',
        'picking_id',
        'Charges by box of other vendor')
    show_charge_other_supplier_box_ids = fields.Boolean(
        'Show field charge_other_supplier_box_ids',
        help='Technical field',
        default=False)
    total_charge_other_supplier_box_ids = fields.Float(
        'Total of charges by box of other vendor',
        compute='_compute_total_charges'
    )

    @api.onchange('charge_supplier_receipt_ids')
    def onchange_charges_supplier(self):
        """Process event onchange on field charge_supplier_receipt_ids"""

        show_charge_product_box_ids = False
        show_charge_other_supplier_box_ids = False
        for charge in self.charge_supplier_receipt_ids:
            if charge.applied_on == 'cost_per_box':
                show_charge_product_box_ids = True
            if charge.applied_on == 'double_cost_box':
                show_charge_other_supplier_box_ids = True

        self.show_charge_product_box_ids = show_charge_product_box_ids
        self.show_charge_other_supplier_box_ids = \
            show_charge_other_supplier_box_ids

    @api.depends('charge_product_box_ids', 'charge_other_supplier_box_ids')
    def _compute_total_charges(self):
        """Computes value of fields total_charge_product_box_ids,
        total_charge_other_supplier_box_ids."""

        for record in self:
            if record.charge_product_box_ids:
                record.total_charge_product_box_ids = sum(
                    record.charge_product_box_ids.mapped('amount'))
            if record.charge_other_supplier_box_ids:
                record.total_charge_other_supplier_box_ids = sum(
                    record.charge_other_supplier_box_ids.mapped('amount'))
