from database.models import ParentDocument, ChildChunk
from database.database import SessionLocal

db = SessionLocal()

chunks = db.query(ChildChunk).all()
for c in chunks:
    parent = db.query(ParentDocument).filter_by(id=c.parent_id).first()
    if not parent:
        print(f"Chunk {c.id} está sem parent: {c.parent_id}")