# ... Continuation of the previous snippet ...

from odmantic import SyncEngine

engine = SyncEngine()
engine.configure_database([Product])
