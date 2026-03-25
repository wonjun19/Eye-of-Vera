import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional

from config.settings import DB_PATH
from src.core.analyzer import AnalysisResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite 기반 전술 로그 저장 및 조회."""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                detected_activity TEXT,
                message TEXT,
                mission TEXT,
                action_required INTEGER DEFAULT 0
            )
        """)
        self._conn.commit()

    def insert(self, result: AnalysisResult, mission: str):
        self._conn.execute(
            """INSERT INTO logs (timestamp, status, confidence, detected_activity,
                                message, mission, action_required)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(),
                result.status,
                result.confidence,
                result.detected_activity,
                result.message,
                mission,
                int(result.action_required),
            ),
        )
        self._conn.commit()
        logger.debug("로그 저장: %s", result.status)

    def get_daily_summary(self, date: Optional[str] = None) -> dict:
        """특정 날짜의 요약 통계 반환. date 형식: 'YYYY-MM-DD' (기본: 오늘)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        rows = self._conn.execute(
            "SELECT status, COUNT(*) as cnt FROM logs WHERE timestamp LIKE ? GROUP BY status",
            (f"{date}%",),
        ).fetchall()

        total = sum(r["cnt"] for r in rows)
        counts = {r["status"]: r["cnt"] for r in rows}

        focus = counts.get("FOCUS", 0)
        relax = counts.get("RELAX", 0)
        deviation = counts.get("DEVIATION", 0)
        valid = focus + relax + deviation
        return {
            "date": date,
            "total": total,
            "focus": focus,
            "relax": relax,
            "deviation": deviation,
            "unknown": counts.get("UNKNOWN", 0),
            "focus_rate": round(focus / valid * 100, 1) if valid > 0 else 0.0,
        }

    def get_weekly_summary(self) -> list[dict]:
        """최근 7일간 일별 요약 리스트 반환."""
        today = datetime.now().date()
        return [
            self.get_daily_summary((today - timedelta(days=i)).isoformat())
            for i in range(6, -1, -1)
        ]

    def get_hourly_distribution(self, date: Optional[str] = None) -> dict[str, int]:
        """특정 날짜의 시간대별 FOCUS 횟수."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        rows = self._conn.execute(
            """SELECT SUBSTR(timestamp, 12, 2) as hour, COUNT(*) as cnt
               FROM logs WHERE timestamp LIKE ? AND status = 'FOCUS'
               GROUP BY hour ORDER BY hour""",
            (f"{date}%",),
        ).fetchall()

        return {r["hour"]: r["cnt"] for r in rows}

    def get_recent_logs(self, limit: int = 5) -> list[dict]:
        """최근 분석 로그 N건을 반환한다."""
        rows = self._conn.execute(
            "SELECT timestamp, status, detected_activity, message "
            "FROM logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def build_chat_context(self) -> str:
        """채팅에 주입할 전술 데이터 문자열을 생성한다."""
        daily = self.get_daily_summary()
        weekly = self.get_weekly_summary()
        recent = self.get_recent_logs(5)

        lines = []

        # 오늘 요약
        if daily["total"] > 0:
            lines.append(f"### 오늘({daily['date']}) 요약")
            lines.append(f"- 총 정찰 {daily['total']}회 | "
                         f"집중 {daily['focus']}회 · 휴식 {daily['relax']}회 · "
                         f"이탈 {daily['deviation']}회")
            lines.append(f"- 집중률: {daily['focus_rate']}%")
        else:
            lines.append("### 오늘 요약")
            lines.append("- 아직 정찰 기록이 없습니다.")

        # 주간 추세
        active_days = [d for d in weekly if d["total"] > 0]
        if active_days:
            lines.append("\n### 최근 7일 추세")
            for d in active_days:
                lines.append(f"- {d['date']}: 집중률 {d['focus_rate']}% "
                             f"({d['total']}회 정찰)")

        # 최근 로그
        if recent:
            lines.append("\n### 최근 정찰 기록")
            for log in recent:
                ts = log["timestamp"][11:16]  # HH:MM
                lines.append(f"- [{ts}] {log['status']} — {log['detected_activity']}")

        return "\n".join(lines)

    def close(self):
        self._conn.close()
