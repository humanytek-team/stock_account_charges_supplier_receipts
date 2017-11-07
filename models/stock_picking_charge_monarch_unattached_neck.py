# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class StockPickingChargeMonarchUnattachedNeck(models.Model):
    _name = 'stock.picking.charge.monarch.unattached.neck'
    _rec_name = 'product_tmpl_id'

    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product (template)', required=True)
    qty = fields.Integer('Quantity', required=True)
    amount = fields.Float('Amount', compute='_compute_amount')

    @api.depends('qty')
    def _compute_amount(self):
        """Computes value of field amount"""

        ChargeSupplierReceipt = self.env['charge.supplier.receipt']
        for record in self:
            if record.qty:
                charge_monarch = ChargeSupplierReceipt.search([
                    ('applied_on', '=', 'order_template_total'),
                    ('template_total_type', '=', 'monarch_unattached_neck'),
                ])

                if charge_monarch:
                    record.amount = charge_monarch[0].amount * record.qty

    @api.model
    def create(self, vals):
        StockPicking = self.env['stock.picking']
        picking = StockPicking.browse(vals['picking_id'])

        if vals['product_tmpl_id'] not in picking.mapped(
                'move_lines_related.product_id.product_tmpl_id.id'):

            raise ValidationError(
                _("The product doesn't is part of this transfer."))

        return super(StockPickingChargeMonarchUnattachedNeck, self).create(vals)
