"""FWC ETL Pipeline - Extractors Package"""

from src.extract.extractors.awards import AwardsExtractor
from src.extract.extractors.classifications import ClassificationsExtractor
from src.extract.extractors.expense_allowances import ExpenseAllowancesExtractor
from src.extract.extractors.pay_rates import PayRatesExtractor
from src.extract.extractors.wage_allowances import WageAllowancesExtractor

__all__ = [
    "AwardsExtractor",
    "ClassificationsExtractor",
    "PayRatesExtractor",
    "ExpenseAllowancesExtractor",
    "WageAllowancesExtractor",
]
