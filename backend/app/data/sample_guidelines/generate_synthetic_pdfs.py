from pathlib import Path
import fitz  # PyMuPDF


def create_sepsis_2026_pdf(output_path: Path) -> None:
    """Generate multi-page synthetic Sepsis Management Guidelines 2026 PDF."""
    doc = fitz.open()

    # Page 1: Title and Scope
    p1 = doc.new_page()
    p1.insert_text(
        fitz.Point(50, 70),
        "SURVIVING SEPSIS CAMPAIGN: CLINICAL GUIDELINE 2026\n"
        "International Guidelines for Management of Sepsis and Septic Shock\n"
        "Document Version: 2026.0 | Authority: International Sepsis Forum (Tier 1)\n\n"
        "1.0 EXECUTIVE SUMMARY\n"
        "Sepsis is defined as life-threatening organ dysfunction caused by a dysregulated host response to infection.\n"
        "Prompt identification, appropriate antimicrobial therapy, and hemodynamic stabilization are paramount.\n"
        "This version supersedes the 2024 guidance regarding rigid fluid boluses.\n",
        fontsize=11,
    )

    # Page 2: Antimicrobial Timing (Section 3.1)
    p2 = doc.new_page()
    p2.insert_text(
        fitz.Point(50, 70),
        "SECTION 3.0 ANTIMICROBIAL THERAPY & INFECTION CONTROL\n\n"
        "3.1 Antimicrobial Administration Timing\n"
        "For adult patients with possible septic shock or a high likelihood of sepsis, we recommend administering\n"
        "broad-spectrum intravenous antimicrobials immediately, ideally within 1 hour of recognition.\n"
        "Empiric broad-spectrum therapy should cover all likely gram-positive and gram-negative pathogens.\n\n"
        "3.2 De-escalation and Duration\n"
        "We recommend daily assessment for de-escalation of antimicrobial therapy based on pathogen identification.\n"
        "Shorter courses of 7 to 10 days are recommended for most clinical presentations once source control is achieved.\n",
        fontsize=11,
    )

    # Page 3: Fluid Resuscitation & Hemodynamics (Section 3.4 & 4.2)
    p3 = doc.new_page()
    p3.insert_text(
        fitz.Point(50, 70),
        "SECTION 3.4 FLUID RESUSCITATION & HEMODYNAMIC MONITORING\n\n"
        "For patients with sepsis-induced hypoperfusion or septic shock, we recommend dynamic fluid assessment\n"
        "rather than automatic fixed crystalloid loading. An initial conservative bolus of 30 mL/kg balanced crystalloids\n"
        "within 3 hours is acceptable, followed by dynamic measures of fluid responsiveness (passive leg raise, stroke volume variation).\n\n"
        "SECTION 4.2 VASOACTIVE MEDICATIONS\n"
        "For adults with septic shock, we recommend Norepinephrine as the first-choice vasopressor.\n"
        "Target a mean arterial pressure (MAP) of 65 mmHg. If MAP remains inadequate despite Norepinephrine titration,\n"
        "add Vasopressin at a fixed rate of 0.03 units/min rather than escalating Norepinephrine to toxic dosages.\n",
        fontsize=11,
    )

    doc.save(str(output_path))
    doc.close()


def create_sepsis_2024_pdf(output_path: Path) -> None:
    """Generate synthetic Sepsis Guideline 2024 (Superseded Version)."""
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text(
        fitz.Point(50, 70),
        "SEPSIS PROTOCOL 2024 (SUPERSEDED)\n"
        "Document Version: 2024.1 | Authority: Clinical SOP Group\n\n"
        "SECTION 2.0 RESUSCITATION BUNDLE\n"
        "Administer at least 30 mL/kg of intravenous crystalloid fluid within the first 3 hours for all patients\n"
        "with hypotension or serum lactate >= 4.0 mmol/L regardless of cardiac ejection fraction.\n",
        fontsize=11,
    )
    doc.save(str(output_path))
    doc.close()


def create_anticoagulation_pdf(output_path: Path) -> None:
    """Generate synthetic Anticoagulation Protocol PDF."""
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text(
        fitz.Point(50, 70),
        "HOSPITAL ANTICOAGULATION & THROMBOPROPHYLAXIS PROTOCOL\n"
        "Document Version: 2025.2 | Authority: Department of Pharmacy & Hematology (Tier 2)\n\n"
        "SECTION 1.0 VENOUS THROMBOEMBOLISM (VTE) PROPHYLAXIS\n"
        "All hospitalized non-bleeding medical patients should receive Enoxaparin 40 mg subcutaneous once daily.\n"
        "For patients with creatinine clearance < 30 mL/min, adjust Enoxaparin dose to 30 mg subcutaneous once daily\n"
        "or switch to Unfractionated Heparin 5000 units subcutaneous every 8 to 12 hours.\n\n"
        "SECTION 2.0 THERAPEUTIC ANTICOAGULATION FOR ATRIAL FIBRILLATION\n"
        "First-line agents include Direct Oral Anticoagulants (Apixaban 5 mg twice daily or Rivaroxaban 20 mg once daily with food).\n"
        "Reduce Apixaban dose to 2.5 mg twice daily if patient meets two of the following criteria: age >= 80, body weight <= 60 kg,\n"
        "or serum creatinine >= 1.5 mg/dL.\n",
        fontsize=11,
    )
    doc.save(str(output_path))
    doc.close()


def create_corrupted_file(output_path: Path) -> None:
    """Generate a corrupted pseudo-PDF file for error-handling test."""
    with open(output_path, "wb") as f:
        f.write(b"%PDF-1.4\n%CORRUPT_PAYLOAD_INVALID_STRUCTURE_HERE_EOF")


def generate_all_samples(target_dir: Path) -> None:
    """Generate all synthetic test guidelines in the target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    create_sepsis_2026_pdf(target_dir / "sepsis_guideline_2026.pdf")
    create_sepsis_2024_pdf(target_dir / "sepsis_guideline_2024.pdf")
    create_anticoagulation_pdf(target_dir / "anticoagulation_protocol.pdf")
    create_corrupted_file(target_dir / "corrupted_sample.pdf")


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    generate_all_samples(out_dir)
    print(f"Synthetic clinical PDFs generated successfully in: {out_dir}")
