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
OUTPUT_DIR = os.path.join(os.getcwd(), "test_output")
ARTIFACT_CASE_ID = "CASE-2024-001"
SOURCE_DB_PATH = "C:/Users/james.wright/AppData/Local/Google/Chrome/User Data/Default/History"
SOURCE_DB_HASH = "a3f1c2e4b5d6789012345678901234567890abcdef1234567890abcdef12345678"
OS_USER_ACCOUNT = "james.wright"
AUTOPSY_CASE_ID = ARTIFACT_CASE_ID


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

    # Morning cover traffic 08:30-10:00 (10)
    h("history_001", "https://nexacorp.internal/home", "NexaCorp Home", "2024-06-12T08:30:00Z", 2, "LINK")
    h("history_002", "https://nexacorp.internal/hr/benefits", "Benefits Portal", "2024-06-12T08:42:00Z", 1, "LINK")
    h("history_003", "https://news.bbc.co.uk/world", "BBC News - World", "2024-06-12T08:55:00Z", 1, "LINK")
    h("history_004", "https://www.bbc.com/news/business", "BBC News - Business", "2024-06-12T09:05:00Z", 1, "LINK")
    h("history_005", "https://www.linkedin.com/feed/", "LinkedIn Feed", "2024-06-12T09:18:00Z", 1, "LINK")
    h("history_006", "https://outlook.office.com/mail/inbox", "Outlook Mail", "2024-06-12T09:30:00Z", 1, "LINK")
    h("history_007", "https://nexacorp.internal/projects/alpha", "Alpha Project Dashboard", "2024-06-12T09:42:00Z", 1, "LINK")
    h("history_008", "https://www.cnn.com/2024/06/12/business/global-markets/index.html", "Global Markets | CNN", "2024-06-12T09:55:00Z", 1, "LINK")
    h("history_009", "https://www.google.com/search?q=project+timeline+management", "project timeline management - Google Search", "2024-06-12T09:58:00Z", 1, "LINK")
    h("history_010", "https://nexacorp.internal/dashboard", "NexaCorp Employee Dashboard", "2024-06-12T10:05:00Z", 1, "LINK")

    # Exfiltration research 10:15-11:45 (10)
    h("history_011", "https://www.duckduckgo.com/?q=best+secure+file+transfer", "best secure file transfer — DuckDuckGo", "2024-06-12T10:15:00Z", 1, "LINK")
    h("history_012", "https://www.cyberforum.com/threads/secure-file-transfer-tools.12345/", "Secure File Transfer Tools - CyberForum", "2024-06-12T10:24:00Z", 1, "LINK")
    h("history_013", "https://www.duckduckgo.com/?q=how+to+copy+files+to+cloud+undetected", "how to copy files to cloud undetected — DuckDuckGo", "2024-06-12T10:35:00Z", 1, "LINK")
    h("history_014", "https://privacy.stackexchange.com/questions/12345/how-to-send-large-files-anonymously", "How to send large files anonymously - Privacy.SE", "2024-06-12T10:45:00Z", 1, "LINK")
    h("history_015", "https://www.duckduckgo.com/?q=meganz+vs+dropbox+privacy", "meganz vs dropbox privacy — DuckDuckGo", "2024-06-12T10:52:00Z", 1, "LINK")
    h("history_016", "https://www.reddit.com/r/privacy/comments/abcd12/meganz_vs_dropbox_privacy/", "MegaNZ vs Dropbox Privacy - Reddit", "2024-06-12T10:58:00Z", 1, "LINK")
    h("history_017", "https://www.duckduckgo.com/?q=veracrypt+tutorial", "veracrypt tutorial — DuckDuckGo", "2024-06-12T11:10:00Z", 1, "LINK")
    h("history_018", "https://www.veracrypt.fr/en/Downloads.html", "VeraCrypt Downloads", "2024-06-12T11:18:00Z", 1, "LINK")
    h("history_019", "https://www.duckduckgo.com/?q=how+to+exfiltrate+data+from+corporate+network", "how to exfiltrate data from corporate network — DuckDuckGo", "2024-06-12T11:27:00Z", 1, "LINK")
    h("history_020", "https://www.sans.org/white-papers/how-to-transfer-files-securely/", "How to Transfer Files Securely - SANS", "2024-06-12T11:35:00Z", 1, "LINK")

    # Cloud storage and transfer 11:45-12:30 (8)
    h("history_021", "https://mega.nz/desktop", "MEGA Desktop Sync", "2024-06-12T11:45:00Z", 1, "TYPED")
    h("history_022", "https://www.wetransfer.com/", "WeTransfer - Send Large Files", "2024-06-12T11:52:00Z", 1, "LINK")
    h("history_023", "https://send.tresorit.com/", "Tresorit Send", "2024-06-12T11:59:00Z", 1, "LINK")
    h("history_024", "https://proton.me/drive", "Proton Drive", "2024-06-12T12:05:00Z", 1, "TYPED")
    h("history_025", "https://www.wetransfer.com/downloads", "WeTransfer Download", "2024-06-12T12:12:00Z", 1, "LINK")
    h("history_026", "https://www.google.com/search?q=mega+sync+client", "mega sync client - Google Search", "2024-06-12T12:18:00Z", 1, "LINK")
    h("history_027", "https://www.tresorit.com/", "Tresorit - Encrypted File Sharing", "2024-06-12T12:22:00Z", 1, "LINK")
    h("history_028", "https://drive.google.com/", "Google Drive", "2024-06-12T12:27:00Z", 1, "LINK")

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

    s("search_001", "how to transfer large files securely without it company knowing", "DuckDuckGo", "2024-06-12T10:15:00Z", "https://www.duckduckgo.com/?q=how+to+transfer+large+files+securely+without+it+company+knowing")
    s("search_002", "best cloud storage no logs", "DuckDuckGo", "2024-06-12T10:52:00Z", "https://www.duckduckgo.com/?q=best+cloud+storage+no+logs")
    s("search_003", "rclone tutorial sync to mega", "DuckDuckGo", "2024-06-12T11:00:00Z", "https://www.duckduckgo.com/?q=rclone+tutorial+sync+to+mega")
    s("search_004", "veracrypt hidden volume how to", "DuckDuckGo", "2024-06-12T11:10:00Z", "https://www.duckduckgo.com/?q=veracrypt+hidden+volume+how+to")
    s("search_005", "7zip encrypt archive password", "DuckDuckGo", "2024-06-12T11:20:00Z", "https://www.duckduckgo.com/?q=7zip+encrypt+archive+password")
    s("search_006", "nexacorp VPN logs monitored", "DuckDuckGo", "2024-06-12T11:35:00Z", "https://www.duckduckgo.com/?q=nexacorp+VPN+logs+monitored")
    s("search_007", "latest market news", "Google", "2024-06-12T08:55:00Z", "https://www.google.com/search?q=latest+market+news")
    s("search_008", "corporate wellness program", "Google", "2024-06-12T09:18:00Z", "https://www.google.com/search?q=corporate+wellness+program")
    s("search_009", "healthy lunch ideas", "Google", "2024-06-12T09:58:00Z", "https://www.google.com/search?q=healthy+lunch+ideas")
    s("search_010", "sports highlights", "Google", "2024-06-12T10:40:00Z", "https://www.google.com/search?q=sports+highlights")
    s("search_011", "news headlines today", "Google", "2024-06-12T12:10:00Z", "https://www.google.com/search?q=news+headlines+today")
    s("search_012", "rclone vs robocopy", "Google", "2024-06-12T12:18:00Z", "https://www.google.com/search?q=rclone+vs+robocopy")
    s("search_013", "secure file sharing tools", "Google", "2024-06-12T12:25:00Z", "https://www.google.com/search?q=secure+file+sharing+tools")
    s("search_014", "best tech podcasts", "Google", "2024-06-12T15:10:00Z", "https://www.google.com/search?q=best+tech+podcasts")
    s("search_015", "weather tomorrow", "Google", "2024-06-12T16:05:00Z", "https://www.google.com/search?q=weather+tomorrow")

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
        "https://nexacorp.internal/reports/Q2_financials.xlsx",
        "https://nexacorp.internal/reports/",
        "C:/Users/james.wright/Downloads/Q2_financials.xlsx",
        "Q2_financials.xlsx",
        2457600,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "2024-06-12T13:35:00Z",
        "2024-06-12T13:35:04Z",
        "complete",
        "safe",
    )
    d(
        "download_002",
        "https://www.7-zip.org/a/7z2301-x64.exe",
        "https://www.7-zip.org/download.html",
        "C:/Users/james.wright/Downloads/7z2301-x64.exe",
        "7z2301-x64.exe",
        1545728,
        "application/x-msdownload",
        "2024-06-12T13:48:00Z",
        "2024-06-12T13:48:22Z",
        "complete",
        "dangerous_file",
    )
    d(
        "download_003",
        "https://github.com/rclone/rclone/releases/download/v1.66.0/rclone-v1.66.0-windows-amd64.zip",
        "https://rclone.org/install/",
        "C:/Users/james.wright/Downloads/rclone-v1.66.0-windows-amd64.zip",
        "rclone-v1.66.0-windows-amd64.zip",
        46137344,
        "application/zip",
        "2024-06-12T14:05:00Z",
        "2024-06-12T14:06:10Z",
        "complete",
        "safe",
    )
    d(
        "download_004",
        "https://mega.nz/desktop/MEGAsyncSetup64.exe",
        "https://mega.nz/desktop",
        "C:/Users/james.wright/Downloads/MEGAsyncSetup64.exe",
        "MEGAsyncSetup64.exe",
        9175040,
        "application/x-msdownload",
        "2024-06-12T14:15:00Z",
        "2024-06-12T14:15:58Z",
        "complete",
        "dangerous_file",
    )
    d(
        "download_005",
        "https://veracrypt.fr/en/Downloads.html",
        "https://veracrypt.fr/en/Downloads.html",
        "C:/Users/james.wright/Downloads/VeraCrypt_Setup_x64_1.26.14.exe",
        "VeraCrypt_Setup_x64_1.26.14.exe",
        35127296,
        "application/x-msdownload",
        "2024-06-12T14:22:00Z",
        "2024-06-12T14:23:15Z",
        "complete",
        "dangerous_file",
    )
    d(
        "download_006",
        "https://nexacorp.internal/hr/employee_directory.csv",
        "https://nexacorp.internal/hr/",
        "C:/Users/james.wright/Downloads/employee_directory.csv",
        "employee_directory.csv",
        512000,
        "text/csv",
        "2024-06-12T14:35:00Z",
        "2024-06-12T14:35:02Z",
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

    b("bookmark_001", "https://mega.nz/", "MEGA Cloud Storage", "Bookmarks Bar > Personal", "2024-06-12T14:45:00Z")
    b("bookmark_002", "https://proton.me/mail", "Proton Mail", "Bookmarks Bar > Personal", "2024-06-12T15:10:00Z")
    b("bookmark_003", "https://rclone.org/", "Rclone — rsync for cloud storage", "Bookmarks Bar > Personal > Tools", "2024-06-12T14:50:00Z")
    b("bookmark_004", "https://www.veracrypt.fr/", "VeraCrypt - Free Open-Source Disk Encryption", "Bookmarks Bar > Personal > Tools", "2024-06-12T15:00:00Z")
    b("bookmark_005", "https://signal.org/", "Signal >> Home", "Bookmarks Bar > Personal > Comms", "2024-06-12T15:20:00Z")
    b("bookmark_006", "https://telegram.org/", "Telegram Web", "Bookmarks Bar > Personal > Comms", "2024-06-12T15:25:00Z")
    b("bookmark_007", "https://nexacorp.internal/employee-handbook", "Employee Handbook", "Bookmarks Bar > Work", "2024-06-12T08:40:00Z")
    b("bookmark_008", "https://nexacorp.internal/helpdesk", "NexaCorp Helpdesk", "Bookmarks Bar > Work", "2024-06-12T09:00:00Z")

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
        "scenario": "insider_threat_exfiltration",
        "case_id": ARTIFACT_CASE_ID,
        "os_user_account": OS_USER_ACCOUNT,
        "date": "2024-06-12",
        "expected_leads": [
            {
                "lead_id": "L001",
                "description": "Subject researched data exfiltration techniques",
                "supporting_artifact_types": ["search", "history"],
                "severity": "high",
            },
            {
                "lead_id": "L002",
                "description": "Subject downloaded file archiving and encryption tools",
                "supporting_artifact_types": ["download"],
                "severity": "high",
            },
            {
                "lead_id": "L003",
                "description": "Subject downloaded internal corporate files before exfiltration tools",
                "supporting_artifact_types": ["download", "history"],
                "severity": "high",
            },
            {
                "lead_id": "L004",
                "description": "Subject bookmarked cloud storage and encrypted communication services",
                "supporting_artifact_types": ["bookmark"],
                "severity": "medium",
            },
            {
                "lead_id": "L005",
                "description": "Suspicious gap in browser activity between 12:30 and 13:30",
                "supporting_artifact_types": [],
                "severity": "medium",
            },
            {
                "lead_id": "L006",
                "description": "Subject used DuckDuckGo for sensitive searches, Google for cover traffic",
                "supporting_artifact_types": ["search"],
                "severity": "medium",
            },
            {
                "lead_id": "L007",
                "description": "Subject directly typed URLs of cloud exfiltration services",
                "supporting_artifact_types": ["history"],
                "severity": "high",
            },
        ],
        "expected_timeline_start": "2024-06-12T08:30:00Z",
        "expected_timeline_end": "2024-06-12T17:00:00Z",
        "expected_gap_start": "2024-06-12T12:30:00Z",
        "expected_gap_end": "2024-06-12T13:30:00Z",
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
            "question": "What suspicious activity did this user carry out on 2024-06-12?",
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
            "question": "Construct a chronological timeline of the user's activity on 2024-06-12.",
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
        payload = {
            "question": q["question"],
            "autopsy_case_id": ARTIFACT_CASE_ID,
            "top_k": 15,
            "artifact_types": q["artifact_types"],
        }
        resp = requests.post(QUERY_URL, json=payload, timeout=120)
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
    write_output_file("ground_truth.json", ground_truth)

    print(f"Ingesting {len(all_records)} artifact records...")
    ingested_ids = ingest_records(all_records)
    write_output_file("ingested_ids.json", ingested_ids)

    print("Running evaluation queries...")
    query_results = run_queries()
    evaluation_data = {
        "case_id": ARTIFACT_CASE_ID,
        "queries": query_results,
    }
    write_output_file("evaluation_results.json", evaluation_data)

    total_leads = sum(item["leads_generated"] for item in query_results)
    total_hallucination_warnings = sum(len(item["hallucination_warnings"]) for item in query_results)

    print("\nSummary:")
    print(f"  Total artifacts ingested: {len(all_records)}")
    print("  Total queries run: 5")
    print(f"  Total leads generated: {total_leads}")
    print(f"  Total hallucination warnings: {total_hallucination_warnings}")
    print(f"  Output written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
