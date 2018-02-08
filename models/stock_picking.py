# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError

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
    charge_monarch_ids = fields.One2many(
        'stock.picking.charge.monarch.unattached.neck',
        'picking_id',
        'Charges by monarch unattached to neck')
    show_charge_monarch_ids = fields.Boolean(
        'Show field charge_monarch_ids',
        help='Technical field',
        default=False)
    total_monarch_ids = fields.Float(
        'Total of charges by monarch unattached to neck',
        compute='_compute_total_charges'
    )
    total_charges_by_order = fields.Float(
        'Total of charges by order',
        compute='_compute_total_charges'
    )

    @api.onchange('charge_supplier_receipt_ids')
    def onchange_charges_supplier(self):
        """Process event onchange on field charge_supplier_receipt_ids"""

        show_charge_product_box_ids = False
        show_charge_other_supplier_box_ids = False
        show_charge_change_material_ids = False
        show_charge_label = False
        show_charge_monarch_ids = False

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
            if charge.applied_on == 'order_template_total' and \
                    charge.template_total_type == 'monarch_unattached_neck':
                show_charge_monarch_ids = True

        self.show_charge_product_box_ids = show_charge_product_box_ids
        self.show_charge_other_supplier_box_ids = \
            show_charge_other_supplier_box_ids
        self.show_charge_change_material_ids = show_charge_change_material_ids
        self.show_charge_label = show_charge_label
        self.show_charge_monarch_ids = show_charge_monarch_ids

    @api.depends(
        'charge_supplier_receipt_ids',
        'charge_product_box_ids',
        'charge_other_supplier_box_ids',
        'charge_change_material_ids',
        'label_qty',
        'charge_monarch_ids')
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

            if record.charge_monarch_ids:
                record.total_monarch_ids = sum(
                    record.charge_monarch_ids.mapped('amount'))

            if record.charge_supplier_receipt_ids:
                charges_by_order = record.charge_supplier_receipt_ids.filtered(
                    lambda charge: charge.applied_on == 'by_order'
                )
                for charge in charges_by_order:
                    if charge.amount_type == 'amount':
                        record.total_charges_by_order += charge.amount
                    else:
                        if record.purchase_id:
                            record.total_charges_by_order += (
                                record.purchase_id.amount_untaxed *
                                charge.percentage) / 100

    @api.multi
    def do_new_transfer(self):

        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']

        for picking in self:
            if picking.picking_type_id.code == 'incoming' and \
                    picking.purchase_id:

                if picking.charge_supplier_receipt_ids:

                    purchase_invoices = picking.purchase_id.invoice_ids.filtered(
                        lambda inv: inv.state != 'cancel'
                    )

                    invoice_origin = False
                    if purchase_invoices:
                        invoice_origin = purchase_invoices[0]

                        in_refund_invoice = AccountInvoice.create({
                            'type': 'in_refund',
                            'origin': invoice_origin.number,
                            'partner_id': purchase_invoices[0].partner_id.id,
                            'currency_id': purchase_invoices[0].currency_id.id,
                            'company_id': purchase_invoices[0].company_id.id,
                            'user_id': purchase_invoices[0].user_id.id,
                            'name': _('Charge to supplier over invoice of purchase order %s' % picking.purchase_id.name)
                        })

                    else:

                        in_refund_invoice = AccountInvoice.create({
                            'type': 'in_refund',
                            'partner_id': picking.partner_id.id,
                            'currency_id': picking.purchase_id.currency_id.id,
                            'company_id': picking.purchase_id.company_id.id,
                            'name': _('Charge to supplier over invoice of purchase order %s' % picking.purchase_id.name)
                        })

                    # The next lines of try applies only for MX
                    try:
                        in_refund_invoice.write({
                            'validate_attachment': True,
                            'validate_attachment2': True,
                        })
                    except Exception:
                        _logger.debug('MX l10n modules are not installed')
                        pass

                    charge_supplier_product = self.env.ref(
                        'stock_account_charges_supplier_receipts.product_charge_supplier_receipt')

                    if charge_supplier_product:

                        for charge in picking.charge_supplier_receipt_ids:

                            price_unit = 0
                            name = charge.name

                            if charge.applied_on == 'by_order':

                                if charge.amount_type == 'amount':
                                    price_unit = charge.amount
                                else:
                                    price_unit = (
                                        picking.purchase_id.amount_untaxed *
                                        charge.percentage) / 100

                            elif charge.applied_on == 'cost_per_box':
                                price_unit = \
                                    picking.total_charge_product_box_ids

                            elif charge.applied_on == 'double_cost_box':
                                price_unit = \
                                    picking.total_charge_other_supplier_box_ids

                            elif charge.applied_on == 'order_template_total' \
                                    and charge.template_total_type == \
                                    'change_material':

                                price_unit = \
                                    picking.total_charge_change_material_ids

                            elif charge.applied_on == 'label':
                                price_unit = picking.total_charge_label

                            elif charge.applied_on == 'order_template_total' \
                                    and charge.template_total_type == \
                                    'monarch_unattached_neck':

                                price_unit = picking.total_monarch_ids

                            if charge_supplier_product.supplier_taxes_id:
                                supplier_taxes_id = [
                                    (4, tax.id)
                                    for tax in
                                    charge_supplier_product.supplier_taxes_id]
                            else:
                                supplier_taxes_id = False

                            if not charge_supplier_product.property_account_expense_id:
                                raise ValidationError(
                                    _('Expense account is not configured for the product'))

                            AccountInvoiceLine.create({
                                'invoice_id': in_refund_invoice.id,
                                'product_id': charge_supplier_product.id,
                                'name': name,
                                'quantity': 1,
                                'price_unit': price_unit,
                                'partner_id': in_refund_invoice.partner_id.id,
                                'account_id':
                                charge_supplier_product.property_account_expense_id.id,
                                'invoice_line_tax_ids': supplier_taxes_id,
                            })

                        in_refund_invoice.compute_taxes()
                        in_refund_invoice.signal_workflow(
                            'invoice_open')

                        # Application of refund invoice over invoice of
                        # supplier
                        if invoice_origin:
                            credit_aml = \
                                in_refund_invoice.move_id.line_ids.filtered(
                                    lambda line: line.debit > 0 and
                                    line.credit == 0
                                )
                            if credit_aml:
                                application_refund_invoice = \
                                    self.pool.get('account.invoice').assign_outstanding_credit(
                                        self._cr,
                                        self._uid,
                                        invoice_origin.id,
                                        credit_aml[0].id,
                                        self._context
                                    )

                    else:
                        raise ValidationError(
                            _('The product "Charge to suppliers" has been deleted.'))

        return super(StockPicking, self).do_new_transfer()
