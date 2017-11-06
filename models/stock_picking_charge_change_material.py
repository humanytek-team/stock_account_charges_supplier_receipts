# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class StockPickingChargeChangeMaterial(models.Model):
    _name = 'stock.picking.charge.change.material'
    _rec_name = 'product_tmpl_id'

    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product (template)', required=True)
    qty = fields.Integer('Quantity', required=True)
    total_order_template = fields.Float(
        'Total of product template in the purchase order',
        compute='_compute_total_order_template')
    amount = fields.Float('Amount', compute='_compute_amount')

    @api.depends('picking_id', 'product_tmpl_id')
    def _compute_total_order_template(self):
        """Computes value of field total_order_template"""

        for record in self:
            if record.picking_id and record.product_tmpl_id:
                if record.picking_id.purchase_id:
                    po_lines = record.picking_id.purchase_id.order_line.filtered(
                        lambda line: line.product_id.product_tmpl_id.id ==
                        record.product_tmpl_id.id
                    )
                    record.total_order_template = sum(
                        po_lines.mapped('price_total'))


    @api.depends('total_order_template', 'qty')
    def _compute_amount(self):
        """Computes value of field amount"""

        ChargeSupplierReceipt = self.env['charge.supplier.receipt']
        for record in self:
            if record.total_order_template and record.qty:
                charge_change_material = ChargeSupplierReceipt.search([
                    ('applied_on', '=', 'order_template_total'),
                    ('template_total_type', '=', 'change_material'),
                ])

                if charge_change_material:
                    record.amount = (
                        (record.total_order_template *
                         charge_change_material[0].percentage) / 100) \
                        * record.qty

    @api.model
    def create(self, vals):
        StockPicking = self.env['stock.picking']
        picking = StockPicking.browse(vals['picking_id'])

        if vals['product_tmpl_id'] not in picking.mapped(
                'move_lines_related.product_id.product_tmpl_id.id'):

            raise ValidationError(
                _("The product doesn't is part of this transfer."))

        return super(StockPickingChargeChangeMaterial, self).create(vals)
