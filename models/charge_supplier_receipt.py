# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models, _


class ChargeSupplierReceipt(models.Model):
    _name = 'charge.supplier.receipt'

    name = fields.Char('Name', required=True)
    amount = fields.Float('Amount')
    percentage = fields.Float('Percentage')
    amount_type = fields.Selection(
        [('amount', 'Amount'), ('percentage', 'Percentage')],
        'Amount Type'
        )
    applied_on = fields.Selection(
        [('by_order', _('By Order')),
         ('cost_per_box', _('Cost per box')),
         ('double_cost_box', _('Double cost of box')),
         (
             'order_template_total',
             _('For the total order of that product (template)')),
         ('label', _('Per label')),],
        'Applied on',
        required=True
        )
    template_total_type = fields.Selection(
        [('change_color', _('Change Color or Material')),
         ('monarch_unattached_neck', _('Monarch unattached to the neck')),
        ],
        'Type of application over total order of product template')


class StockPickingChargeProductBox(models.Model):
    _name = 'stock.picking.charge.product.box'

    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    qty = fields.Integer('Box Quantity', required=True)
    amount = fields.Float('Amount', compute='_compute_amount')

    @api.depends('product_id', 'qty')
    def _compute_amount(self):
        for record in self:
            if record.product_id and record.qty:
                record.amount = record.product_id.product_box_id.cost * \
                    record.qty
