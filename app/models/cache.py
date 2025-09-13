from datetime import datetime, timezone, timedelta
from .. import db
import json

class CacheEntry(db.Model): 
    __tablename__ = "cache_entries"
    id = db.Column(db.Integer, primary_key = True)
    symbol = db.Column(db.String, nullable = False)
    kind = db.Column(db.String, nullable = False)
    payload = db.Column(db.Text, nullable = False) 
    fetched_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("symbol", "kind", name="uq_symbol_kind"),)



def get_cached(symbol, kind):
    now = datetime.now(timezone.utc)
    row = CacheEntry.query.filter(CacheEntry.symbol == symbol, CacheEntry.kind == kind, CacheEntry.fetched_at >= (now - timedelta(minutes=5))).first()
    # what to do if query is missing 
    return row



def set_cached(symbol, kind, data):
    row = CacheEntry.query.filter(CacheEntry.symbol == symbol, CacheEntry.kind == kind).first()
    payload = data if isinstance(data, str) else json.dumps(data)

    if row:
        row.fetched_at = datetime.now(timezone.utc)
        row.payload = payload
    else: 
        row = CacheEntry(
        symbol=symbol,
        kind=kind,
        payload=payload,
        fetched_at=datetime.now(timezone.utc)
    )
        db.session.add(row)

    db.session.commit()


def get_or_update(symbol, kind, compute_fn):
    row = get_cached(symbol, kind)
    if row:
        try:
            return json.loads(row.payload)
        except json.JSONDecodeError:
            pass
    try:
        data = compute_fn()
        set_cached(symbol, kind, data)
        return data
    except Exception as e:
        raise
