import unittest
from datetime import datetime
from ticket_engine import TicketEngine, parse_ticket_document, extract_field_val, is_bbmp_ticket

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
                    "customer": {"stringValue": "Bangalore (BBMP)"}
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
                    "customer": {"stringValue": "Bangalore (BBMP)"}
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
                    "customer": {"stringValue": "Bangalore (BBMP)"}
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

    def test_filter_by_date(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        filtered_today = self.engine.filter_tickets(self.raw_tickets, target_date=today_str)
        self.assertEqual(len(filtered_today), 1)
        self.assertEqual(filtered_today[0]["ticket_id"], "TCK001")

        filtered_aug3 = self.engine.filter_tickets(self.raw_tickets, target_date="2026-08-03")
        self.assertEqual(len(filtered_aug3), 1)
        self.assertEqual(filtered_aug3[0]["ticket_id"], "TCK003")

    def test_analytics_calculation(self):
        analytics = self.engine.analyze_tickets(self.valid_bbmp_tickets)
        self.assertEqual(analytics["total_tickets"], 2)
        self.assertEqual(analytics["open_tickets"], 1)
        self.assertEqual(analytics["closed_tickets"], 1)
        self.assertAlmostEqual(analytics["resolution_rate_percent"], 50.0, places=2)

        # Verify today's metrics
        self.assertEqual(analytics["today_total_tickets"], 1)
        self.assertEqual(analytics["today_open_tickets"], 1)
        self.assertEqual(analytics["today_closed_tickets"], 0)

        # Verify SLC panel vs Lamps breakdown keys
        self.assertIn("open_slc_panels", analytics)
        self.assertIn("open_lamps", analytics)
        self.assertIn("today_open_slc_panels", analytics)
        self.assertIn("today_open_lamps", analytics)
        self.assertIn("july1_total_tickets", analytics)
        self.assertIn("july1_open_tickets", analytics)
        self.assertIn("july1_closed_tickets", analytics)
        self.assertIn("july1_resolution_rate_percent", analytics)

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

if __name__ == "__main__":
    unittest.main()
