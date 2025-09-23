from dataclasses import dataclass, asdict
from typing import List
import csv


@dataclass
class ClientRecord:
    first_name: str
    last_name: str
    date_of_birth: str
    email: str
    password: str
    mobile_country_code: str
    mobile_number: str
    passport_number: str = ""
    visa_type: str = ""
    application_center: str = ""
    service_center: str = ""
    trip_reason: str = ""
    gender: str = ""
    current_nationality: str = ""
    passport_expiry: str = ""


def load_clients(csv_path: str) -> List[ClientRecord]:
    records: List[ClientRecord] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize and provide fallbacks
            visa_type = row.get("visa_type", "").strip()
            if not visa_type:
                # Fallback to trip_reason if provided
                visa_type = row.get("trip_reason", "").strip()

            records.append(
                ClientRecord(
                    first_name=row.get("first_name", "").strip(),
                    last_name=row.get("last_name", "").strip(),
                    date_of_birth=row.get("date_of_birth", "").strip(),
                    email=row.get("email", "").strip(),
                    password=row.get("password", "").strip(),
                    mobile_country_code=row.get("mobile_country_code", "").strip(),
                    mobile_number=row.get("mobile_number", "").strip(),
                    passport_number=row.get("passport_number", "").strip(),
                    visa_type=visa_type,
                    application_center=row.get("application_center", "").strip(),
                    service_center=row.get("service_center", "").strip(),
                    trip_reason=row.get("trip_reason", "").strip(),
                    gender=row.get("gender", "").strip(),
                    current_nationality=row.get("current_nationality", "").strip(),
                    passport_expiry=row.get("passport_expiry", "").strip(),
                )
            )
    return records


def save_clients(csv_path: str, clients: List[ClientRecord]) -> None:
    fieldnames = list(asdict(ClientRecord("", "", "", "", "", "", "")).keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in clients:
            writer.writerow(asdict(c))


