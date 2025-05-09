import os
from pathlib import Path

import functions_framework
from dotenv import load_dotenv
from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright
from slack_sdk import WebClient


@functions_framework.cloud_event
def post_report_to_slack(cloud_event):
    # check that the file created in the cloud event follows *markdown_report*md

    # Convert the markdown file to a PDF file according to the script below, save it in the same bucket as the original file

    # Use the slack API to upload the file to the correct channel. get the slack API key and the channel_id from environment variables.
    pass


if __name__ == "__main__":
    report_file = Path(
        "../gcp-brownbag-agents/markdown_report_Alignment__2025-05-07 11:29:07.939597.md"
    )
    md_report = report_file.read_text()

    md = MarkdownIt()
    tokens = md.parse(md_report)
    if (
        tokens[0].type == "heading_open"
        and tokens[0].tag == "h1"
        and tokens[2].type == "heading_close"
        and tokens[2].tag == "h1"
    ):
        title = tokens[1].content
    else:
        print("Unexpected first few tokens:")
        for token in tokens[:3]:
            print(token.type, token.tag, token.content)
        title = "Grimaud Tech Report"

    html_report = md.render(md_report)
    html_preface = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        img {{
          max-width: 100%;
          height: auto;
        }}
    </style>
</head>
<body>
<div>
        """
    html_closing = """
</div>
</body>
</html>
    """
    html_report = html_preface + html_report + html_closing

    output_path = Path(f"./{report_file.stem}.pdf")

    temp_html = Path("./test_output.html")
    temp_html.write_text(html_report)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{temp_html.resolve()}")
        page.pdf(
            path=output_path,
            format="A4",
            margin={"top": "3cm", "bottom": "2cm", "left": "2cm", "right": "2cm"},
        )
        browser.close()

    # do the Slack thing
    load_dotenv()
    client = WebClient(os.getenv("SLACK_BOT_TOKEN"))
    new_slack_file = client.files_upload_v2(
        title=title,
        file=output_path,
        initial_comment="This is a test report upload",
        channel=os.getenv("SLACK_CHANNEL_ID"),
    )
