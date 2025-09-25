# -*- coding: utf-8 -*-
from odoo import models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def _get_discount_amount(self):


        self.ensure_one()
        order = self.order_id
        currency = (
            (order.pricelist_id and order.pricelist_id.currency_id)
            or (order.session_id and order.session_id.currency_id)
            or order.company_id.currency_id
        )
        partner = order.partner_id
        product = self.product_id
        qty = self.qty


        original_total = self.tax_ids.compute_all(
            self.price_unit,
            currency,
            qty,
            product=product,
            partner=partner,
        )['total_included']

        if getattr(self, 'discount_line_type', False) in ('Fixed', 'fixed'):
            discounted_unit = self.price_unit - (self.discount or 0.0)
        else:
            discounted_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        after_total = self.tax_ids.compute_all(
            discounted_unit,
            currency,
            qty,
            product=product,
            partner=partner,
        )['total_included']

        return original_total - after_total
