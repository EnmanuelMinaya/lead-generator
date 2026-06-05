DOWNLOAD_TEMPLATE = """
File download record. User downloaded file "{filename}" ({mime_type}, {file_size_bytes} bytes)
from {download_url} on {start_timestamp}. File saved to: {target_path}.
Download initiated from page: {referrer_url}. Download state: {download_state}.
Browser risk classification: {danger_type}.
Browser: {browser}. User account: {os_user_account}.
""".strip()