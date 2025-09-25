# -*- coding: utf-8 -*-
{
    'name': 'POS Payment Method Summary - Professional Reports',
    'summary': 'Advanced POS payment reporting with PDF output, multi-currency support, session analytics & professional layouts for comprehensive financial analysis',
    'description': """
Professional POS Payment Method Summary Reports
==============================================

Transform your Point of Sale financial reporting with this comprehensive module that generates professional PDF reports summarizing payment transactions by method, session, and configuration.

Key Features:
• Advanced payment method analysis with detailed breakdowns
• Multi-currency support with automatic conversion
• Session-by-session breakdown for detailed analysis  
• POS configuration comparison across multiple terminals
• Professional PDF reports with company branding
• Flexible filtering by date range, sessions, payment methods
• Change amount tracking for accurate cash reconciliation
• User-friendly wizard interface for easy report generation
• Optimized performance for large datasets
• Complete audit trail and compliance support

Perfect for:
• Multi-location retailers needing standardized reporting
• Franchise operations requiring performance benchmarking
• Hospitality businesses tracking payment patterns
• Any business requiring detailed POS financial analysis

Business Benefits:
• Save hours of manual calculation and reporting time
• Improve financial accuracy with automated reconciliation
• Make data-driven decisions with comprehensive analytics
• Ensure audit compliance with professional documentation
• Optimize payment processing across locations

Technical Excellence:
• Efficient database queries for fast report generation
• Secure access controls and proper user permissions
• Clean, maintainable code following Odoo best practices
• Extensive documentation and professional support included

Investment: $99 USD (One-time payment)
Includes: 6 months support, 1 year of updates, customization consultation
Contact: WhatsApp +967711778764 for immediate assistance
    """,
    'version': '18.0.1.0.0',
    'category': 'Point of Sale/Reporting',
    'author': "Salah Alhjany - Professional Odoo Developer",
    'website': "https://wa.me/967711778764",
    'license': 'OPL-1',
    'price': 99.0,
    'currency': 'USD',
    'depends': ['point_of_sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_payment_summary_wizard_views.xml',
        'reports/pos_payment_summary_report_templates.xml',
        'reports/pos_payment_summary_report_actions.xml',
    ],
    'assets': {},
    'installable': True,
    'application': False,
    'auto_install': False,
    'icon': 'static/description/icon.png',
}
