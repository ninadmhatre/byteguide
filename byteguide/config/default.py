from pathlib import Path


def get():
    return dict(
        docfiles_dir=Path("/home/nmhatre/byte_guide_docs"),
        docfiles_link_root="/static/docfiles",
        copyright="",
        title="byteguide",
        welcome="Hello there!, \n - From byte/guide!",
        intro_line1="self host <i>your</i> code documentation easily!",
        intro_line2="</br><ul><li>Open Source</li><li>Free</li><li>Easy to Setup & Use</li><li>and <b>You</b> control hosting environment</li></ul>",
        footer="&copy; created with <strong><span>Byte/Guide</span></strong>!  All Rights Reserved",
        host="127.0.0.1",
        port=29000,
        debug=False,
        readonly=True,
        disable_delete=False,
        max_content_mb=10,
        enable_email_notification=False,
        smpt_server="",
        smpt_port=587,
        smpt_username="",
        smtp_password="",
    )
