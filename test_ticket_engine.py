import unittest
from datetime import datetime
from ticket_engine import TicketEngine, parse_ticket_document, extract_field_val, is_bbmp_ticket, is_slc_panel_ticket, is_lamp_ticket

class TestTicketEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TicketEngine()
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.sample_docs = [
            {
                "name": "projects/test/databases/test/documents/tickets/doc1",
                "fields": {
                    "ticket_id": {"stringValue": "TCK001"},
                    "status": {"stringValue": "Open"},
                    "zone": {"stringValue": "Yelahanka"},
                    "ward": {"stringValue": "Ward 1"},
                    "complainee": {"stringValue": "System"},
                    "problem_type": {"stringValue": "Power Outage"},
                    "priority": {"stringValue": "Major"},
                    "ticket_opened_on": {"stringValue": f"{today_str} 09:15:00"},
                    "region": {"stringValue": "EAST"},
                    "customer": {"stringValue": "Bangalore (BBMP)"},
                    "entity_type": {"stringValue": "Lamp"}
                }
            },
            {
                "name": "projects/test/databases/test/documents/tickets/doc2",
                "fields": {
                    "ticket_id": {"stringValue": "TCK002"},
                    "status": {"stringValue": "Closed"},
                    "zone": {"stringValue": "Yelahanka"},
                    "ward": {"stringValue": "Ward 2"},
                    "complainee": {"stringValue": "Auto"},
                    "problem_type": {"stringValue": "Voltage Low"},
                    "priority": {"stringValue": "Minor"},
                    "ticket_opened_on": {"stringValue": f"{today_str} 10:30:00"},
                    "ticket_closed_on": {"stringValue": f"{today_str} 11:00:00"},
                    "region": {"stringValue": "EAST"},
                    "customer": {"stringValue": "Bangalore (BBMP)"},
                    "entity_type": {"stringValue": "Lamp"}
                }
            },
            {
                "name": "projects/test/databases/test/documents/tickets/doc3",
                "fields": {
                    "ticket_id": {"stringValue": "TCK003"},
                    "status": {"stringValue": "Closed"},
                    "zone": {"stringValue": "East"},
                    "ward": {"stringValue": "Ward 10"},
                    "complainee": {"stringValue": "System"},
                    "problem_type": {"stringValue": "Power Outage"},
                    "priority": {"stringValue": "Critical"},
                    "ticket_opened_on": {"stringValue": "2026-08-03 14:00:00"},
                    "ticket_closed_on": {"stringValue": "2026-08-03 16:00:00"},
                    "region": {"stringValue": "Bommanahali"},
                    "customer": {"stringValue": "Bangalore (BBMP)"},
                    "entity_type": {"stringValue": "Lamp"}
                }
            },
            {
                "name": "projects/test/databases/test/documents/tickets/doc4",
                "fields": {
                    "ticket_id": {"stringValue": "TCK004"},
                    "status": {"stringValue": "Open"},
                    "zone": {"stringValue": "East"},
                    "ward": {"stringValue": "Ward 11"},
                    "complainee": {"stringValue": "System"},
                    "problem_type": {"stringValue": "SLC Communication Failure"},
                    "priority": {"stringValue": "Critical"},
                    "ticket_opened_on": {"stringValue": f"{today_str} 12:00:00"},
                    "region": {"stringValue": "EAST"},
                    "customer": {"stringValue": "Bangalore (BBMP)"},
                    "entity_type": {"stringValue": "SLC Panel"}
                }
            }
        ]
        self.raw_tickets = [parse_ticket_document(d) for d in self.sample_docs]
        self.valid_bbmp_tickets = [t for t in self.raw_tickets if is_bbmp_ticket(t)]

    def test_auto_ticket_exclusion(self):
        # Verify doc2 (Auto) is rejected by is_bbmp_ticket
        self.assertTrue(is_bbmp_ticket(self.raw_tickets[0]))
        self.assertFalse(is_bbmp_ticket(self.raw_tickets[1]))
        self.assertTrue(is_bbmp_ticket(self.raw_tickets[2]))
        self.assertTrue(is_bbmp_ticket(self.raw_tickets[3]))

    def test_slc_panel_exclusion(self):
        # Verify SLC Panel ticket identification and exclusion
        self.assertFalse(is_slc_panel_ticket(self.raw_tickets[0]))
        self.assertTrue(is_lamp_ticket(self.raw_tickets[0]))

        self.assertTrue(is_slc_panel_ticket(self.raw_tickets[3]))
        self.assertFalse(is_lamp_ticket(self.raw_tickets[3]))

        filtered_lamps = self.engine.filter_tickets(self.raw_tickets, lamps_only=True)
        lamp_ids = [t["ticket_id"] for t in filtered_lamps]
        self.assertIn("TCK001", lamp_ids)
        self.assertNotIn("TCK004", lamp_ids)

    def test_filter_by_date(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        filtered_today = self.engine.filter_tickets(self.raw_tickets, target_date=today_str)
        # Should include TCK001 (Lamp) and exclude TCK002 (Auto) and TCK004 (SLC Panel)
        self.assertEqual(len(filtered_today), 1)
        self.assertEqual(filtered_today[0]["ticket_id"], "TCK001")

        filtered_aug3 = self.engine.filter_tickets(self.raw_tickets, target_date="2026-08-03")
        self.assertEqual(len(filtered_aug3), 1)
        self.assertEqual(filtered_aug3[0]["ticket_id"], "TCK003")

    def test_analytics_calculation(self):
        analytics = self.engine.analyze_tickets(self.valid_bbmp_tickets)
        # TCK001 (Open Lamp) and TCK003 (Closed Lamp) are included. TCK002 (Auto) and TCK004 (SLC Panel) excluded.
        self.assertEqual(analytics["total_tickets"], 2)
        self.assertEqual(analytics["open_tickets"], 1)
        self.assertEqual(analytics["closed_tickets"], 1)
        self.assertAlmostEqual(analytics["resolution_rate_percent"], 50.0, places=2)

        # Verify today's metrics
        self.assertEqual(analytics["today_total_tickets"], 1)
        self.assertEqual(analytics["today_open_tickets"], 1)
        self.assertEqual(analytics["today_closed_tickets"], 0)

        # Verify Past 7 Days Clustered Trend
        self.assertIn("past_7_days_trend", analytics)
        self.assertEqual(len(analytics["past_7_days_trend"]), 7)
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.assertIn(today_str, analytics["past_7_days_trend"])
        self.assertIn("open", analytics["past_7_days_trend"][today_str])
        self.assertIn("closed", analytics["past_7_days_trend"][today_str])

        # Complainee Breakdown verification (Auto must NOT be present)
        self.assertIn("System", analytics["complainee_breakdown"])
        self.assertNotIn("Auto", analytics["complainee_breakdown"])

    def test_unresolved_aging_separation(self):
        from datetime import datetime, timedelta
        now = datetime.now()
        t_5_days = (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        t_15_days = (now - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
        t_45_days = (now - timedelta(days=45)).strftime("%Y-%m-%d %H:%M:%S")

        aging_tickets = [
            {"ticket_id": "T5", "status": "Open", "ticket_opened_on": t_5_days, "complainee": "User", "region": "EAST", "entity_type": "Lamp"},
            {"ticket_id": "T15", "status": "Open", "ticket_opened_on": t_15_days, "complainee": "User", "region": "EAST", "entity_type": "Lamp"},
            {"ticket_id": "T45", "status": "Open", "ticket_opened_on": t_45_days, "complainee": "User", "region": "EAST", "entity_type": "Lamp"},
        ]

        analytics = self.engine.analyze_tickets(aging_tickets)
        
        u7_30_ids = [t["ticket_id"] for t in analytics["unresolved_7_to_30_days_tickets"]]
        u30_ids = [t["ticket_id"] for t in analytics["unresolved_over_30_days_tickets"]]

        self.assertIn("T15", u7_30_ids)
        self.assertNotIn("T45", u7_30_ids, "Tickets > 30 days must NOT be in 7-30 days list")
        self.assertNotIn("T5", u7_30_ids)

        self.assertIn("T45", u30_ids)
        self.assertNotIn("T15", u30_ids)
        self.assertNotIn("T5", u30_ids)

        self.assertEqual(analytics["unresolved_7_to_30_days_count"], 1)
        self.assertEqual(analytics["unresolved_over_30_days_count"], 1)

if __name__ == "__main__":
    unittest.main()

