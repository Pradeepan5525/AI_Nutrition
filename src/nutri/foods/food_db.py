"""Database repository and caching layer for foods database."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from nutri.config import FOODS_DB, FOODS_PARQUET
from nutri.logging import setup_logger

logger = setup_logger(__name__)


class FoodDatabase:
    """Provides high-performance querying and caching over harmonized food catalog."""

    def __init__(self, db_path: Optional[Path] = None, parquet_path: Optional[Path] = None):
        self.db_path = db_path or FOODS_DB
        self.parquet_path = parquet_path or FOODS_PARQUET
        self._df_cache: Optional[pd.DataFrame] = None
        self._food_cache: Dict[str, Dict[str, Any]] = {}

    def get_connection(self) -> sqlite3.Connection:
        """Create a connection to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_dataframe(self) -> pd.DataFrame:
        """Load or return cached complete foods DataFrame from Parquet."""
        if self._df_cache is None:
            if not self.parquet_path.exists():
                raise FileNotFoundError(f"Foods parquet file not found at {self.parquet_path}")
            self._df_cache = pd.read_parquet(self.parquet_path)
        return self._df_cache

    def get_food_by_id(self, food_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single food record by its food_id with caching."""
        if food_id in self._food_cache:
            return self._food_cache[food_id]
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM foods WHERE food_id = ? LIMIT 1", (food_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            res = dict(row)
            self._food_cache[food_id] = res
            return res
        return None

    def search_foods(
        self,
        query: str = "",
        category: Optional[str] = None,
        food_type: Optional[str] = None,
        min_health_score: float = 0.0,
        exclude_allergens: Optional[List[str]] = None,
        dietary_tags: Optional[List[str]] = None,
        strict_allergens: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search foods with SQL filters, allergen exclusions, and pagination."""
        exclude_allergens = [a.lower().strip() for a in (exclude_allergens or [])]
        dietary_tags = [d.lower().strip() for d in (dietary_tags or [])]

        conditions = ["health_score_v2 >= ?"]
        params: List[Any] = [min_health_score]

        if query.strip():
            conditions.append("name LIKE ?")
            params.append(f"%{query.strip()}%")

        if category and category != "All":
            conditions.append("category = ?")
            params.append(category)

        if food_type and food_type != "All":
            conditions.append("food_type = ?")
            params.append(food_type)

        # Allergen SQL clauses
        for allergen in exclude_allergens:
            col_name = f"allergen_{allergen}"
            if strict_allergens:
                # Must be strictly absent
                conditions.append(f"{col_name} = 'absent'")
            else:
                # Must not be present (absent or unknown allowed)
                conditions.append(f"{col_name} != 'present'")

        # Dietary tags clause
        for tag in dietary_tags:
            conditions.append("restriction_tags LIKE ?")
            params.append(f"%{tag}%")

        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT * FROM foods
            WHERE {where_clause}
            ORDER BY health_score_v2 DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        return [dict(r) for r in rows]

    def count_matching_foods(
        self,
        query: str = "",
        category: Optional[str] = None,
        food_type: Optional[str] = None,
        min_health_score: float = 0.0,
        exclude_allergens: Optional[List[str]] = None,
        dietary_tags: Optional[List[str]] = None,
        strict_allergens: bool = True,
    ) -> int:
        """Count total matching foods without pagination."""
        exclude_allergens = [a.lower().strip() for a in (exclude_allergens or [])]
        dietary_tags = [d.lower().strip() for d in (dietary_tags or [])]

        conditions = ["health_score_v2 >= ?"]
        params: List[Any] = [min_health_score]

        if query.strip():
            conditions.append("name LIKE ?")
            params.append(f"%{query.strip()}%")

        if category and category != "All":
            conditions.append("category = ?")
            params.append(category)

        if food_type and food_type != "All":
            conditions.append("food_type = ?")
            params.append(food_type)

        for allergen in exclude_allergens:
            col_name = f"allergen_{allergen}"
            if strict_allergens:
                conditions.append(f"{col_name} = 'absent'")
            else:
                conditions.append(f"{col_name} != 'present'")

        for tag in dietary_tags:
            conditions.append("restriction_tags LIKE ?")
            params.append(f"%{tag}%")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT COUNT(*) FROM foods WHERE {where_clause}"

        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        count = cur.fetchone()[0]
        conn.close()
        return count

    def get_total_count(self) -> int:
        """Return total number of rows in the foods database."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM foods")
        count = cur.fetchone()[0]
        conn.close()
        return count

    def get_unique_categories(self) -> List[str]:
        """Return sorted list of distinct food categories."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT category FROM foods WHERE category IS NOT NULL ORDER BY category"
        )
        cats = [r[0] for r in cur.fetchall()]
        conn.close()
        return cats

    def get_unique_food_types(self) -> List[str]:
        """Return sorted list of distinct food types."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT food_type FROM foods WHERE food_type IS NOT NULL ORDER BY food_type"
        )
        types_ = [r[0] for r in cur.fetchall()]
        conn.close()
        return types_


# Global singleton database instance
_DB_INSTANCE: Optional[FoodDatabase] = None


def get_food_db() -> FoodDatabase:
    """Retrieve singleton FoodDatabase instance."""
    global _DB_INSTANCE
    if _DB_INSTANCE is None:
        _DB_INSTANCE = FoodDatabase()
    return _DB_INSTANCE
