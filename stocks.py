"""
Broad Mongolian finance keyword groups for Twitter scraping.
Each entry maps to one CSV file. Filter by ticker/query_used afterwards.
"""

MSE_STOCKS = [
    {
        "ticker": "huvitsaa",
        "name_en": "Stock / Share",
        "queries": ["хувьцаа", "хувьцааны зах зээл"],
    },
    {
        "ticker": "nogdol",
        "name_en": "Dividend",
        "queries": ["ногдол ашиг"],
    },
    {
        "ticker": "mhb",
        "name_en": "MSE / МХБ",
        "queries": ["МХБ хувьцаа", "Монголын хөрөнгийн бирж"],
    },
    {
        "ticker": "invest",
        "name_en": "Investment",
        "queries": ["хөрөнгийн бирж", "хөрөнгө оруулалт хувьцаа"],
    },
    {
        "ticker": "ariljaa",
        "name_en": "Trading / Broker",
        "queries": ["хувьцаа арилжаа", "брокер хувьцаа"],
    },
    {
        "ticker": "oyu",
        "name_en": "Oyu Tolgoi",
        "queries": ["Оюу толгой хувьцаа", "Оюутолгой ногдол ашиг"],
    },
    {
        "ticker": "tavan",
        "name_en": "Tavan Tolgoi / ETT",
        "queries": ["Тавантолгой хувьцаа", "ETT хувьцаа"],
    },
    {
        "ticker": "apu",
        "name_en": "APU",
        "queries": ["АПУ хувьцаа", "АПУ ХК"],
    },
    {
        "ticker": "banks",
        "name_en": "Mongolian Banks",
        "queries": [
            "Голомт банк хувьцаа",
            "Хаан банк хувьцаа",
            "Худалдаа хөгжлийн банк хувьцаа",
        ],
    },
    {
        "ticker": "ipo",
        "name_en": "IPO",
        "queries": ["IPO Монгол", "хувьцаа гаргах"],
    },
    {
        "ticker": "bloombergtvm",
        "name_en": "Bloomberg TV Mongolia",
        "queries": ["from:BloombergTVM"],
    },
]
