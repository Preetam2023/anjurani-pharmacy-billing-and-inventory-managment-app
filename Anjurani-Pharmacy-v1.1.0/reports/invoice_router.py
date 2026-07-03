from logic.app_settings import get_invoice_layout

from reports.invoice_pdf import generate_invoice_pdf

try:
    from reports.invoice_preprinted import generate_invoice_preprinted
except ImportError:
    generate_invoice_preprinted = None


def generate_invoice(*args, **kwargs):

    layout = get_invoice_layout()

    if (
        layout == "preprinted"
        and generate_invoice_preprinted is not None
    ):
        return generate_invoice_preprinted(
            *args,
            **kwargs,
        )

    return generate_invoice_pdf(
        *args,
        **kwargs,
    )