"""
Generate a synthetic contract PDF for smoke-testing the eval pipeline.

Usage
-----
    python scripts/make_sample_pdf.py

Output: scripts/sample_contract.pdf  (~6 pages, all six clause types)

Requires: fpdf2  (included in server/requirements.txt)
"""
from __future__ import annotations

from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    raise SystemExit(
        "fpdf2 is required. Install it with:\n"
        "  pip install fpdf2"
    )

CLAUSES: list[dict] = [
    {
        "heading": "1. DEFINITIONS",
        "type": "other",
        "body": (
            "1.1 \"Agreement\" means this Software Services Agreement, including all "
            "exhibits and schedules attached hereto.\n\n"
            "1.2 \"Services\" means the software development, maintenance, and support "
            "services described in Exhibit A.\n\n"
            "1.3 \"Deliverables\" means all work product, software, documentation, and "
            "other materials produced by Provider in the course of performing the Services.\n\n"
            "1.4 \"Intellectual Property Rights\" means all patents, copyrights, trademarks, "
            "trade secrets, and other proprietary rights recognized in any jurisdiction.\n\n"
            "1.5 \"Confidential Information\" has the meaning given in Section 6 of this Agreement."
        ),
    },
    {
        "heading": "2. PAYMENT TERMS",
        "type": "payment",
        "body": (
            "2.1 Fees. Client shall pay Provider the fees set forth in Exhibit B (\"Fees\"). "
            "All Fees are denominated in United States dollars and are exclusive of applicable taxes.\n\n"
            "2.2 Invoicing. Provider shall issue invoices on a monthly basis no later than the "
            "fifth (5th) business day of each calendar month for Services rendered in the prior month.\n\n"
            "2.3 Payment Due Date. Client shall remit payment within thirty (30) days of the "
            "invoice date (\"Net 30\"). Payments not received within thirty (30) days shall be "
            "considered overdue.\n\n"
            "2.4 Late Payment. Overdue invoices shall accrue interest at the rate of one and "
            "one-half percent (1.5%) per month, or the maximum rate permitted by applicable law, "
            "whichever is lower. Provider reserves the right to suspend Services until all "
            "overdue amounts, including accrued interest, are paid in full.\n\n"
            "2.5 Disputed Invoices. If Client disputes any portion of an invoice, Client shall "
            "notify Provider in writing within ten (10) days of receipt, specifying the disputed "
            "amount and the basis for the dispute. The undisputed portion of the invoice shall "
            "remain due and payable on the original due date."
        ),
    },
    {
        "heading": "3. CONFIDENTIALITY",
        "type": "confidentiality",
        "body": (
            "3.1 Confidential Information. Each party (\"Receiving Party\") acknowledges that it "
            "may receive or have access to information of the other party (\"Disclosing Party\") "
            "that is proprietary information, trade secrets, or otherwise confidential, including "
            "but not limited to business plans, customer lists, financial information, technical "
            "specifications, source code, and pricing information (collectively, \"Confidential "
            "Information\").\n\n"
            "3.2 Non-Disclosure Obligations. The Receiving Party shall: (a) hold all Confidential "
            "Information in strict confidence using at least the same degree of care it uses to "
            "protect its own confidential information, but in no event less than reasonable care; "
            "(b) not disclose Confidential Information to any third party without the prior written "
            "consent of the Disclosing Party; (c) use Confidential Information solely for the "
            "purposes of performing its obligations or exercising its rights under this Agreement.\n\n"
            "3.3 Exceptions. The obligations of confidentiality shall not apply to information "
            "that: (a) is or becomes publicly available through no breach of this Agreement; "
            "(b) was rightfully known to the Receiving Party prior to disclosure; or (c) is "
            "independently developed by the Receiving Party without use of the Confidential Information."
        ),
    },
    {
        "heading": "4. INDEMNIFICATION",
        "type": "indemnification",
        "body": (
            "4.1 Indemnification by Provider. Provider shall indemnify, defend, and hold harmless "
            "Client and its officers, directors, employees, agents, successors, and assigns "
            "(collectively, \"Client Indemnitees\") from and against any and all claims, damages, "
            "losses, liabilities, costs, and expenses (including reasonable attorneys' fees) "
            "(\"Losses\") arising out of or relating to: (a) Provider's material breach of this "
            "Agreement; (b) the gross negligence or willful misconduct of Provider; or (c) any "
            "claim that the Deliverables, as delivered and used in accordance with this Agreement, "
            "infringe any third-party Intellectual Property Rights.\n\n"
            "4.2 Indemnification by Client. Client shall indemnify, defend, and hold harmless "
            "Provider and its officers, directors, employees, agents, successors, and assigns "
            "(\"Provider Indemnitees\") from and against any Losses arising out of or relating to: "
            "(a) Client's material breach of this Agreement; (b) the gross negligence or willful "
            "misconduct of Client; or (c) Client's use of the Deliverables in a manner not "
            "authorized by this Agreement.\n\n"
            "4.3 Indemnification Procedure. The party seeking indemnification (\"Indemnified Party\") "
            "shall promptly notify the indemnifying party (\"Indemnitor\") of any claim for which "
            "indemnification is sought. The Indemnitor shall have the right to assume sole control "
            "of the defense and settlement of such claim, provided that the Indemnified Party may "
            "participate with counsel of its own choosing at its own expense. The Indemnified Party "
            "shall cooperate reasonably with the Indemnitor in the defense of such claim."
        ),
    },
    {
        "heading": "5. LIMITATION OF LIABILITY",
        "type": "liability",
        "body": (
            "5.1 Exclusion of Consequential Damages. IN NO EVENT SHALL EITHER PARTY BE LIABLE "
            "TO THE OTHER FOR ANY INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE, OR "
            "CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, LOSS OF DATA, LOSS OF GOODWILL, "
            "OR COST OF PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES, HOWEVER CAUSED AND UNDER "
            "ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING "
            "NEGLIGENCE), EVEN IF SUCH PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.\n\n"
            "5.2 Cap on Liability. EACH PARTY'S TOTAL CUMULATIVE LIABILITY TO THE OTHER PARTY "
            "FOR ALL CLAIMS ARISING UNDER OR RELATED TO THIS AGREEMENT, WHETHER IN CONTRACT, "
            "TORT, OR OTHERWISE, SHALL NOT EXCEED THE TOTAL FEES PAID OR PAYABLE BY CLIENT TO "
            "PROVIDER IN THE TWELVE (12) MONTH PERIOD IMMEDIATELY PRECEDING THE EVENT GIVING "
            "RISE TO THE CLAIM.\n\n"
            "5.3 Exceptions. The limitations in Sections 5.1 and 5.2 shall not apply to: "
            "(a) a party's indemnification obligations under Section 4; (b) damages arising from "
            "a party's gross negligence or willful misconduct; or (c) a party's breach of its "
            "confidentiality obligations under Section 3."
        ),
    },
    {
        "heading": "6. TERM AND TERMINATION",
        "type": "termination",
        "body": (
            "6.1 Term. This Agreement shall commence on the Effective Date and shall continue "
            "for an initial term of one (1) year (the \"Initial Term\"), unless earlier terminated "
            "in accordance with this Section 6. Following the Initial Term, this Agreement shall "
            "automatically renew for successive one-year periods (each, a \"Renewal Term\") unless "
            "either party provides written notice of non-renewal at least sixty (60) days prior to "
            "the end of the then-current term.\n\n"
            "6.2 Termination for Cause. Either party may terminate this Agreement upon written "
            "notice of termination if the other party materially breaches this Agreement and fails "
            "to cure such breach within thirty (30) days after receiving written notice specifying "
            "the breach in reasonable detail.\n\n"
            "6.3 Termination for Convenience. Either party may terminate this Agreement for any "
            "reason or no reason upon ninety (90) days' prior written notice to the other party. "
            "In the event of termination for convenience by Client, Client shall pay all Fees for "
            "Services rendered through the effective date of termination.\n\n"
            "6.4 Effect of Termination. Upon the expiration or termination of this Agreement for "
            "any reason: (a) all rights and licenses granted herein shall immediately terminate; "
            "(b) each party shall promptly return or destroy all Confidential Information of the "
            "other party; and (c) all payment obligations accrued prior to the effective date of "
            "termination or expiration shall survive."
        ),
    },
    {
        "heading": "7. GOVERNING LAW AND DISPUTE RESOLUTION",
        "type": "governing_law",
        "body": (
            "7.1 Governing Law. This Agreement and all disputes, claims, or controversies arising "
            "out of or relating to this Agreement shall be governed by and construed in accordance "
            "with the laws of the State of Delaware, without regard to its conflict-of-laws "
            "principles (\"Choice of Law\").\n\n"
            "7.2 Exclusive Jurisdiction. The parties irrevocably consent to the exclusive "
            "jurisdiction and venue of the state and federal courts located in New Castle County, "
            "Delaware for the resolution of any dispute arising under this Agreement. Each party "
            "hereby waives any objection to the laying of venue of any such proceeding in such "
            "courts, and waives any claim that any such proceeding has been brought in an "
            "inconvenient forum.\n\n"
            "7.3 Waiver of Jury Trial. EACH PARTY HEREBY IRREVOCABLY WAIVES, TO THE FULLEST "
            "EXTENT PERMITTED BY APPLICABLE LAW, ANY RIGHT TO A TRIAL BY JURY IN ANY ACTION, "
            "PROCEEDING, OR CLAIM ARISING OUT OF OR RELATING TO THIS AGREEMENT.\n\n"
            "7.4 Injunctive Relief. Notwithstanding the foregoing, either party may seek "
            "preliminary or injunctive relief in any court of competent jurisdiction to prevent "
            "irreparable harm pending the resolution of a dispute."
        ),
    },
    {
        "heading": "8. GENERAL PROVISIONS",
        "type": "other",
        "body": (
            "8.1 Entire Agreement. This Agreement, together with all exhibits and schedules, "
            "constitutes the entire agreement between the parties with respect to the subject "
            "matter hereof and supersedes all prior and contemporaneous agreements, proposals, "
            "negotiations, representations, and understandings between the parties.\n\n"
            "8.2 Amendment. This Agreement may not be modified or amended except by a written "
            "instrument signed by authorized representatives of both parties.\n\n"
            "8.3 Waiver. No failure or delay by either party in exercising any right under this "
            "Agreement shall constitute a waiver of that right.\n\n"
            "8.4 Severability. If any provision of this Agreement is found invalid or "
            "unenforceable, such provision shall be modified to the minimum extent necessary to "
            "make it valid and enforceable, and the remaining provisions shall continue in "
            "full force and effect.\n\n"
            "8.5 Notices. All notices under this Agreement shall be in writing and delivered "
            "by (a) personal delivery, (b) nationally recognized overnight courier, or "
            "(c) certified mail, return receipt requested."
        ),
    },
]

PAGE_WIDTH = 210  # A4 mm
MARGIN = 20
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


def build_pdf(output_path: Path) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=MARGIN)
    pdf.set_margins(MARGIN, MARGIN, MARGIN)

    # ── Cover page ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.ln(40)
    pdf.cell(0, 12, "SOFTWARE SERVICES AGREEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 8, "Sample Contract - Clause Lens Eval Dataset", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        CONTENT_WIDTH,
        6,
        (
            "This Software Services Agreement (\"Agreement\") is entered into as of "
            "January 1, 2025 (\"Effective Date\") by and between ACME Software Inc., "
            "a Delaware corporation (\"Provider\"), and GlobalCorp Ltd., a United Kingdom "
            "limited company (\"Client\").\n\n"
            "WHEREAS, Provider desires to provide certain software development and related "
            "services to Client; and\n\n"
            "WHEREAS, Client desires to obtain such services from Provider;\n\n"
            "NOW, THEREFORE, in consideration of the mutual covenants and agreements set "
            "forth herein, and for other good and valuable consideration, the receipt and "
            "sufficiency of which are hereby acknowledged, the parties agree as follows:"
        ),
        align="J",
    )

    # ── Clause pages ──────────────────────────────────────────────────────
    for clause in CLAUSES:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, clause["heading"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(CONTENT_WIDTH, 6, clause["body"], align="J")

    # ── Signature page ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "SIGNATURE PAGE", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        CONTENT_WIDTH,
        6,
        (
            "IN WITNESS WHEREOF, the parties have executed this Agreement as of the "
            "Effective Date.\n\n\n"
            "ACME SOFTWARE INC.\n\n"
            "By: _________________________\n"
            "Name: Jane Smith\n"
            "Title: Chief Executive Officer\n"
            "Date: ________________________\n\n\n"
            "GLOBALCORP LTD.\n\n"
            "By: _________________________\n"
            "Name: John Doe\n"
            "Title: Vice President, Procurement\n"
            "Date: ________________________"
        ),
        align="L",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    print(f"Sample PDF written to: {output_path.resolve()}")
    print(f"Pages: {pdf.page}")


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_contract.pdf"
    build_pdf(out)
