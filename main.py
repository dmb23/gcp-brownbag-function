from pathlib import Path

import functions_framework
from cloudevents.http.event import CloudEvent


@functions_framework.cloud_event
def post_report_to_slack(cloud_event: CloudEvent) -> None:
    # Extract file information from the cloud event
    file_path = cloud_event.data["name"]
    bucket = cloud_event.data["bucket"]

    # Check that the file created in the cloud event follows *markdown_report*md pattern
    if "markdown_report" not in Path(file_path).name or not file_path.endswith(".md"):
        print(f"Ignoring file {file_path} as it doesn't match the expected pattern")
        return

    # imports only after check if the function should be run
    import os

    from google.cloud import storage
    from markdown_it import MarkdownIt
    from playwright.sync_api import sync_playwright
    from slack_sdk import WebClient

    # Download the file from the bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)
    blob = bucket.blob(file_path)

    # Create a temporary file to store the markdown content
    temp_md_file = Path("./tmp_report.md")
    blob.download_to_filename(temp_md_file)
    md_report = temp_md_file.read_text()

    # Parse the markdown to extract the title
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
        print("Unexpected first few tokens to infer the title:")
        for token in tokens[:3]:
            print(token.type, token.tag, token.content)
        title = "Grimaud Tech Report"

    # Convert markdown to HTML
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

    # Create temporary files for HTML and PDF
    temp_html = Path("./report.html")
    temp_html.write_text(html_report)
    output_path = Path(f"./{Path(file_path).stem}.pdf")

    # Convert HTML to PDF using Playwright
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

    # Upload the PDF back to the same bucket
    pdf_blob = bucket.blob(f"{Path(file_path).stem}.pdf")
    pdf_blob.upload_from_filename(output_path)

    # Post the PDF to Slack
    try:
        client = WebClient(os.environ["SLACK_BOT_TOKEN"])
    except KeyError:
        print(
            "Please specify the SLACK_BOT_TOKEN environment variable to post to Slack!"
        )
        return

    try:
        client.files_upload_v2(
            title=title,
            file=output_path,
            initial_comment=f"New report: {title}",
            channel=os.environ["SLACK_CHANNEL_ID"],
        )
    except KeyError:
        print(
            "Please specify the SLACK_CHANNEL_ID environment variable to publish the report in a channel!"
        )
        return

    print(f"Successfully processed {file_path} and posted to Slack")
    return


# if __name__ == "__main__":
#     report_file = Path(
#         "../gcp-brownbag-agents/markdown_report_Alignment__2025-05-07 11:29:07.939597.md"
#     )
#     md_report = report_file.read_text()
#
#     md = MarkdownIt()
#     tokens = md.parse(md_report)
#     if (
#         tokens[0].type == "heading_open"
#         and tokens[0].tag == "h1"
#         and tokens[2].type == "heading_close"
#         and tokens[2].tag == "h1"
#     ):
#         title = tokens[1].content
#     else:
#         print("Unexpected first few tokens:")
#         for token in tokens[:3]:
#             print(token.type, token.tag, token.content)
#         title = "Grimaud Tech Report"
#
#     html_report = md.render(md_report)
#     html_preface = f"""
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>{title}</title>
#     <style>
#         body {{ font-family: Arial, sans-serif; padding: 20px; }}
#         img {{
#           max-width: 100%;
#           height: auto;
#         }}
#     </style>
# </head>
# <body>
# <div>
#         """
#     html_closing = """
# </div>
# </body>
# </html>
#     """
#     html_report = html_preface + html_report + html_closing
#
#     output_path = Path(f"./{report_file.stem}.pdf")
#
#     temp_html = Path("./test_output.html")
#     temp_html.write_text(html_report)
#     with sync_playwright() as p:
#         browser = p.chromium.launch()
#         page = browser.new_page()
#         page.goto(f"file:///{temp_html.resolve()}")
#         page.pdf(
#             path=output_path,
#             format="A4",
#             margin={"top": "3cm", "bottom": "2cm", "left": "2cm", "right": "2cm"},
#         )
#         browser.close()
#
#     # do the Slack thing
#     load_dotenv()
#     client = WebClient(os.getenv("SLACK_BOT_TOKEN"))
#     new_slack_file = client.files_upload_v2(
#         title=title,
#         file=output_path,
#         initial_comment="This is a test report upload",
#         channel=os.getenv("SLACK_CHANNEL_ID"),
#     )
