"""
Country utilities for Nobel Laureate Speech Explorer.

- Extract unique country names from Nobel literature metadata
- Map country names to Unicode flag emoji (where possible)

Author: NobelLM Team
"""
import os
import json
from typing import List, Set, Dict, Optional

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'nobel_literature.json')


def extract_unique_countries(metadata_path: str = DATA_PATH) -> Set[str]:
    """
    Extract all unique country names from the Nobel literature metadata JSON.
    Args:
        metadata_path: Path to the Nobel literature JSON file.
    Returns:
        Set of unique country names (case-sensitive, as in data).
    """
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    countries = set()
    for entry in data:
        for laureate in entry.get('laureates', []):
            country = laureate.get('country')
            if country:
                countries.add(country)
    return countries


def country_to_flag(country: str) -> Optional[str]:
    """
    Convert a country name to its Unicode flag emoji, if possible.
    Args:
        country: Country name (e.g., 'France', 'USA', 'United Kingdom')
    Returns:
        Unicode flag emoji string, or None if not mappable.
    """
    # Mapping for special/ambiguous cases
    special_cases = {
        'USA': 'US',
        'United States': 'US',
        'United Kingdom': 'GB',
        'UK': 'GB',
        'England': 'GB',
        'Scotland': 'GB',
        'Northern Ireland': 'GB',
        'South Korea': 'KR',
        'North Korea': 'KP',
        'Russia': 'RU',
        'Soviet Union': 'RU',
        'USSR': 'RU',
        'Iran': 'IR',
        'Turkey': 'TR',
        'Egypt': 'EG',
        'Saint Lucia': 'LC',
        'Bosnia and Herzegovina': 'BA',
        'Czech Republic': 'CZ',
        'Slovakia': 'SK',
        'South Africa': 'ZA',
        'Ivano-Frankivsk, Ukraine': 'UA',
        'Ukraine': 'UA',
        'Poland': 'PL',
        'Sweden': 'SE',
        'Norway': 'NO',
        'Denmark': 'DK',
        'Finland': 'FI',
        'Iceland': 'IS',
        'Ireland': 'IE',
        'Italy': 'IT',
        'France': 'FR',
        'Germany': 'DE',
        'Austria': 'AT',
        'Belgium': 'BE',
        'Switzerland': 'CH',
        'Spain': 'ES',
        'Portugal': 'PT',
        'Chile': 'CL',
        'Peru': 'PE',
        'Mexico': 'MX',
        'Canada': 'CA',
        'Japan': 'JP',
        'China': 'CN',
        'India': 'IN',
        'South Korea': 'KR',
        'Turkey': 'TR',
        'Romania': 'RO',
        'Hungary': 'HU',
        'Greece': 'GR',
        'Algeria': 'DZ',
        'Mauritius': 'MU',
        'Saint Lucia': 'LC',
        'Australia': 'AU',
        'New Zealand': 'NZ',
        'Serbia': 'RS',
        'Croatia': 'HR',
        'Slovenia': 'SI',
        'Montenegro': 'ME',
        'Bosnia and Herzegovina': 'BA',
        'Macedonia': 'MK',
        'Georgia': 'GE',
        'Armenia': 'AM',
        'Azerbaijan': 'AZ',
        'Latvia': 'LV',
        'Lithuania': 'LT',
        'Estonia': 'EE',
        'Luxembourg': 'LU',
        'Monaco': 'MC',
        'Liechtenstein': 'LI',
        'San Marino': 'SM',
        'Vatican City': 'VA',
        'Kosovo': 'XK',
        'South Korea': 'KR',
        'North Korea': 'KP',
        'Israel': 'IL',
        'Palestine': 'PS',
        'Lebanon': 'LB',
        'Syria': 'SY',
        'Jordan': 'JO',
        'Iraq': 'IQ',
        'Saudi Arabia': 'SA',
        'United Arab Emirates': 'AE',
        'Qatar': 'QA',
        'Kuwait': 'KW',
        'Bahrain': 'BH',
        'Oman': 'OM',
        'Yemen': 'YE',
        'Morocco': 'MA',
        'Tunisia': 'TN',
        'Libya': 'LY',
        'Sudan': 'SD',
        'Ethiopia': 'ET',
        'Nigeria': 'NG',
        'Ghana': 'GH',
        'Kenya': 'KE',
        'Tanzania': 'TZ',
        'Uganda': 'UG',
        'Zimbabwe': 'ZW',
        'South Africa': 'ZA',
        'Namibia': 'NA',
        'Botswana': 'BW',
        'Mozambique': 'MZ',
        'Angola': 'AO',
        'Zambia': 'ZM',
        'Malawi': 'MW',
        'Madagascar': 'MG',
        'Cameroon': 'CM',
        'Senegal': 'SN',
        'Ivory Coast': 'CI',
        "Côte d'Ivoire": 'CI',
        'Democratic Republic of the Congo': 'CD',
        'Republic of the Congo': 'CG',
        'Gabon': 'GA',
        'Equatorial Guinea': 'GQ',
        'Central African Republic': 'CF',
        'Chad': 'TD',
        'Niger': 'NE',
        'Mali': 'ML',
        'Burkina Faso': 'BF',
        'Guinea': 'GN',
        'Sierra Leone': 'SL',
        'Liberia': 'LR',
        'Benin': 'BJ',
        'Togo': 'TG',
        'Gambia': 'GM',
        'Guinea-Bissau': 'GW',
        'Cape Verde': 'CV',
        'Comoros': 'KM',
        'Seychelles': 'SC',
        'Mauritania': 'MR',
        'Somalia': 'SO',
        'Djibouti': 'DJ',
        'Eritrea': 'ER',
        'Burundi': 'BI',
        'Rwanda': 'RW',
        'Swaziland': 'SZ',
        'Lesotho': 'LS',
        'Gabon': 'GA',
        'Congo': 'CG',
        'Zaire': 'CD',
        'Moldova': 'MD',
        'Belarus': 'BY',
        'Ukraine': 'UA',
        'Uzbekistan': 'UZ',
        'Kazakhstan': 'KZ',
        'Kyrgyzstan': 'KG',
        'Tajikistan': 'TJ',
        'Turkmenistan': 'TM',
        'Afghanistan': 'AF',
        'Pakistan': 'PK',
        'Bangladesh': 'BD',
        'Sri Lanka': 'LK',
        'Nepal': 'NP',
        'Bhutan': 'BT',
        'Maldives': 'MV',
        'Mongolia': 'MN',
        'Vietnam': 'VN',
        'Thailand': 'TH',
        'Cambodia': 'KH',
        'Laos': 'LA',
        'Myanmar': 'MM',
        'Malaysia': 'MY',
        'Singapore': 'SG',
        'Indonesia': 'ID',
        'Philippines': 'PH',
        'Brunei': 'BN',
        'Timor-Leste': 'TL',
        'Papua New Guinea': 'PG',
        'Fiji': 'FJ',
        'Samoa': 'WS',
        'Tonga': 'TO',
        'Vanuatu': 'VU',
        'Solomon Islands': 'SB',
        'Micronesia': 'FM',
        'Palau': 'PW',
        'Marshall Islands': 'MH',
        'Nauru': 'NR',
        'Tuvalu': 'TV',
        'Kiribati': 'KI',
        'Antigua and Barbuda': 'AG',
        'Bahamas': 'BS',
        'Barbados': 'BB',
        'Belize': 'BZ',
        'Dominica': 'DM',
        'Grenada': 'GD',
        'Guyana': 'GY',
        'Haiti': 'HT',
        'Jamaica': 'JM',
        'Saint Kitts and Nevis': 'KN',
        'Saint Vincent and the Grenadines': 'VC',
        'Suriname': 'SR',
        'Trinidad and Tobago': 'TT',
        'Cuba': 'CU',
        'Dominican Republic': 'DO',
        'Puerto Rico': 'PR',
        'Greenland': 'GL',
        'Faroe Islands': 'FO',
        'Svalbard and Jan Mayen': 'SJ',
        'Hong Kong': 'HK',
        'Macau': 'MO',
        'Taiwan': 'TW',
        'Venezuela': 'VE',
        'Colombia': 'CO',
        'Ecuador': 'EC',
        'Bolivia': 'BO',
        'Paraguay': 'PY',
        'Uruguay': 'UY',
        'Argentina': 'AR',
        'Brazil': 'BR',
        'Panama': 'PA',
        'Costa Rica': 'CR',
        'Nicaragua': 'NI',
        'Honduras': 'HN',
        'El Salvador': 'SV',
        'Guatemala': 'GT',
        'Czechia': 'CZ',
        'Eswatini': 'SZ',
        'Ivory Coast': 'CI',
        "Côte d'Ivoire": 'CI',
        "Ivory Coast (Côte d'Ivoire)": 'CI',
    }
    # Normalize country name
    code = special_cases.get(country, None)
    if not code:
        # Try to derive from country name (e.g., "France" -> "FR")
        import pycountry
        try:
            c = pycountry.countries.lookup(country)
            code = c.alpha_2
        except Exception:
            return None
    # Convert country code to flag emoji
    if len(code) == 2 and code.isalpha():
        return chr(0x1F1E6 + ord(code[0].upper()) - ord('A')) + chr(0x1F1E6 + ord(code[1].upper()) - ord('A'))
    return None 