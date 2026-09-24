import re
from typing import Dict, Any, Tuple, Optional, List
from api.models import ChatSession

POPULAR_MAKES = [
    'toyota', 'honda', 'ford', 'chevrolet', 'chevy', 'nissan', 'bmw', 'mercedes', 'benz',
    'audi', 'volkswagen', 'vw', 'hyundai', 'kia', 'subaru', 'mazda', 'lexus', 'dodge',
    'jeep', 'ram', 'chrysler', 'tesla', 'volvo', 'porsche', 'land rover', 'acura', 'infiniti',
    'buick', 'cadillac', 'gmc', 'mitsubishi', 'mini', 'jaguar', 'maruti', 'suzuki', 'tata',
    'mahindra', 'skoda', 'renault', 'mg', 'byd'
]

POPULAR_MODELS_MAP = {
    'wagonr': ('Maruti Suzuki', 'WagonR'),
    'wagon r': ('Maruti Suzuki', 'WagonR'),
    'swift': ('Maruti Suzuki', 'Swift'),
    'dzire': ('Maruti Suzuki', 'Dzire'),
    'baleno': ('Maruti Suzuki', 'Baleno'),
    'brezza': ('Maruti Suzuki', 'Brezza'),
    'alto': ('Maruti Suzuki', 'Alto'),
    'ertiga': ('Maruti Suzuki', 'Ertiga'),
    'celerio': ('Maruti Suzuki', 'Celerio'),
    'ignis': ('Maruti Suzuki', 'Ignis'),
    'creta': ('Hyundai', 'Creta'),
    'i20': ('Hyundai', 'i20'),
    'i10': ('Hyundai', 'Grand i10'),
    'verna': ('Hyundai', 'Verna'),
    'venue': ('Hyundai', 'Venue'),
    'santro': ('Hyundai', 'Santro'),
    'elantra': ('Hyundai', 'Elantra'),
    'alcazar': ('Hyundai', 'Alcazar'),
    'nexon': ('Tata', 'Nexon'),
    'harrier': ('Tata', 'Harrier'),
    'safari': ('Tata', 'Safari'),
    'punch': ('Tata', 'Punch'),
    'tiago': ('Tata', 'Tiago'),
    'altroz': ('Tata', 'Altroz'),
    'scorpio': ('Mahindra', 'Scorpio'),
    'thar': ('Mahindra', 'Thar'),
    'xuv700': ('Mahindra', 'XUV700'),
    'xuv300': ('Mahindra', 'XUV300'),
    'bolero': ('Mahindra', 'Bolero'),
    'city': ('Honda', 'City'),
    'amaze': ('Honda', 'Amaze'),
    'civic': ('Honda', 'Civic'),
    'innova': ('Toyota', 'Innova'),
    'fortuner': ('Toyota', 'Fortuner'),
    'camry': ('Toyota', 'Camry'),
    'corolla': ('Toyota', 'Corolla'),
    'seltos': ('Kia', 'Seltos'),
    'sonet': ('Kia', 'Sonet'),
    'carens': ('Kia', 'Carens'),
    'f-150': ('Ford', 'F-150'),
    'f150': ('Ford', 'F-150'),
    'mustang': ('Ford', 'Mustang'),
    'ecosport': ('Ford', 'EcoSport'),
}


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

        # Check known models map first (e.g. "wagonr", "swift", "creta")
        for model_key, (make_val, model_val) in POPULAR_MODELS_MAP.items():
            if re.search(rf'\b{re.escape(model_key)}\b', clean_text):
                details['car_make'] = make_val
                # Check for trim details (e.g. "lxi", "vxi", "zxi", "ex", "sx")
                trim_match = re.search(rf'\b{re.escape(model_key)}\s+([a-zA-Z0-9]+)\b', clean_text)
                if trim_match:
                    details['car_model'] = f"{model_val} {trim_match.group(1).upper()}"
                else:
                    details['car_model'] = model_val
                break

        # Check popular makes if not already resolved by model
        if 'car_make' not in details:
            for make in POPULAR_MAKES:
                if re.search(rf'\b{make}\b', clean_text):
                    if make == 'chevy':
                        details['car_make'] = 'Chevrolet'
                    elif make in ('mercedes', 'benz'):
                        details['car_make'] = 'Mercedes-Benz'
                    elif make == 'vw':
                        details['car_make'] = 'Volkswagen'
                    elif make in ('maruti', 'suzuki'):
                        details['car_make'] = 'Maruti Suzuki'
                    else:
                        details['car_make'] = make.capitalize()
                    break

        # If a year was provided and remaining words exist, fallback to extracting them
        if year_match and 'car_make' not in details:
            after_year = clean_text[year_match.end():].strip()
            # Remove punctuation and split words
            words = [w for w in re.sub(r'[^\w\s]', '', after_year).split() if len(w) > 1 and w not in ('my', 'car', 'the', 'is', 'not', 'have', 'driving')]
            if words:
                details['car_make'] = words[0].capitalize()
                if len(words) > 1:
                    details['car_model'] = " ".join([w.upper() if len(w) <= 3 else w.capitalize() for w in words[1:]])

        # Mileage match (e.g. 85,000 miles or 120k miles or 45000 km)
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

        if 'car_year' in extracted:
            session.car_year = extracted['car_year']
            changed = True
        if 'car_make' in extracted:
            session.car_make = extracted['car_make']
            changed = True
        if 'car_model' in extracted:
            session.car_model = extracted['car_model']
            changed = True
        if 'mileage' in extracted:
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

        # If already diagnosed, remain in diagnosed stage for follow-ups and service inquiries
        if session.stage == 'diagnosed' or getattr(session, 'diagnosis', None) is not None:
            return True, None, ["Book Certified Mechanic", "What tools do I need?", "Can I drive it safely?"]

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

        # Case 2: Vehicle known, check if we need to ask follow-up on operating condition
        has_condition_indicators = any(cond in text for cond in [
            'when accelerating', 'when braking', 'braking', 'brakes', 'highway', 'idle', 'idling',
            'cold start', 'morning', 'turning', 'bumps', 'speed', 'mph', 'flashing', 'solid',
            'temperature', 'constant', 'intermittent', 'only when', 'clicks', 'smoke',
            'light is on', 'check engine', 'warning light', 'battery light', 'dash light', 'light'
        ])

        already_asked_condition = session.messages.filter(
            sender='mechanic',
            content__icontains='operating condition'
        ).exists()

        if not has_condition_indicators and not already_asked_condition and message_history_count <= 4:
            vehicle_name = f"{session.car_year or ''} {session.car_make} {session.car_model}".strip() or "your vehicle"
            session.stage = 'gathering_info'
            session.save()
            return (
                False,
                f"Understood regarding {vehicle_name}. As a senior technician, I need to pinpoint the operating condition: "
                f"Does this happen continuously, or specifically during **cold starts**, **under heavy acceleration**, or **when applying the brakes**? "
                f"Also, are there any warning lights (like Check Engine or Battery) on your dash?",
                ["Constant while driving", "Happens when braking", "Happens on cold start", "Under heavy acceleration"]
            )

        # Case 3: We have gathered symptoms + operating conditions, diagnosis is ready!
        session.stage = 'diagnosed'
        session.save()
        return (
            True,
            None,
            ["Book Certified Mechanic", "DIY repair difficulty?", "Estimated repair cost breakdown"]
        )
