# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosPaymentSummaryWizard(models.TransientModel):
    _name = 'organic.pos.payment.summary.wizard'
    _description = 'POS Payment Summary Wizard'

    date_start = fields.Datetime(string='Start Date')
    date_stop = fields.Datetime(string='End Date')
    config_ids = fields.Many2many('pos.config', string='POS Configurations')
    session_ids = fields.Many2many('pos.session', string='Sessions')
    payment_method_ids = fields.Many2many('pos.payment.method', string='Payment Methods')
    group_by_session = fields.Boolean(string='Show Session Breakdown', default=False)
    group_by_config = fields.Boolean(string='Show POS Totals per Config', default=False)

    @api.onchange('config_ids')
    def _onchange_config_ids(self):
        if self.config_ids:
            return {'domain': {'session_ids': [('config_id', 'in', self.config_ids.ids)]}}
        return {'domain': {'session_ids': []}}

    def action_print_pdf(self):
        self.ensure_one()
        data = {
            'date_start': self.date_start and fields.Datetime.to_string(self.date_start) or False,
            'date_stop': self.date_stop and fields.Datetime.to_string(self.date_stop) or False,
            'config_ids': self.config_ids.ids,
            'session_ids': self.session_ids.ids,
            'payment_method_ids': self.payment_method_ids.ids,
            'group_by_session': self.group_by_session,
            'group_by_config': self.group_by_config,
        }
        action = self.env.ref('organic_pos_payment_summary.action_report_pos_payment_summary').report_action(docids=[], data=data)

        if isinstance(action, dict):
            action['close_on_report_download'] = False
        return action
