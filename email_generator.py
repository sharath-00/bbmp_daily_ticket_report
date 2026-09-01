from datetime import datetime
from typing import Dict, Any

def generate_html_email_report(analytics: Dict[str, Any], date_label: str = "Today") -> str:
    """
    Generates a beautifully styled, email-client compatible HTML report.
    """
    total_tickets = analytics.get("total_tickets", 0)
    open_tickets = analytics.get("open_tickets", 0)
    open_slc = analytics.get("open_slc_panels", 0)
    open_lamps = analytics.get("open_lamps", 0)
    closed_tickets = analytics.get("closed_tickets", 0)
    resolution_rate = analytics.get("resolution_rate_percent", 0.0)

    today_total = analytics.get("today_total_tickets", 0)
    today_open = analytics.get("today_open_tickets", 0)
    today_open_slc = analytics.get("today_open_slc_panels", 0)
    today_open_lamps = analytics.get("today_open_lamps", 0)
    today_closed = analytics.get("today_closed_tickets", 0)
    today_res_rate = analytics.get("today_resolution_rate_percent", 0.0)

    july1_total = analytics.get("july1_total_tickets", 0)
    july1_open = analytics.get("july1_open_tickets", 0)
    july1_open_slc = analytics.get("july1_open_slc_panels", 0)
    july1_open_lamps = analytics.get("july1_open_lamps", 0)
    july1_closed = analytics.get("july1_closed_tickets", 0)
    july1_res_rate = analytics.get("july1_resolution_rate_percent", 0.0)
    
    u7_30_count = analytics.get("unresolved_7_to_30_days_count", analytics.get("unresolved_over_7_days_count", 0))
    u30_count = analytics.get("unresolved_over_30_days_count", 0)
    u30_tickets = analytics.get("unresolved_over_30_days_tickets", [])

    u30_rows_html = ""
    for t in u30_tickets[:10]:
        t_id = t.get("ticket_id", "")
        t_days = t.get("days_unresolved", 0)
        t_zone = t.get("zone", "")
        t_prob = t.get("problem_type", "")
        t_loc = str(t.get("location", ""))[:35]
        u30_rows_html += f"""
        <tr style="border-bottom: 1px solid #fee2e2;">
            <td style="padding: 6px 8px; font-weight: 700; color: #991b1b;">{t_id}</td>
            <td style="padding: 6px 8px; text-align: center; font-weight: 800; color: #dc2626;">{t_days} Days</td>
            <td style="padding: 6px 8px; color: #1e293b; font-weight: 600;">{t_zone}</td>
            <td style="padding: 6px 8px; color: #475569;">{t_prob}</td>
            <td style="padding: 6px 8px; color: #64748b; font-size: 10px;">{t_loc}</td>
        </tr>
        """

    zone_breakdown = analytics.get("zone_breakdown", {})
    complainee_breakdown = analytics.get("complainee_breakdown", {})
    full_complainee_breakdown = analytics.get("full_complainee_breakdown", complainee_breakdown)
    problem_breakdown = analytics.get("problem_type_breakdown", {})
    
    official_stats = full_complainee_breakdown.get("Officials", full_complainee_breakdown.get("Official", {}))
    official_total = official_stats.get("total", 0)
    official_open = official_stats.get("open", 0)
    official_closed = official_stats.get("closed", 0)
    official_closure_rate = round((official_closed / official_total * 100), 1) if official_total > 0 else 0.0

    generated_at = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    # Render Zone Rows (Top 15 Zones)
    zone_rows_html = ""
    for zone_name, stats in list(zone_breakdown.items())[:15]:
        z_total = stats.get("total", 0)
        z_open = stats.get("open", 0)
        z_closed = stats.get("closed", 0)
        z_rate = round((z_closed / z_total * 100), 1) if z_total > 0 else 0.0
        
        # Color badge for open
        open_badge = f'<span style="background-color: #ffe4e6; color: #e11d48; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">{z_open}</span>' if z_open > 0 else f'<span style="color: #64748b;">0</span>'
        
        zone_rows_html += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px 12px; font-weight: 600; color: #1e293b;">{zone_name}</td>
            <td style="padding: 10px 12px; text-align: center; color: #334155; font-weight: 600;">{z_total}</td>
            <td style="padding: 10px 12px; text-align: center;">{open_badge}</td>
            <td style="padding: 10px 12px; text-align: center; color: #16a34a; font-weight: 600;">{z_closed}</td>
            <td style="padding: 10px 12px; text-align: center;">
                <div style="background: #e2e8f0; border-radius: 6px; height: 8px; width: 80px; display: inline-block; overflow: hidden; vertical-align: middle; margin-right: 6px;">
                    <div style="background: #10b981; height: 100%; width: {z_rate}%;"></div>
                </div>
                <span style="font-size: 11px; font-weight: 600; color: #475569;">{z_rate}%</span>
            </td>
        </tr>
        """

    # Render Complainee Rows
    complainee_rows_html = ""
    for comp_name, stats in list(complainee_breakdown.items())[:10]:
        c_total = stats.get("total", 0)
        c_open = stats.get("open", 0)
        c_closed = stats.get("closed", 0)
        c_share = round((c_total / total_tickets * 100), 1) if total_tickets > 0 else 0.0

        complainee_rows_html += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px 12px; font-weight: 600; color: #1e293b;">{comp_name}</td>
            <td style="padding: 10px 12px; text-align: center; color: #334155; font-weight: 600;">{c_total}</td>
            <td style="padding: 10px 12px; text-align: center; color: #e11d48; font-weight: 600;">{c_open}</td>
            <td style="padding: 10px 12px; text-align: center; color: #16a34a; font-weight: 600;">{c_closed}</td>
            <td style="padding: 10px 12px; text-align: center; color: #475569; font-weight: 500;">{c_share}%</td>
        </tr>
        """

    # Render Problem Rows (Top 8)
    problem_rows_html = ""
    for prob_name, p_count in list(problem_breakdown.items())[:8]:
        p_share = round((p_count / total_tickets * 100), 1) if total_tickets > 0 else 0.0
        problem_rows_html += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 12px; color: #1e293b; font-weight: 500;">{prob_name}</td>
            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: #4f46e5;">{p_count}</td>
            <td style="padding: 8px 12px; text-align: center; color: #64748b; font-size: 11px;">{p_share}%</td>
        </tr>
        """

    # Render 7-Day Clustered Bar Chart HTML (Open vs Closed)
    past_7_trend = analytics.get("past_7_days_trend", {})
    max_val = max([max(s.get("open", 0), s.get("closed", 0)) for s in past_7_trend.values()] or [1])
    if max_val <= 0:
        max_val = 1

    chart_columns_html = ""
    for d_str, s in past_7_trend.items():
        o_cnt = s.get("open", 0)
        c_cnt = s.get("closed", 0)

        # Scale bar height between 4px (min visible height if >0) and 100px (max height)
        o_h = max(4, int((o_cnt / max_val) * 100)) if o_cnt > 0 else 0
        c_h = max(4, int((c_cnt / max_val) * 100)) if c_cnt > 0 else 0

        try:
            d_lbl = datetime.strptime(d_str, "%Y-%m-%d").strftime("%d %b")
        except Exception:
            d_lbl = d_str

        chart_columns_html += f"""
        <td width="14%" align="center" valign="bottom" style="padding: 0 4px;">
            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td valign="bottom" align="center" style="padding-right: 2px;">
                        <div style="font-size: 10px; font-weight: 700; color: #e11d48; text-align: center; margin-bottom: 2px;">{o_cnt if o_cnt > 0 else ''}</div>
                        <div style="background-color: #e11d48; width: 16px; height: {o_h}px; border-radius: 3px 3px 0 0; margin: 0 auto;"></div>
                    </td>
                    <td valign="bottom" align="center" style="padding-left: 2px;">
                        <div style="font-size: 10px; font-weight: 700; color: #16a34a; text-align: center; margin-bottom: 2px;">{c_cnt if c_cnt > 0 else ''}</div>
                        <div style="background-color: #10b981; width: 16px; height: {c_h}px; border-radius: 3px 3px 0 0; margin: 0 auto;"></div>
                    </td>
                </tr>
            </table>
            <div style="font-size: 10px; color: #475569; margin-top: 8px; font-weight: 600; text-align: center;">{d_lbl}</div>
        </td>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BBMP Daily Ticket Analytics Report</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 20px 0;">
            <tr>
                <td align="center">
                    <!-- Main Container Card -->
                    <table border="0" cellpadding="0" cellspacing="0" width="680" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
                        
                        <!-- Header Banner -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%); padding: 30px 32px; color: #ffffff;">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td>
                                            <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #818cf8; margin-bottom: 4px;">Schnell IoT Cloud Analytics</div>
                                            <h1 style="margin: 0; font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">BBMP Smart Light Lamp Ticket Dashboard</h1>
                                            <div style="font-size: 13px; color: #c7d2fe; margin-top: 6px;">Official Executive Daily Report (Lamp Tickets Only) &bull; Period: <strong>{date_label}</strong></div>
                                        </td>
                                        <td align="right" valign="top">
                                            <div style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 8px 12px; text-align: right; color: #ffffff; font-size: 11px;">
                                                <div><strong>Generated On</strong></div>
                                                <div style="color: #cbd5e1; margin-top: 2px;">{generated_at}</div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Exclusion Notice -->
                        <tr>
                            <td style="background-color: #eff6ff; padding: 10px 32px; border-bottom: 1px solid #dbeafe; color: #1e40af; font-size: 12px; font-weight: 600; text-align: center;">
                                &#9432; Note: SLC Panel tickets &amp; Automated tickets ("Auto") are excluded from all metrics to focus strictly on Lamp operational issues.
                            </td>
                        </tr>

                        <!-- KPI Section 1: July 1st to Present Ticket Metrics -->
                        <tr>
                            <td style="padding: 20px 32px 10px 32px; background-color: #ffffff;">
                                <div style="font-size: 13px; font-weight: 700; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                                    Lamp Tickets Summary (Raised From July 1st)
                                </div>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <!-- Raised Since July 1st -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">Raised (From July 1)</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #1e1b4b; margin: 4px 0;">{july1_total}</div>
                                                <div style="font-size: 10px; color: #64748b;">July 1st to Date</div>
                                            </div>
                                        </td>

                                        <!-- Open Since July 1st -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #e11d48; text-transform: uppercase; letter-spacing: 0.5px;">Open (From July 1)</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #e11d48; margin: 4px 0;">{july1_open}</div>
                                                <div style="font-size: 10px; font-weight: 700; color: #9f1239;">{july1_open} Lamp Tickets</div>
                                            </div>
                                        </td>

                                        <!-- Closed Since July 1st -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #f0fdf4; border: 1px solid #a7f3d0; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #15803d; text-transform: uppercase; letter-spacing: 0.5px;">Closed (From July 1)</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #16a34a; margin: 4px 0;">{july1_closed}</div>
                                                <div style="font-size: 10px; color: #14532d;">Resolved</div>
                                            </div>
                                        </td>

                                        <!-- July 1st Resolution Rate -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #4338ca; text-transform: uppercase; letter-spacing: 0.5px;">Resolution Rate</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #3730a3; margin: 4px 0;">{july1_res_rate}%</div>
                                                <div style="font-size: 10px; color: #4338ca;">July 1st to Date</div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- KPI Section 2: Selected Period Overview -->
                        <tr>
                            <td style="padding: 10px 32px 16px 32px; background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                                <div style="font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                                    Period Overview ({date_label})
                                </div>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <!-- KPI 1: Total Raised -->
                                        <td width="23%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Total Raised</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #312e81; margin: 4px 0;">{total_tickets}</div>
                                                <div style="font-size: 10px; color: #475569;">Period Total</div>
                                            </div>
                                        </td>
                                        <td width="23%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #fecdd3; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #e11d48; text-transform: uppercase; letter-spacing: 0.5px;">Total Open</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #e11d48; margin: 4px 0;">{open_tickets}</div>
                                                <div style="font-size: 10px; font-weight: 700; color: #9f1239;">{open_tickets} Lamp Tickets</div>
                                            </div>
                                        </td>

                                        <!-- KPI 3: Closed Tickets -->
                                        <td width="23%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #a7f3d0; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">Total Closed</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #16a34a; margin: 4px 0;">{closed_tickets}</div>
                                                <div style="font-size: 10px; color: #065f46;">Period Closed</div>
                                            </div>
                                        </td>

                                        <!-- KPI 4: Resolution Rate -->
                                        <td width="30%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #c7d2fe; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #4f46e5; text-transform: uppercase; letter-spacing: 0.5px;">Resolution Rate</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #4338ca; margin: 4px 0;">{resolution_rate}%</div>
                                                <div style="font-size: 10px; color: #3730a3;">Period Rate</div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Unresolved Fault Aging Overview (> 7 Days & > 30 Days) -->
                        <tr>
                            <td style="padding: 16px 32px; background-color: #ffffff; border-bottom: 1px solid #e2e8f0;">
                                <div style="font-size: 13px; font-weight: 700; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                                    Unresolved Fault Aging Overview
                                </div>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <!-- Unresolved 7 - 30 Days Card -->
                                        <td width="50%" style="padding: 4px;">
                                            <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 11px; font-weight: 700; color: #b45309; text-transform: uppercase; letter-spacing: 0.5px;">Unresolved 7 - 30 Days</div>
                                                <div style="font-size: 24px; font-weight: 800; color: #d97706; margin: 4px 0;">{u7_30_count} <span style="font-size: 13px; font-weight: 600;">Tickets</span></div>
                                                <div style="font-size: 10px; color: #92400e; font-weight: 600;">Action Required (7 - 30 Days Pending)</div>
                                            </div>
                                        </td>

                                        <!-- Unresolved > 30 Days Card -->
                                        <td width="50%" style="padding: 4px;">
                                            <div style="background: #fef2f2; border: 1px solid #fca5a5; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 11px; font-weight: 700; color: #991b1b; text-transform: uppercase; letter-spacing: 0.5px;">Unresolved > 30 Days (Critical)</div>
                                                <div style="font-size: 24px; font-weight: 800; color: #dc2626; margin: 4px 0;">{u30_count} <span style="font-size: 13px; font-weight: 600;">Tickets</span></div>
                                                <div style="font-size: 10px; color: #991b1b; font-weight: 700;">Critical Escalation Required (&gt; 30 Days Pending)</div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Sahaya App Tickets Summary (Official Complainees) -->
                        <tr>
                            <td style="padding: 16px 32px; background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                                <div style="font-size: 13px; font-weight: 700; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                                    Sahaya App Tickets Summary
                                </div>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <!-- Official Total -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">Total Officials Tickets</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #1e1b4b; margin: 4px 0;">{official_total}</div>
                                                <div style="font-size: 10px; color: #64748b;">All-Time Registered</div>
                                            </div>
                                        </td>

                                        <!-- Official Open -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #fecdd3; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #e11d48; text-transform: uppercase; letter-spacing: 0.5px;">Open Tickets</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #e11d48; margin: 4px 0;">{official_open}</div>
                                                <div style="font-size: 10px; font-weight: 700; color: #9f1239;">Pending Resolution</div>
                                            </div>
                                        </td>

                                        <!-- Official Closed -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #a7f3d0; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">Closed Tickets</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #16a34a; margin: 4px 0;">{official_closed}</div>
                                                <div style="font-size: 10px; color: #065f46;">Total Resolved</div>
                                            </div>
                                        </td>

                                        <!-- Official Closure Rate -->
                                        <td width="25%" style="padding: 4px;">
                                            <div style="background: #ffffff; border: 1px solid #c7d2fe; border-radius: 10px; padding: 14px; text-align: center;">
                                                <div style="font-size: 10px; font-weight: 700; color: #4338ca; text-transform: uppercase; letter-spacing: 0.5px;">Closure Rate</div>
                                                <div style="font-size: 22px; font-weight: 800; color: #3730a3; margin: 4px 0;">{official_closure_rate}%</div>
                                                <div style="font-size: 10px; color: #4338ca;">Overall Closure Rate</div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Section: Zone-Wise Breakdown -->
                        <tr>
                            <td style="padding: 24px 32px;">
                                <h3 style="margin: 0 0 14px 0; font-size: 16px; font-weight: 700; color: #1e293b; display: flex; align-items: center;">
                                    <span style="display: inline-block; width: 4px; height: 16px; background: #4f46e5; margin-right: 8px; border-radius: 2px;"></span>
                                    Zone-Wise Breakdown (Top Zones)
                                </h3>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; font-size: 12px;">
                                    <thead>
                                        <tr style="background-color: #f8fafc; border-bottom: 2px solid #cbd5e1; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 11px;">
                                            <th align="left" style="padding: 10px 12px;">Zone Name</th>
                                            <th align="center" style="padding: 10px 12px;">Total</th>
                                            <th align="center" style="padding: 10px 12px;">Open</th>
                                            <th align="center" style="padding: 10px 12px;">Closed</th>
                                            <th align="center" style="padding: 10px 12px;">Resolution %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {zone_rows_html if zone_rows_html else '<tr><td colspan="5" style="padding:16px; text-align:center; color:#94a3b8;">No zone data available.</td></tr>'}
                                    </tbody>
                                </table>
                            </td>
                        </tr>

                        <!-- Section: Complainee Breakdown & Top Problems side by side -->
                        <tr>
                            <td style="padding: 0 32px 24px 32px;">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <!-- Left Column: Complainee Breakdown -->
                                        <td width="55%" valign="top" style="padding-right: 12px;">
                                            <h3 style="margin: 0 0 14px 0; font-size: 15px; font-weight: 700; color: #1e293b;">
                                                Complainee-Wise Breakdown
                                            </h3>
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; font-size: 12px;">
                                                <thead>
                                                    <tr style="background-color: #f8fafc; border-bottom: 2px solid #cbd5e1; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 10px;">
                                                        <th align="left" style="padding: 8px 10px;">Complainee</th>
                                                        <th align="center" style="padding: 8px 10px;">Total</th>
                                                        <th align="center" style="padding: 8px 10px;">Open</th>
                                                        <th align="center" style="padding: 8px 10px;">Closed</th>
                                                        <th align="center" style="padding: 8px 10px;">Share</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {complainee_rows_html}
                                                </tbody>
                                            </table>
                                        </td>

                                        <!-- Right Column: Top Problem Types -->
                                        <td width="45%" valign="top" style="padding-left: 12px;">
                                            <h3 style="margin: 0 0 14px 0; font-size: 15px; font-weight: 700; color: #1e293b;">
                                                Top Problem Types
                                            </h3>
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; font-size: 12px;">
                                                <thead>
                                                    <tr style="background-color: #f8fafc; border-bottom: 2px solid #cbd5e1; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 10px;">
                                                        <th align="left" style="padding: 8px 10px;">Problem Type</th>
                                                        <th align="center" style="padding: 8px 10px;">Count</th>
                                                        <th align="center" style="padding: 8px 10px;">Share</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {problem_rows_html}
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Section: 7-Day Clustered Bar Chart (Open vs Closed) -->
                        <tr>
                            <td style="padding: 0 32px 24px 32px;">
                                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                        <tr>
                                            <td>
                                                <h3 style="margin: 0; font-size: 15px; font-weight: 700; color: #1e293b; display: flex; align-items: center;">
                                                    <span style="display: inline-block; width: 4px; height: 16px; background: #6366f1; margin-right: 8px; border-radius: 2px;"></span>
                                                    7-Day Ticket Activity Trend (Clustered Open vs Closed)
                                                </h3>
                                                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Daily breakdown of Open &amp; Closed tickets for the past 7 days</div>
                                            </td>
                                            <td align="right" valign="middle">
                                                <!-- Legend -->
                                                <span style="font-size: 11px; font-weight: 700; color: #e11d48; margin-right: 14px;">
                                                    <span style="display: inline-block; width: 10px; height: 10px; background-color: #e11d48; border-radius: 2px; margin-right: 4px; vertical-align: middle;"></span>Open
                                                </span>
                                                <span style="font-size: 11px; font-weight: 700; color: #16a34a;">
                                                    <span style="display: inline-block; width: 10px; height: 10px; background-color: #10b981; border-radius: 2px; margin-right: 4px; vertical-align: middle;"></span>Closed
                                                </span>
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Clustered Bars Grid -->
                                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 20px;">
                                        <tr>
                                            {chart_columns_html}
                                        </tr>
                                    </table>
                                </div>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; text-align: center; color: #64748b; font-size: 11px;">
                                <div style="font-weight: 600; color: #475569;">BBMP Smart Light Ticket Analytics System &bull; Schnell Energy Technologies</div>
                                <div style="margin-top: 4px;">This is an automated executive daily digest sent to higher officials.</div>
                                <div style="margin-top: 8px; font-size: 10px; color: #94a3b8;">Confidential &bull; For internal official use only.</div>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html
