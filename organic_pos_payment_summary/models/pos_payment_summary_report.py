# -*- coding: utf-8 -*-
from datetime import timedelta

import pytz

from odoo import api, fields, models, _
from odoo.osv.expression import AND


class ReportPosPaymentSummary(models.AbstractModel):
    _name = 'report.organic_pos_payment_summary.report_pos_payment_summary'
    _description = 'POS Payment Method Summary'

    def _get_date_start_and_date_stop(self, date_start, date_stop):
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
            date_start = today.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)

        if date_stop:
            date_stop = fields.Datetime.from_string(date_stop)
            if date_stop < date_start:
                date_stop = date_start + timedelta(days=1, seconds=-1)
        else:
            date_stop = date_start + timedelta(days=1, seconds=-1)

        return date_start, date_stop

    def _get_domain(self, date_start=False, date_stop=False, config_ids=False, session_ids=False, payment_method_ids=False):
        domain = [('pos_order_id.state', 'in', ['paid', 'invoiced', 'done'])]

        if session_ids:
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            date_start, date_stop = self._get_date_start_and_date_stop(date_start, date_stop)
            domain = AND([domain, [
                ('payment_date', '>=', fields.Datetime.to_string(date_start)),
                ('payment_date', '<=', fields.Datetime.to_string(date_stop)),
            ]])
            if config_ids:
                domain = AND([domain, ['|', ('session_id.config_id', 'in', config_ids),
                                        '|', ('pos_order_id.session_id.config_id', 'in', config_ids),
                                             ('pos_order_id.config_id', 'in', config_ids)]])

        if payment_method_ids:
            domain = AND([domain, [('payment_method_id', 'in', payment_method_ids)]])

        return domain

    def _get_target_currency(self, config_ids=False, session_ids=False, payments=None):
        """Choose a single display currency.
        - If all selected pos.config share the same currency, use it.
        - Else if sessions provided, use their currency if unique.
        - Else fallback to company currency.
        """
        Currency = self.env['res.currency']
        user_currency = self.env.company.currency_id
        if config_ids:
            config_currencies = self.env['pos.config'].browse(config_ids).mapped('currency_id')
            if config_currencies and all(cid == config_currencies[0].id for cid in config_currencies.ids):
                user_currency = config_currencies[0]
        elif session_ids:
            session_currencies = self.env['pos.session'].browse(session_ids).mapped('config_id.currency_id')
            if session_currencies and all(cid == session_currencies[0].id for cid in session_currencies.ids):
                user_currency = session_currencies[0]
        elif payments is not None and payments:
            sessions = payments.mapped('session_id') or payments.mapped('pos_order_id.session_id')
            session_currencies = sessions.mapped('config_id.currency_id')
            if session_currencies and all(cid == session_currencies[0].id for cid in session_currencies.ids):
                user_currency = session_currencies[0]
        return user_currency

    def _convert_amount(self, amount, from_currency, to_currency, date):
        if not from_currency or from_currency == to_currency:
            return amount
        return from_currency._convert(amount, to_currency, self.env.company, date or fields.Date.today())

    @api.model
    def _compute_payment_summary(self, date_start=False, date_stop=False, config_ids=False, session_ids=False, payment_method_ids=False, group_by_session=False, group_by_config=False):
        domain = self._get_domain(date_start, date_stop, config_ids, session_ids, payment_method_ids)
        payments = self.env['pos.payment'].search(domain)

        target_currency = self._get_target_currency(config_ids, session_ids, payments)

        summary_map = {}
        session_breakdown = {}  
        configs_map = {}  

        for p in payments:
            method = p.payment_method_id
            method_id = method.id
            key = method_id

            amount_converted = self._convert_amount(p.amount, p.currency_id, target_currency, p.payment_date)
            session = p.session_id or (p.pos_order_id and p.pos_order_id.session_id)
            config = None
            if session and session.config_id:
                config = session.config_id
            elif getattr(p, 'pos_order_id', False):
                config = p.pos_order_id.config_id or (p.pos_order_id.session_id and p.pos_order_id.session_id.config_id)

            if key not in summary_map:
                summary_map[key] = {
                    'method_id': method_id,
                    'method_name': method.name,
                    'is_cash': method.is_cash_count,
                    'payments_count': 0,
                    'sessions': set(),
                    'in_amount': 0.0,          
                    'change_amount': 0.0,      
                    'net_amount': 0.0,         
                }
            rec = summary_map[key]
            rec['payments_count'] += 1
            if session:
                rec['sessions'].add(session.id)

            if p.is_change:
                rec['change_amount'] += amount_converted
            else:
                rec['in_amount'] += amount_converted
            rec['net_amount'] += amount_converted

            if group_by_session and session:
                session_breakdown.setdefault(key, {})
                session_breakdown[key].setdefault(session.id, 0.0)
                session_breakdown[key][session.id] += amount_converted

            if group_by_config and config:
                cfg = config
                cfg_key = cfg.id
                if cfg_key not in configs_map:
                    configs_map[cfg_key] = {
                        'config_id': cfg_key,
                        'config_name': cfg.name,
                        'payments_count': 0,
                        'sessions': set(),
                        'in_amount': 0.0,
                        'change_amount': 0.0,
                        'net_amount': 0.0,
                    }
                crec = configs_map[cfg_key]
                crec['payments_count'] += 1
                if p.session_id:
                    crec['sessions'].add(p.session_id.id)
                if p.is_change:
                    crec['change_amount'] += amount_converted
                else:
                    crec['in_amount'] += amount_converted
                crec['net_amount'] += amount_converted


        summary = []
        totals = {'in_amount': 0.0, 'change_amount': 0.0, 'net_amount': 0.0, 'payments_count': 0, 'sessions_count': 0}
        all_sessions_set = set()
        for key, rec in summary_map.items():
            line = {
                'method_id': rec['method_id'],
                'method_name': rec['method_name'],
                'is_cash': rec['is_cash'],
                'in_amount': target_currency.round(rec['in_amount']),
                'change_amount': target_currency.round(rec['change_amount']),
                'net_amount': target_currency.round(rec['net_amount']),
                'payments_count': rec['payments_count'],
                'sessions_count': len(rec['sessions']),
            }
            totals['in_amount'] += line['in_amount']
            totals['change_amount'] += line['change_amount']
            totals['net_amount'] += line['net_amount']
            totals['payments_count'] += line['payments_count']
            all_sessions_set.update(rec['sessions'])
            summary.append(line)

        totals['sessions_count'] = len(all_sessions_set)

        summary.sort(key=lambda l: l['net_amount'], reverse=True)

        session_lines = []
        if group_by_session and session_breakdown:
            Session = self.env['pos.session']
            for method_id, sessions_map in session_breakdown.items():
                method_name = self.env['pos.payment.method'].browse(method_id).name
                for session_id, amount in sessions_map.items():
                    session = Session.browse(session_id)
                    session_lines.append({
                        'method_id': method_id,
                        'method_name': method_name,
                        'session_id': session_id,
                        'session_name': session.name,
                        'amount': target_currency.round(amount),
                    })
            session_lines.sort(key=lambda l: (l['method_name'], l['session_name']))

        config_lines = []
        if group_by_config and configs_map:
            for cfg_id, rec in configs_map.items():
                config_lines.append({
                    'config_id': rec['config_id'],
                    'config_name': rec['config_name'],
                    'payments_count': rec['payments_count'],
                    'sessions_count': len(rec['sessions']),
                    'in_amount': target_currency.round(rec['in_amount']),
                    'change_amount': target_currency.round(rec['change_amount']),
                    'net_amount': target_currency.round(rec['net_amount']),
                })
            config_lines.sort(key=lambda l: l['net_amount'], reverse=True)

        return summary, totals, target_currency, session_lines, config_lines

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        group_by_session = bool(data.get('group_by_session'))
        group_by_config = bool(data.get('group_by_config'))

        date_start = data.get('date_start')
        date_stop = data.get('date_stop')
        config_ids = data.get('config_ids') or []
        session_ids = data.get('session_ids') or []
        payment_method_ids = data.get('payment_method_ids') or []

        summary, totals, currency, session_lines, config_lines = self._compute_payment_summary(
            date_start=date_start,
            date_stop=date_stop,
            config_ids=config_ids,
            session_ids=session_ids,
            payment_method_ids=payment_method_ids,
            group_by_session=group_by_session,
            group_by_config=group_by_config,
        )

        config_names = self.env['pos.config'].browse(config_ids).mapped('name') if config_ids else []
        method_names = self.env['pos.payment.method'].browse(payment_method_ids).mapped('name') if payment_method_ids else []
        session_names = self.env['pos.session'].browse(session_ids).mapped('name') if session_ids else []
        date_start_disp, date_stop_disp = self._get_date_start_and_date_stop(date_start, date_stop)

        return {
            'company_name': self.env.company.name,
            'date_start': date_start_disp,
            'date_stop': date_stop_disp,
            'summary': summary,
            'totals': totals,
            'currency': currency,
            'group_by_session': group_by_session,
            'session_lines': session_lines,
            'group_by_config': group_by_config,
            'config_lines': config_lines,
            'config_names': config_names,
            'method_names': method_names,
            'session_names': session_names,
        }

