"""Generische Bewerbungstexte fuer Demo- und Produktivbetrieb.

Die Vorlagen enthalten bewusst keine persoenlichen Projektdetails. Eigene
Formulierungen koennen lokal ueber config.json oder die erzeugten Dateien
angepasst werden.
"""

DEFAULT_PROJECT_SUMMARY = (
    "Aktuell arbeite ich an einem eigenen Softwareprojekt zur strukturierten "
    "Datenerfassung und Automatisierung wiederkehrender Arbeitsablaeufe. Dabei "
    "sammle ich praktische Erfahrung mit Datenaufbereitung, Schnittstellen und "
    "klar dokumentierten Prozessen."
)


def project_summary(applicant: dict) -> str:
    return applicant.get("project_summary") or DEFAULT_PROJECT_SUMMARY


def email_subject(applicant: dict) -> str:
    return f"Bewerbung als Werkstudent IT - {applicant['name']}"


def email_body(job: dict, applicant: dict) -> str:
    return (
        "Sehr geehrte Damen und Herren,\n\n"
        f"anbei sende ich Ihnen meine Bewerbung für die ausgeschriebene Stelle als "
        f"{job['title']} bei {job['company']}.\n\n"
        f"Ich studiere {applicant.get('study', 'Informatik')} und interessiere mich "
        "besonders fuer Softwareentwicklung, strukturierte Arbeitsablaeufe und "
        "technische Problemloesung. Im Anhang finden Sie meinen Lebenslauf und "
        "mein Anschreiben.\n\n"
        f"Gerne unterstütze ich Ihr Team mit {applicant.get('weekly_hours', '20 Stunden')} "
        f"pro Woche, {applicant.get('available_from', 'ab sofort')}.\n\n"
        "Mit freundlichen Grüßen\n"
        f"{applicant['name']}\n"
        f"{applicant.get('email', '')} | {applicant.get('phone', '')}"
    )


def cover_letter_text(job: dict, applicant: dict) -> str:
    age = applicant.get("age")
    alter = f"Ich bin {age} Jahre alt und studiere" if age else "Ich studiere"
    return (
        f"Bewerbung als {job['title']}\n\n"
        "Sehr geehrte Damen und Herren,\n\n"
        f"mit großem Interesse habe ich Ihre Ausschreibung für die Werkstudentenstelle als "
        f"{job['title']} bei {job['company']} in {job['location']} gelesen.\n\n"
        f"{alter} {applicant.get('study', 'Informatik')}. Während meines Studiums und "
        "durch eigene Projekte habe ich mir gute Kenntnisse in Softwareentwicklung, technischen "
        "Systemen und der Analyse von Prozessen angeeignet. Besonders interessiert mich, wie man "
        "wiederkehrende Abläufe durch digitale Tools verlässlicher und effizienter "
        "gestalten kann.\n\n"
        f"{project_summary(applicant)}\n\n"
        "Ich arbeite mich schnell in neue Themen ein, denke analytisch und bringe eine hohe "
        f"Lernbereitschaft mit. Gerne unterstütze ich Ihr Team mit "
        f"{applicant.get('weekly_hours', '20 Stunden')} pro Woche, "
        f"{applicant.get('available_from', 'ab sofort')}.\n\n"
        "Über eine Einladung zu einem persönlichen Gespräch freue ich mich sehr.\n\n"
        "Mit freundlichen Grüßen\n"
        f"{applicant['name']}\n"
        f"{applicant.get('email', '')} | {applicant.get('phone', '')}"
    )


def portal_answers(job: dict, applicant: dict) -> str:
    skills = ", ".join(applicant.get("skills", []))
    return (
        f"=== Portal-Antworten für: {job['title']} bei {job['company']} ===\n\n"
        "-- Motivation --\n"
        f"Die Stelle als {job['title']} bei {job['company']} passt sehr gut zu meinem Studium "
        f"({applicant.get('study', 'Informatik')}) und meinen praktischen Erfahrungen. "
        "Besonders interessieren mich strukturierte technische Arbeit, Softwareentwicklung "
        "und gut nachvollziehbare Prozesse.\n\n"
        "-- Verfügbarkeit --\n"
        f"{applicant.get('available_from', 'ab sofort')}\n\n"
        "-- Wochenstunden --\n"
        f"{applicant.get('weekly_hours', '20 Stunden')}\n\n"
        "-- Skills --\n"
        f"{skills}\n\n"
        "-- Eigenes Praxisprojekt --\n"
        f"{project_summary(applicant)}\n"
    )
