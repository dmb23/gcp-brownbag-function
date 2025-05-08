from pathlib import Path
from tempfile import NamedTemporaryFile

import functions_framework
from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright


@functions_framework.cloud_event
def post_report_to_slack(cloud_event):
    # check that the file created in the cloud event follows *markdown_report*md

    # Convert the markdown file to a PDF file according to the script below, save it as temporary

    # Use the slack API to upload the file to the correct channel. get the slack API key and the channel_id from environment variables.
    pass


if __name__ == "__main__":
    report_file = Path(
        "../gcp-brownbag-agents/markdown_report_Alignment__2025-05-07 11:29:07.939597.md"
    )
    md_report = report_file.read_text()
    print("********************")
    print(md_report)

    md = MarkdownIt()
    for token in md.parse(md_report):
        print(token)
    title = "SomeTitle"
    html_report = md.render(md_report)
    print("********************")
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
    print(html_report)

    output_path = Path("./test_output.pdf")

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

    if False:
        with NamedTemporaryFile("w") as temp_html:
            temp_html.write(html_report)
            print("********************")
            print(temp_html.name)
            print(Path(temp_html.name).read_text()[:100])
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(f"file:///{temp_html.name}")
                page.pdf(path=output_path)
                browser.close()
