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
    charge_change_material_ids = fields.One2many(
        'stock.picking.charge.change.material',
        'picking_id',
        'Charges by change of material')
    show_charge_change_material_ids = fields.Boolean(
        'Show field charge_change_material_ids',
        help='Technical field',
        default=False)
    total_charge_change_material_ids = fields.Float(
        'Total of charges by change in material',
        compute='_compute_total_charges'
    )
    show_charge_label = fields.Boolean(
        'Show fields of charge by missing tags ',
        help='Technical field',
        default=False)
    label_qty = fields.Integer('Quantity of missing tags')
    total_charge_label = fields.Float(
        'Total of charges by missing tags',
        compute='_compute_total_charges'
    )

    @api.onchange('charge_supplier_receipt_ids')
    def onchange_charges_supplier(self):
        """Process event onchange on field charge_supplier_receipt_ids"""

        show_charge_product_box_ids = False
        show_charge_other_supplier_box_ids = False
        show_charge_change_material_ids = False
        show_charge_label = False

        for charge in self.charge_supplier_receipt_ids:
            if charge.applied_on == 'cost_per_box':
                show_charge_product_box_ids = True
            if charge.applied_on == 'double_cost_box':
                show_charge_other_supplier_box_ids = True
            if charge.applied_on == 'order_template_total' and \
                    charge.template_total_type == 'change_material':
                show_charge_change_material_ids = True
            if charge.applied_on == 'label':
                show_charge_label = True

        self.show_charge_product_box_ids = show_charge_product_box_ids
        self.show_charge_other_supplier_box_ids = \
            show_charge_other_supplier_box_ids
        self.show_charge_change_material_ids = show_charge_change_material_ids
        self.show_charge_label = show_charge_label

    @api.depends(
        'charge_product_box_ids',
        'charge_other_supplier_box_ids',
        'charge_change_material_ids',
        'label_qty')
    def _compute_total_charges(self):
        """Computes value of fields total_charge_product_box_ids,
        total_charge_other_supplier_box_ids."""

        ChargeSupplierReceipt = self.env['charge.supplier.receipt']

        for record in self:

            if record.charge_product_box_ids:
                record.total_charge_product_box_ids = sum(
                    record.charge_product_box_ids.mapped('amount'))

            if record.charge_other_supplier_box_ids:
                record.total_charge_other_supplier_box_ids = sum(
                    record.charge_other_supplier_box_ids.mapped('amount'))

            if record.charge_change_material_ids:
                record.total_charge_change_material_ids = sum(
                    record.charge_change_material_ids.mapped('amount'))

            if record.label_qty > 0:
                charge_label = ChargeSupplierReceipt.search([
                    ('applied_on', '=', 'label')
                ])
                if charge_label:
                    record.total_charge_label = \
                        charge_label[0].amount * record.label_qty
