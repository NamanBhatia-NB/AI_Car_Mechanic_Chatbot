import re
from typing import Dict, Any, Tuple, Optional, List
from api.models import ChatSession

POPULAR_MAKES = [
    'toyota', 'honda', 'ford', 'chevrolet', 'chevy', 'nissan', 'bmw', 'mercedes', 'benz',
    'audi', 'volkswagen', 'vw', 'hyundai', 'kia', 'subaru', 'mazda', 'lexus', 'dodge',
    'jeep', 'ram', 'chrysler', 'tesla', 'volvo', 'porsche', 'land rover', 'acura', 'infiniti',
    'buick', 'cadillac', 'gmc', 'mitsubishi', 'mini', 'jaguar', 'maruti', 'suzuki', 'tata',
    'mahindra', 'skoda', 'renault'
]


class DiagnosticStateMachine:
    """
    Tier 1: Deterministic state machine that extracts vehicle parameters and
    generates targeted technician follow-up questions before triggering a diagnosis.
    """

    @classmethod
    def extract_vehicle_details(cls, text: str) -> Dict[str, Any]:
        """Extracts year, make, and mileage from user text."""
        details = {}
        clean_text = text.lower()

        # Year match: 1980 - 2027
        year_match = re.search(r'\b(19[8-9]\d|20[0-2]\d)\b', clean_text)
        if year_match:
            details['car_year'] = int(year_match.group(1))

        # Make match
        for make in POPULAR_MAKES:
            if re.search(rf'\b{make}\b', clean_text):
                # Standardize common abbreviations
                if make == 'chevy':
                    details['car_make'] = 'Chevrolet'
                elif make in ('mercedes', 'benz'):
                    details['car_make'] = 'Mercedes-Benz'
                elif make == 'vw':
                    details['car_make'] = 'Volkswagen'
                else:
                    details['car_make'] = make.capitalize()
                break

        # Mileage match (e.g. 85,000 miles or 120k miles)
        mileage_match = re.search(r'\b(\d{1,3}(?:,\d{3})+|\d+)\s*(?:k\s*)?(?:miles|mi|km|kms)\b', clean_text)
        if mileage_match:
            raw_val = mileage_match.group(1).replace(',', '')
            val = int(raw_val)
            if 'k' in clean_text[mileage_match.start():mileage_match.end()]:
                val *= 1000
            details['mileage'] = val

        return details

    @classmethod
    def update_session_vehicle(cls, session: ChatSession, text: str):
        """Updates session attributes with extracted vehicle details."""
        extracted = cls.extract_vehicle_details(text)
        changed = False

        if 'car_year' in extracted and not session.car_year:
            session.car_year = extracted['car_year']
            changed = True
        if 'car_make' in extracted and not session.car_make:
            session.car_make = extracted['car_make']
            changed = True
        if 'mileage' in extracted and not session.mileage:
            session.mileage = extracted['mileage']
            changed = True

        if changed:
            session.save()

    @classmethod
    def evaluate_flow(
        cls,
        session: ChatSession,
        user_message: str,
        message_history_count: int,
        has_media: bool = False
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Determines whether sufficient information exists to formulate a diagnosis,
        or whether Marcus should ask targeted follow-up questions first.

        Returns:
            (diagnosis_ready: bool, follow_up_question: Optional[str], quick_replies: List[str])
        """
        text = user_message.lower()

        # Update session with any vehicle info mentioned
        cls.update_session_vehicle(session, user_message)

        # Explicit user request for diagnosis or booking overrides
        if any(trigger in text for trigger in ['give me diagnosis', 'diagnose now', 'what is the issue', 'what is wrong', 'book mechanic', 'give me the report']):
            session.stage = 'diagnosed'
            session.save()
            return True, None, ["Book a Mechanic", "Get estimated repair cost", "Ask another question"]

        # If media was uploaded, the user provided direct evidence, proceed towards diagnosis
        if has_media:
            return True, None, ["View Complete Diagnosis", "Book Mechanic Inspection"]

        # Case 1: Brand new conversation, user has not specified car make or year
        if not session.car_make and message_history_count <= 2:
            session.stage = 'gathering_info'
            session.save()
            return (
                False,
                f"Got it. To give you an accurate diagnostic assessment and part pricing, "
                f"what is the **Year, Make, and Model** of your vehicle? (e.g., 2018 Honda Civic, 2015 Ford F-150)",
                ["2018 Honda Civic", "2016 Toyota Camry", "2019 Ford F-150", "2020 Hyundai Elantra"]
            )

        # Case 2: Vehicle known, but driving condition or sound frequency missing
        has_condition_indicators = any(cond in text for cond in [
            'when accelerating', 'when braking', 'highway', 'idle', 'idling', 'cold start',
            'morning', 'turning', 'bumps', 'speed', 'mph', 'flashing', 'solid', 'temperature',
            'constant', 'intermittent', 'only when', 'clicks', 'smoke'
        ])

        if not has_condition_indicators and message_history_count <= 4:
            vehicle_name = f"{session.car_year or ''} {session.car_make} {session.car_model}".strip() or "your car"
            session.stage = 'gathering_info'
            session.save()
            return (
                False,
                f"Understood regarding {vehicle_name}. As a senior technician, I need to pinpoint the operating condition: "
                f"Does this happen continuously, or specifically during **cold starts**, **under heavy acceleration**, or **when applying the brakes**? "
                f"Also, are there any warning lights (like Check Engine or Battery) on your dash?",
                ["Happens when braking", "Happens on cold start", "Constant while driving", "Check Engine Light is on"]
            )

        # Case 3: We have gathered symptoms + operating conditions, diagnosis is ready!
        session.stage = 'diagnosed'
        session.save()
        return (
            True,
            None,
            ["Book Certified Mechanic", "DIY repair difficulty?", "Estimated repair cost breakdown"]
        )
