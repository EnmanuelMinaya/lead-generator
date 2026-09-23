import json
import os
import sys
import time
from datetime import datetime

import requests

SERVER_URL = "http://localhost:8000"
HEALTH_URL = f"{SERVER_URL}/health"
INGEST_URL = f"{SERVER_URL}/ingest"
QUERY_URL = f"{SERVER_URL}/query"
OUTPUT_DIR = os.path.join(os.getcwd(), "test_output_fraud")
USE_DECOMPOSITION = True
TOP_K = 15
CASE_ID = "CASE-2024-002"
SOURCE_DB_PATH = "C:/Users/sarah.chen/AppData/Local/Google/Chrome/User Data/Default/History"
SOURCE_DB_HASH = "b7e2d4f1a3c5908712345678901234567890abcdef1234567890abcdef98765432"
OS_USER_ACCOUNT = "sarah.chen"
AUTOPSY_CASE_ID = CASE_ID


def ensure_output_dir():
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)


def check_server():
    try:
        resp = requests.get(HEALTH_URL, timeout=5)
    except Exception as exc:
        print(f"ERROR: Server not reachable at {HEALTH_URL}: {exc}")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"ERROR: Health check failed with status {resp.status_code}: {resp.text}")
        sys.exit(1)

    data = resp.json()
    if data.get("status") != "ok":
        print(f"ERROR: Health check returned unexpected payload: {data}")
        sys.exit(1)

    print(f"Server healthy: collection_count={data.get('collection_count')}")


def build_history_records():
    records = []

    def h(label, url, title, timestamp, visit_count, transition, artifact_label=None):
        rec = {
            "artifact_type": "history",
            "browser": "chrome",
            "browser_profile": "Default",
            "source_db_path": SOURCE_DB_PATH,
            "source_db_hash": SOURCE_DB_HASH,
            "os_user_account": OS_USER_ACCOUNT,
            "autopsy_case_id": AUTOPSY_CASE_ID,
            "url": url,
            "page_title": title,
            "visit_timestamp": timestamp,
            "visit_count": visit_count,
            "transition_type": transition,
        }
        records.append((label, rec))

    # Morning cover traffic 08:30-10:00 (10 records)
    h("history_001", "https://bank.internal/dashboard", "Bank Internal Dashboard", "2024-09-03T08:30:00Z", 2, "LINK")
    h("history_002", "https://bank.internal/accounts", "Accounts Overview", "2024-09-03T08:42:00Z", 1, "LINK")
    h("history_003", "https://bank.internal/reports", "Quarterly Reports", "2024-09-03T08:55:00Z", 1, "LINK")
    h("history_004", "https://www.reuters.com/markets", "Reuters Markets", "2024-09-03T09:05:00Z", 1, "LINK")
    h("history_005", "https://www.linkedin.com/feed/", "LinkedIn Feed", "2024-09-03T09:18:00Z", 1, "LINK")
    h("history_006", "https://outlook.office365.com/mail/inbox", "Outlook Mail", "2024-09-03T09:30:00Z", 1, "LINK")
    h("history_007", "https://bank.internal/reports/transactions", "Transaction Reports", "2024-09-03T09:42:00Z", 1, "LINK")
    h("history_008", "https://www.bbc.com/news/business", "BBC Business News", "2024-09-03T09:55:00Z", 1, "LINK")
    h("history_009", "https://www.google.com/search?q=bank+reconciliation+best+practices", "bank reconciliation best practices - Google Search", "2024-09-03T09:58:00Z", 1, "LINK")
    h("history_010", "https://bank.internal/dashboard/ops", "Operations Dashboard", "2024-09-03T10:00:00Z", 1, "LINK")

    # Identity fraud research 10:10-11:45 (10 records)
    h("history_011", "https://www.duckduckgo.com/?q=how+to+use+stolen+credit+card+without+getting+caught", "how to use stolen credit card without getting caught — DuckDuckGo", "2024-09-03T10:10:00Z", 1, "TYPED")
    h("history_012", "https://www.reddit.com/r/fraud/comments/abc123/credit_card_fraud_tips", "Credit card fraud tips - Reddit", "2024-09-03T10:22:00Z", 1, "LINK")
    h("history_013", "https://www.darkweblinks.info/carding-guide", "Carding Guide", "2024-09-03T10:35:00Z", 1, "TYPED")
    h("history_014", "https://www.identitytheft.org/resources", "Identity Theft Resources", "2024-09-03T10:48:00Z", 1, "LINK")
    h("history_015", "https://pastebin.com/abc123def456", "Pastebin dump — fullz", "2024-09-03T10:58:00Z", 1, "TYPED")
    h("history_016", "https://pastebin-like.net/fullz/cvv-shop", "fullz cvv shop", "2024-09-03T11:05:00Z", 1, "LINK")
    h("history_017", "https://www.duckduckgo.com/?q=how+to+convert+fullz+to+cash", "how to convert fullz to cash — DuckDuckGo", "2024-09-03T11:15:00Z", 1, "LINK")
    h("history_018", "https://www.duckduckgo.com/?q=how+to+open+bank+account+with+fake+identity", "how to open bank account with fake identity — DuckDuckGo", "2024-09-03T11:25:00Z", 1, "TYPED")
    h("history_019", "https://www.duckduckgo.com/?q=how+to+launder+money+through+crypto", "how to launder money through crypto — DuckDuckGo", "2024-09-03T11:36:00Z", 1, "LINK")
    h("history_020", "https://www.security.stackexchange.com/questions/12345/credit-card-fraud", "Security.SE — credit card fraud", "2024-09-03T11:45:00Z", 1, "LINK")

    # Cryptocurrency and anonymisation 11:45-12:30 (8 records)
    h("history_021", "https://www.localbitcoins.com/", "LocalBitcoins", "2024-09-03T11:50:00Z", 1, "TYPED")
    h("history_022", "https://bisq.network/", "Bisq", "2024-09-03T11:58:00Z", 1, "LINK")
    h("history_023", "https://www.tornado.cash/", "Tornado Cash", "2024-09-03T12:02:00Z", 1, "TYPED")
    h("history_024", "https://www.monero.org/", "Monero", "2024-09-03T12:08:00Z", 1, "LINK")
    h("history_025", "https://www.cryptolaundry.net/", "Crypto Laundry", "2024-09-03T12:14:00Z", 1, "LINK")
    h("history_026", "https://www.duckduckgo.com/?q=best+bitcoin+mixer+no+kyc+2024", "best bitcoin mixer no kyc 2024 — DuckDuckGo", "2024-09-03T12:20:00Z", 1, "TYPED")
    h("history_027", "https://www.duckduckgo.com/?q=monero+vs+bitcoin+anonymity", "monero vs bitcoin anonymity — DuckDuckGo", "2024-09-03T12:25:00Z", 1, "LINK")
    h("history_028", "https://www.duckduckgo.com/?q=tor+browser+dark+web+markets", "tor browser dark web markets — DuckDuckGo", "2024-09-03T12:30:00Z", 1, "LINK")

    # Gap 12:30-13:30 intentionally absent

    # Post-lunch cover traffic / benign browsing to reach 40 history rows (6 records)
    h("history_029", "https://bank.internal/exports/customer_accounts_Q3.xlsx", "Customer Account Export", "2024-09-03T13:35:00Z", 1, "LINK")
    h("history_030", "https://www.python.org/downloads/", "Python Downloads", "2024-09-03T13:48:00Z", 1, "LINK")
    h("history_031", "https://pandas.pydata.org/docs/", "Pandas Documentation", "2024-09-03T14:00:00Z", 1, "LINK")
    h("history_032", "https://www.torproject.org/download/", "Tor Browser Downloads", "2024-09-03T14:05:00Z", 1, "LINK")
    h("history_033", "https://keepass.info/download.html", "KeePass Downloads", "2024-09-03T14:15:00Z", 1, "LINK")
    h("history_034", "https://protonvpn.com/download", "ProtonVPN Downloads", "2024-09-03T14:22:00Z", 1, "LINK")

    # Late afternoon cover traffic (6 records)
    h("history_035", "https://bank.internal/dashboard", "Bank Dashboard", "2024-09-03T15:00:00Z", 1, "LINK")
    h("history_036", "https://www.reuters.com/world", "Reuters World", "2024-09-03T15:20:00Z", 1, "LINK")
    h("history_037", "https://www.linkedin.com/jobs/", "LinkedIn Jobs", "2024-09-03T15:45:00Z", 1, "LINK")
    h("history_038", "https://outlook.office365.com/calendar", "Outlook Calendar", "2024-09-03T16:00:00Z", 1, "LINK")
    h("history_039", "https://www.google.com/search?q=weekend+weather+forecast", "weekend weather forecast - Google Search", "2024-09-03T16:20:00Z", 1, "LINK")
    h("history_040", "https://www.google.com/search?q=premier+league+results", "premier league results - Google Search", "2024-09-03T16:50:00Z", 1, "LINK")

    return records


def build_search_records():
    records = []

    def s(label, term, engine, timestamp, result_url=None):
        rec = {
            "artifact_type": "search",
            "browser": "chrome",
            "browser_profile": "Default",
            "source_db_path": SOURCE_DB_PATH,
            "source_db_hash": SOURCE_DB_HASH,
            "os_user_account": OS_USER_ACCOUNT,
            "autopsy_case_id": AUTOPSY_CASE_ID,
            "search_term": term,
            "search_engine": engine,
            "search_timestamp": timestamp,
            "result_url": result_url,
        }
        records.append((label, rec))

    s("search_001", "how to use stolen credit card without getting caught", "DuckDuckGo", "2024-09-03T10:10:00Z", "https://www.duckduckgo.com/?q=how+to+use+stolen+credit+card+without+getting+caught")
    s("search_002", "best bitcoin mixer no kyc 2024", "DuckDuckGo", "2024-09-03T11:50:00Z", "https://www.duckduckgo.com/?q=best+bitcoin+mixer+no+kyc+2024")
    s("search_003", "how to launder money through crypto", "DuckDuckGo", "2024-09-03T11:36:00Z", "https://www.duckduckgo.com/?q=how+to+launder+money+through+crypto")
    s("search_004", "monero vs bitcoin anonymity", "DuckDuckGo", "2024-09-03T12:25:00Z", "https://www.duckduckgo.com/?q=monero+vs+bitcoin+anonymity")
    s("search_005", "how to convert fullz to cash", "DuckDuckGo", "2024-09-03T11:15:00Z", "https://www.duckduckgo.com/?q=how+to+convert+fullz+to+cash")
    s("search_006", "tor browser dark web markets", "DuckDuckGo", "2024-09-03T12:30:00Z", "https://www.duckduckgo.com/?q=tor+browser+dark+web+markets")
    s("search_007", "how to open bank account with fake identity", "DuckDuckGo", "2024-09-03T11:25:00Z", "https://www.duckduckgo.com/?q=how+to+open+bank+account+with+fake+identity")
    s("search_008", "bank reconciliation best practices", "Google", "2024-09-03T08:58:00Z", "https://www.google.com/search?q=bank+reconciliation+best+practices")
    s("search_009", "Q3 financial reporting deadlines", "Google", "2024-09-03T09:12:00Z", "https://www.google.com/search?q=Q3+financial+reporting+deadlines")
    s("search_010", "excel pivot table tutorial", "Google", "2024-09-03T09:40:00Z", "https://www.google.com/search?q=excel+pivot+table+tutorial")
    s("search_011", "restaurants near me", "Google", "2024-09-03T10:05:00Z", "https://www.google.com/search?q=restaurants+near+me")
    s("search_012", "weekend weather forecast", "Google", "2024-09-03T16:20:00Z", "https://www.google.com/search?q=weekend+weather+forecast")
    s("search_013", "premier league results", "Google", "2024-09-03T16:50:00Z", "https://www.google.com/search?q=premier+league+results")
    s("search_014", "python pandas dataframe tutorial", "Google", "2024-09-03T13:50:00Z", "https://www.google.com/search?q=python+pandas+dataframe+tutorial")
    s("search_015", "best coffee shops london", "Google", "2024-09-03T15:30:00Z", "https://www.google.com/search?q=best+coffee+shops+london")

    return records


def build_download_records():
    records = []

    def d(label, download_url, referrer_url, target_path, filename, file_size_bytes, mime_type, start_timestamp, end_timestamp, download_state, danger_type):
        rec = {
            "artifact_type": "download",
            "browser": "chrome",
            "browser_profile": "Default",
            "source_db_path": SOURCE_DB_PATH,
            "source_db_hash": SOURCE_DB_HASH,
            "os_user_account": OS_USER_ACCOUNT,
            "autopsy_case_id": AUTOPSY_CASE_ID,
            "download_url": download_url,
            "referrer_url": referrer_url,
            "target_path": target_path,
            "filename": filename,
            "file_size_bytes": file_size_bytes,
            "mime_type": mime_type,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "download_state": download_state,
            "danger_type": danger_type,
        }
        records.append((label, rec))

    d(
        "download_001",
        "https://bank.internal/exports/customer_accounts_Q3.xlsx",
        "https://bank.internal/reports/",
        "C:/Users/sarah.chen/Downloads/customer_accounts_Q3.xlsx",
        "customer_accounts_Q3.xlsx",
        5242880,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "2024-09-03T13:35:00Z",
        "2024-09-03T13:35:08Z",
        "complete",
        "safe",
    )
    d(
        "download_002",
        "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe",
        "https://www.python.org/downloads/",
        "C:/Users/sarah.chen/Downloads/python-3.12.0-amd64.exe",
        "python-3.12.0-amd64.exe",
        25165824,
        "application/x-msdownload",
        "2024-09-03T13:48:00Z",
        "2024-09-03T13:49:15Z",
        "complete",
        "dangerous_file",
    )
    d(
        "download_003",
        "https://www.torproject.org/dist/torbrowser/13.0/tor-browser-windows-x86_64-portable-13.0.exe",
        "https://www.torproject.org/download/",
        "C:/Users/sarah.chen/Downloads/tor-browser-windows-x86_64-portable-13.0.exe",
        "tor-browser-windows-x86_64-portable-13.0.exe",
        85983232,
        "application/x-msdownload",
        "2024-09-03T14:05:00Z",
        "2024-09-03T14:07:22Z",
        "complete",
        "dangerous_file",
    )
    d(
        "download_004",
        "https://keepass.info/download/p_win64/KeePass-2.56-Setup.exe",
        "https://keepass.info/download.html",
        "C:/Users/sarah.chen/Downloads/KeePass-2.56-Setup.exe",
        "KeePass-2.56-Setup.exe",
        3932160,
        "application/x-msdownload",
        "2024-09-03T14:15:00Z",
        "2024-09-03T14:15:44Z",
        "complete",
        "safe",
    )
    d(
        "download_005",
        "https://protonvpn.com/download/ProtonVPN_win_v3.2.2.exe",
        "https://protonvpn.com/download",
        "C:/Users/sarah.chen/Downloads/ProtonVPN_win_v3.2.2.exe",
        "ProtonVPN_win_v3.2.2.exe",
        67108864,
        "application/x-msdownload",
        "2024-09-03T14:22:00Z",
        "2024-09-03T14:23:50Z",
        "complete",
        "safe",
    )
    d(
        "download_006",
        "https://bank.internal/exports/transaction_log_aug2024.csv",
        "https://bank.internal/reports/transactions/",
        "C:/Users/sarah.chen/Downloads/transaction_log_aug2024.csv",
        "transaction_log_aug2024.csv",
        1048576,
        "text/csv",
        "2024-09-03T14:35:00Z",
        "2024-09-03T14:35:03Z",
        "complete",
        "safe",
    )

    return records


def build_bookmark_records():
    records = []

    def b(label, url, title, folder_path, date_added, date_last_used=None):
        rec = {
            "artifact_type": "bookmark",
            "browser": "chrome",
            "browser_profile": "Default",
            "source_db_path": SOURCE_DB_PATH,
            "source_db_hash": SOURCE_DB_HASH,
            "os_user_account": OS_USER_ACCOUNT,
            "autopsy_case_id": AUTOPSY_CASE_ID,
            "url": url,
            "bookmark_title": title,
            "folder_path": folder_path,
            "date_added": date_added,
            "date_last_used": date_last_used,
        }
        records.append((label, rec))

    b("bookmark_001", "https://localbitcoins.com/", "LocalBitcoins — Buy Bitcoin", "Bookmarks Bar > Personal > Crypto", "2024-09-03T14:45:00Z")
    b("bookmark_002", "https://bisq.network/", "Bisq — Decentralised Bitcoin Exchange", "Bookmarks Bar > Personal > Crypto", "2024-09-03T14:50:00Z")
    b("bookmark_003", "https://www.torproject.org/", "Tor Project | Anonymity Online", "Bookmarks Bar > Personal > Tools", "2024-09-03T15:05:00Z")
    b("bookmark_004", "https://protonmail.com/", "Proton Mail — Encrypted Email", "Bookmarks Bar > Personal > Tools", "2024-09-03T15:10:00Z")
    b("bookmark_005", "https://www.monero.org/", "Monero — Private Digital Currency", "Bookmarks Bar > Personal > Research", "2024-09-03T15:20:00Z")
    b("bookmark_006", "https://coinmixers.io/", "CoinMixers — Anonymous Bitcoin", "Bookmarks Bar > Personal > Research", "2024-09-03T15:25:00Z")
    b("bookmark_007", "https://bank.internal/employee-handbook", "Employee Handbook", "Bookmarks Bar > Work", "2024-09-03T08:40:00Z")
    b("bookmark_008", "https://bank.internal/helpdesk", "Bank Helpdesk", "Bookmarks Bar > Work", "2024-09-03T09:00:00Z")

    return records


def build_all_records():
    records = []
    records.extend(build_history_records())
    records.extend(build_search_records())
    records.extend(build_download_records())
    records.extend(build_bookmark_records())
    return records


def build_ground_truth():
    return {
        "scenario": "financial_fraud_identity_theft",
        "case_id": CASE_ID,
        "os_user_account": OS_USER_ACCOUNT,
        "date": "2024-09-03",
        "expected_leads": [
            {
                "lead_id": "L001",
                "description": "Subject researched identity theft and credit card fraud techniques",
                "supporting_artifact_types": ["search", "history"],
                "severity": "high",
            },
            {
                "lead_id": "L002",
                "description": "Subject researched cryptocurrency mixing and money laundering methods",
                "supporting_artifact_types": ["search", "history"],
                "severity": "high",
            },
            {
                "lead_id": "L003",
                "description": "Subject downloaded Tor Browser — anonymisation tool",
                "supporting_artifact_types": ["download"],
                "severity": "high",
            },
            {
                "lead_id": "L004",
                "description": "Subject downloaded internal bank customer account data and transaction logs",
                "supporting_artifact_types": ["download"],
                "severity": "high",
            },
            {
                "lead_id": "L005",
                "description": "Subject bookmarked cryptocurrency exchanges and anonymous communication tools",
                "supporting_artifact_types": ["bookmark"],
                "severity": "medium",
            },
            {
                "lead_id": "L006",
                "description": "Suspicious gap in browser activity between 12:30 and 13:30",
                "supporting_artifact_types": [],
                "severity": "medium",
            },
            {
                "lead_id": "L007",
                "description": "Subject used DuckDuckGo for all fraud and crypto searches, Google for cover traffic",
                "supporting_artifact_types": ["search"],
                "severity": "medium",
            },
        ],
        "expected_timeline_start": "2024-09-03T08:30:00Z",
        "expected_timeline_end": "2024-09-03T17:00:00Z",
        "expected_gap_start": "2024-09-03T12:30:00Z",
        "expected_gap_end": "2024-09-03T13:30:00Z",
    }


def ingest_records(records):
    ingested_ids = {}
    for label, record in records:
        response = requests.post(INGEST_URL, json=record, timeout=10)
        status = response.status_code
        if response.ok:
            artifact_id = response.json().get("artifact_id")
            ingested_ids[label] = artifact_id
            print(f"ingest {record['artifact_type']} {label} -> {artifact_id} status {status}")
        else:
            print(f"ERROR ingest {record['artifact_type']} {label} status {status}: {response.text}")
            sys.exit(1)
        time.sleep(0.1)
    return ingested_ids


def run_queries():
    queries = [
        {
            "query_id": "Q001",
            "question": "What suspicious activity did this user carry out on 2024-09-03?",
            "artifact_types": None,
        },
        {
            "query_id": "Q002",
            "question": "Did the user show intent to exfiltrate data? What evidence supports this?",
            "artifact_types": ["search", "history"],
        },
        {
            "query_id": "Q003",
            "question": "What files did the user download and are any of them suspicious?",
            "artifact_types": ["download"],
        },
        {
            "query_id": "Q004",
            "question": "Construct a chronological timeline of the user's activity on 2024-09-03.",
            "artifact_types": None,
        },
        {
            "query_id": "Q005",
            "question": "Are there any unusual gaps or anomalies in the user's browser activity?",
            "artifact_types": None,
        },
    ]

    results = []
    for q in queries:
        print(f"Running query {q['query_id']}: {q['question']}")
        payload = {
            "question": q["question"],
            "autopsy_case_id": CASE_ID,
            "top_k": TOP_K,
            "artifact_types": q["artifact_types"],
            "use_decomposition": USE_DECOMPOSITION,
        }
        resp = requests.post(QUERY_URL, json=payload, timeout=600)
        if not resp.ok:
            print(f"ERROR query {q['query_id']} status {resp.status_code}: {resp.text}")
            sys.exit(1)
        data = resp.json()
        results.append(
            {
                "query_id": q["query_id"],
                "question": q["question"],
                "artifacts_retrieved": data.get("artifacts_retrieved", 0),
                "leads_generated": len(data.get("leads", [])),
                "hallucination_warnings": data.get("hallucination_warnings", []),
                "raw_response": data,
            }
        )
    return results


def write_output_file(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def main():
    ensure_output_dir()
    check_server()

    all_records = build_all_records()
    ground_truth = build_ground_truth()

    print("Writing ground truth...")
    write_output_file("ground_truth_fraud.json", ground_truth)

    print(f"Ingesting {len(all_records)} artifact records...")
    ingested_ids = ingest_records(all_records)
    write_output_file("ingested_ids_fraud.json", ingested_ids)

    print("Running evaluation queries...")
    query_results = run_queries()
    evaluation_data = {
        "case_id": CASE_ID,
        "queries": query_results,
    }
    write_output_file("evaluation_results_fraud.json", evaluation_data)

    total_leads = sum(item["leads_generated"] for item in query_results)
    total_hallucination_warnings = sum(len(item["hallucination_warnings"]) for item in query_results)

    print("\nSummary:")
    print(f"  Scenario: Financial Fraud")
    print(f"  Case ID: {CASE_ID}")
    print(f"  User: {OS_USER_ACCOUNT}")
    print(f"  Total artifacts ingested: {len(all_records)}")
    print("  Total queries run: 5")
    print(f"  Use decomposition: {USE_DECOMPOSITION}")
    print(f"  Top k: {TOP_K}")
    print(f"  Total leads generated: {total_leads}")
    print(f"  Total hallucination warnings: {total_hallucination_warnings}")
    print(f"  Output written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
