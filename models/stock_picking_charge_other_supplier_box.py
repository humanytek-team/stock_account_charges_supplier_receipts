# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class StockPickingChargeOtherSupplierBox(models.Model):
    _name = 'stock.picking.charge.other.supplier.box'
    _rec_name = 'product_id'

    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    qty = fields.Integer('Box Quantity', required=True)
    amount = fields.Float('Amount', compute='_compute_amount')

    @api.depends('product_id', 'qty')
    def _compute_amount(self):
        """Computes value of field amount"""

        for record in self:
            if record.product_id and record.qty:
                record.amount = (record.product_id.product_box_id.cost*2) * \
                    record.qty

    @api.model
    def create(self, vals):
        StockPicking = self.env['stock.picking']
        picking = StockPicking.browse(vals['picking_id'])

        if vals['product_id'] not in picking.mapped(
                'move_lines_related.product_id.id'):

            raise ValidationError(
                _("The product doesn't is part of this transfer."))

        return super(StockPickingChargeOtherSupplierBox, self).create(vals)
