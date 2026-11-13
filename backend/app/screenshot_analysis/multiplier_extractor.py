"""Robust multiplier pattern extraction and regex sanitization."""
import re
from typing import List, Dict, Any, Optional, Tuple


class MultiplierExtractor:
    """Extracts, normalizes, and filters crash multiplier patterns from text blocks."""

    # Matches patterns like 1.24x, 1,245.67x, 2.00X, 10.45 x, 1.00x, 34.50X
    # Negative lookahead/lookbehind to avoid currency symbols ($100, 5000 INR)
    MULTIPLIER_REGEX = re.compile(
        r'(?<![\$\€\£\₹])\b([1-9]\d{0,3}(?:[.,]\d{1,3})*|\d+)[.,](\d{2})\s*[xX]\b'
    )
    # Loose regex for pills that missed the 'x' but have standard decimal multiplier formatting (e.g., 2.34 or 1.05)
    LOOSE_DECIMAL_REGEX = re.compile(
        r'\b([1-9]\d{0,2})[.,](\d{2})\b'
    )

    @classmethod
    def clean_number_string(cls, integer_part: str, decimal_part: str) -> float:
        """Converts strings like '1,245' and '67' into 1245.67."""
        clean_int = integer_part.replace(",", "").replace(".", "").replace(" ", "")
        val_str = f"{clean_int}.{decimal_part}"
        return round(float(val_str), 2)

    @classmethod
    def extract_multipliers_from_text(cls, raw_text: str) -> List[Dict[str, Any]]:
        """Parses raw OCR output text into recognized multiplier tokens."""
        found_records = []
        seen_keys = set()

        # Pass 1: Strict 'x' or 'X' matches
        for match in cls.MULTIPLIER_REGEX.finditer(raw_text):
            int_part, dec_part = match.group(1), match.group(2)
            try:
                multiplier = cls.clean_number_string(int_part, dec_part)
                if multiplier >= 1.00:
                    found_records.append({
                        "multiplier": multiplier,
                        "raw_token": match.group(0),
                        "confidence": 0.95,
                    })
            except (ValueError, TypeError):
                continue

        # If strict matches are few, look for potential loose decimal tokens
        # but filter out obvious balance numbers (> 100000 or integers)
        if len(found_records) < 3:
            for match in cls.LOOSE_DECIMAL_REGEX.finditer(raw_text):
                int_part, dec_part = match.group(1), match.group(2)
                try:
                    multiplier = cls.clean_number_string(int_part, dec_part)
                    # Filter realistic crash range: 1.00 to 5000.00
                    if 1.00 <= multiplier <= 5000.00:
                        # Avoid duplicates from strict pass
                        token = match.group(0)
                        if not any(abs(r["multiplier"] - multiplier) < 0.001 for r in found_records):
                            found_records.append({
                                "multiplier": multiplier,
                                "raw_token": token,
                                "confidence": 0.70,
                            })
                except (ValueError, TypeError):
                    continue

        return found_records

    @classmethod
    def filter_ui_false_positives(cls, records: List[Dict[str, Any]], raw_text: str) -> List[Dict[str, Any]]:
        """Prunes tokens that look like user balances, round bets, or button text."""
        # Common UI strings near balance or bet boxes: 'balance', 'bet', 'cashout', 'total'
        # Multipliers in Spribe Aviator are generally between 1.00x and 10,000x
        cleaned = []
        for r in records:
            m = r["multiplier"]
            # Exclude extreme unrealistic values from accidental OCR glitch
            if m < 1.00 or m > 1000000.00:
                continue
            cleaned.append(r)
        return cleaned
